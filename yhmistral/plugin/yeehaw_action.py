#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import traceback
import six
import json

from mistral import exceptions as exc
from mistral.actions.std_actions import NoOpAction
import mistral.actions.if_session as ses
import mistral.actions.eureka_client as eureka
from mistral.utils import kfk_etypes
from mistral.utils import kfk_trace
from mistral_lib import actions
from oslo_log import log as logging

from mie.xlogger.klog import klog
from mie.bprint import varfmt, todict
import mie.confcenter

LOG = logging.getLogger(__name__)
conf = mie.confcenter.getdefcc()

#
# yihe.Session
#
class Session(NoOpAction):
    '''
    action yihe.Session cmd=Create ...
    '''
    def __init__(self, action_context, cmd, psid=None, sid=None):
        actx = action_context
        klog.d("  ACTX : " + str(varfmt(actx)))
        klog.d("   CMD : " + str(cmd))
        klog.d("  PSID : " + str(psid))
        klog.d("   SID : " + str(sid))

        self.cmd = cmd
        self.actx = actx
        self.psid = psid
        self.sid = sid

    def run(self, context):
        klog.d("CMD: ", self.cmd)
        klog.d(varfmt(context))
        if self.cmd == "create":
            # Get content information
            # action_execution_id = self.actx.get("action_execution_id")
            # task_id = self.actx.get("task_id")
            # task_name = self.actx.get("task_name")
            workflow_execution_id = self.actx.get("workflow_execution_id")
            # workflow_name = self.actx.get("workflow_name")

            sid = self.psid or workflow_execution_id
            # sesCreate return a session ID.
            res = {
                "content": ses.sesCreate(sid, workflow_execution_id)
            }

        if self.cmd == "rollback":
            res = ses.sesRollback(self.sid)

        klog.d(varfmt(res))
        return res

    def test(self, context):
        return None


#
# yihe.Sync
#
class Sync(actions.Action):
    def orgInit(self,
                url,
                method="GET",
                params=None,
                body=None,
                headers=None,
                cookies=None,
                auth=None,
                timeout=None,
                allow_redirects=None,
                proxies=None,
                verify=None):

        if auth and len(auth.split(':')) == 2:
            self.auth = (auth.split(':')[0], auth.split(':')[1])
        else:
            self.auth = auth

        if isinstance(headers, dict):
            for key, val in headers.items():
                if isinstance(val, (six.integer_types, float)):
                    headers[key] = str(val)

        self.url = url
        self.method = method
        self.params = params

        if isinstance(body, dict):
            body = json.dumps(body, ensure_ascii=False)
        if body:
            body = body.encode("utf-8")
        self.body = body

        self.headers = headers
        self.cookies = cookies
        self.timeout = timeout
        self.allow_redirects = allow_redirects
        self.proxies = proxies
        self.verify = verify

    def __init__(self,
                 action_context,
                 url,
                 method="GET",
                 params=None,
                 body=None,
                 atom=None,
                 session=None,
                 headers=None,
                 cookies=None,
                 auth=None,
                 timeout=None,
                 allow_redirects=None,
                 proxies=None,
                 verify=None):
        self.ts_init_start = time.time()
        klog.d("INTO YIHE.SYNC")

        actx = action_context

        # 1. Strip the session info
        klog.d("   URL : " + str(url))
        klog.d("METHOD : " + str(method))
        klog.d("  BODY : " + str(body))
        klog.d("  HDRS : " + str(headers))
        klog.d(" PARAM : " + str(params))
        klog.d("  ACTX : " + str(varfmt(actx)))

        # FIXME: how to process the atomID
        self.atom = atom
        self.session = session

        sesEna = conf.SES_ENA and session
        hookEna = conf.HOOK
        # klog.d("Session or NOT:", sesEna, "  In config:", conf.SES_ENA, "  Session Id:", session)

        self.skipRun = False

        # Get content information
        self.action_execution_id = actx.get("action_execution_id")
        self.task_id = actx.get("task_id")
        self.task_name = actx.get("task_name")
        self.workflow_execution_id = actx.get("workflow_execution_id")
        self.workflow_name = actx.get("workflow_name")

        if hookEna:
            # FIXME: Provide a chance to modify the input and output.
            pass

        '''

            exid = actx.get("action_execution_id")
            hookInfo = db_get_hook_info(exid)
            if hookInfo:
                self.skipRun = hookInfo.skipRun

                self.input = hookInfo.input

                # Only once
                db_mark_used(exid)

                #
                # Overwrite All the parameters and DO NOT overwrite key
                # parameters
                #
                url = _url or url
                body = _body or body
        '''

        # Overwrite the rerun input and/or output
        self.rrInput = self.rrOutput = None

        self.ts_ses_start = self.ts_ses_end = 0
        if sesEna:
            klog.d("Process session")

            self.ts_ses_start = time.time()
            dic = {
                "x__sid": session,

                "url": url,
                "method": method,
                "body": body,
                "headers": headers,
                "params": params,
                "actx": actx,
                "cookies": cookies,
                "auth": auth,
                "allow_redirects": allow_redirects,
                "proxies": proxies,
                "verify": verify,
            }
            ses.sesPush(session, dic)
            self.ts_ses_end = time.time()

        self.orgInit(
            url,
            method,
            params,
            body,
            headers,
            cookies,
            auth,
            timeout,
            allow_redirects,
            proxies,
            verify,
        )
        klog.d()
        self.ts_init_end = time.time()

    def orgRun(self, context):
        LOG.info(
            "Running HTTP action "
            "[url=%s, method=%s, params=%s, body=%s, headers=%s,"
            " cookies=%s, auth=%s, timeout=%s, allow_redirects=%s,"
            " proxies=%s, verify=%s]",
            self.url,
            self.method,
            self.params,
            self.body,
            self.headers,
            self.cookies,
            self.auth,
            self.timeout,
            self.allow_redirects,
            self.proxies,
            self.verify
        )

        try:
            resp = requests.request(
                self.method,
                self.url,
                params=self.params,
                data=self.body,
                headers=self.headers,
                cookies=self.cookies,
                auth=self.auth,
                timeout=self.timeout,
                allow_redirects=self.allow_redirects,
                proxies=self.proxies,
                verify=self.verify
            )
        except Exception as e:
            raise exc.ActionException("Failed to send HTTP request: %s" % e)

        LOG.info(
            "HTTP action response:\n%s\n%s",
            resp.status_code,
            resp.content
        )

        # TODO(akuznetsova): Need to refactor Mistral serialiser and
        # deserializer to have an ability to pass needed encoding and work
        # with it. Now it can process only default 'utf-8' encoding.
        # Appropriate bug #1676411 was created.

        # Represent important resp data as a dictionary.
        try:
            content = resp.json(encoding=resp.encoding)
        except Exception as e:
            LOG.debug("HTTP action response is not json.")
            content = resp.content
            if content and resp.encoding != 'utf-8':
                content = content.decode(resp.encoding).encode('utf-8')

        _result = {
            'content': content,
            'status': resp.status_code,
            'headers': dict(resp.headers.items()),
            'url': resp.url,
            'history': resp.history,
            'encoding': resp.encoding,
            'reason': resp.reason,
            'cookies': dict(resp.cookies.items()),
            'elapsed': resp.elapsed.total_seconds()
        }

        if resp.status_code not in range(200, 307):
            return actions.Result(error=_result)

        return _result

    def run(self, context):
        self.ts_run_start = time.time()

        if not self.skipRun:
            # TODO: replace input with self.rrInput
            # if self.rrInput:
                # pass

            klog.d(varfmt(self))
            # klog.d(varfmt(context))
            klog.d(">>> Run action")
            res = self.orgRun(context)

            klog.d("<<< Run action")
            klog.d(varfmt(res))
            try:
                _input = todict(self)
            except:
                _input = None
            try:
                _output = todict(res)
            except:
                _output = None

            kfk_trace.log(kfk_etypes.TASK_ACTION, self.atom, "RUNNING",
                          self.workflow_name, self.workflow_execution_id,
                          self.task_id, self.task_name,
                          _input, _output, None)

        else:
            klog.d("YIHE.Sync.run skipped")

        # TODO: replace output with self.rrOutput
        if self.rrOutput:
            pass

        self.ts_run_end = time.time()

        klog.d("TIME:    Init total: ", self.ts_init_end - self.ts_init_start)
        klog.d("TIME:     Run total: ", self.ts_run_end - self.ts_run_start)
        klog.d("TIME:  Action Total: ", self.ts_run_end - self.ts_init_start)
        if self.ts_ses_end:
            klog.d("TIME: Session Total: ", self.ts_ses_end - self.ts_ses_start)

        return res


class Async(Sync):
    def __init__(self,
                 action_context,
                 url,
                 method="GET",
                 params=None,
                 body=None,
                 atom=None,
                 session=None,
                 headers=None,
                 cookies=None,
                 auth=None,
                 timeout=None,
                 allow_redirects=None,
                 proxies=None,
                 verify=None):

        actx = action_context

        ck_url = actx.get('callback_url')
        if conf.EUREKA_ENABLE:
            host = eureka.get_app_url(conf.APP_NAME_CALLBACK)
            ck_url = host + ck_url
            klog.d("Eureka enable, CK_URL:", ck_url)

        headers = headers or {}
        headers.update({
            'Workflow-Name': actx.get('workflow_name'),
            'Workflow-Execution-Id': actx.get('workflow_execution_id'),
            'Task-Id': actx.get('task_id'),
            'Action-Execution-Id': actx.get('action_execution_id'),
            'Callback-URL': ck_url,
        })

        super(Async, self).__init__(
            action_context,
            url,
            method,
            params,
            body,
            atom,
            session,
            headers,
            cookies,
            auth,
            timeout,
            allow_redirects,
            proxies,
            verify,
        )

    def is_sync(self):
        return False

    def test(self, context):
        return None

# vim: sw=4 ts=4 sts=4 ai et
