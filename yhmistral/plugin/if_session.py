#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import time
import requests
import traceback
import urlparse
import json

from mie.xlogger.klog import klog
from mie.bprint import varfmt
import mie.confcenter

from mistral.utils import kfk_etypes
from mistral.utils import kfk_trace

from mistral.utils.mongoclient import MgoClient

conf = mie.confcenter.getdefcc()


class MyMgoClient(MgoClient):
    def __init__(self):
        host = ("ses/mgo/host", '127.0.0.1')
        port = ("ses/mgo/port", 27017)
        ena = ("ses/enable", True)

        MgoClient.__init__(self, conf, host, port, ena)

mgoclient = MyMgoClient()


### #####################################################################
## Session
#

def sesCreate(psid, wfexid):
    # Create a new session
    klog.d("Parent Session ID: ", psid)
    try:
        client = mgoclient.client()
        tab = client.yeehaw.session
        res = tab.find_one({"_id": psid})
        if res:
            klog.d("PSID %s found" % str(psid))
            return psid

        info = {
            "wfexid": wfexid,
        }

        res = tab.insert_one({"_id": psid, "info": info})
        klog.d("SID %s added" % res.inserted_id)
        return str(res.inserted_id)
    except:
        klog.e(traceback.format_exc())
        return "OK"


def sesPush(sid, inf):
    # Add action node

    """
    p.update({"_id":sid},{"$push":{"actions":"Test"}})
    p.update({"_id":sid},{"$addToSet": {"tags":{"$each":["Python","Each"]}}})
    """

    try:
        # klog.d("SID: ", sid, ", INF: ", varfmt(inf))
        client = mgoclient.client()
        tab = client.yeehaw.session
        res = tab.find_one({"_id": sid})
        if not res:
            klog.e("push NG: sid %s not exist" % sid)
            return False

        inf["createat"] = time.time()
        tab.update({"_id": sid}, {"$push": {"actions": inf}})

        klog.d("push OK")
        return True
    except:
        klog.e(traceback.format_exc())

        klog.d("push NG")
        return False


def kfkMessagePush(etype=None, atomId=None, status=None, wfId=None, exId=None,
                   taskId=None, taskName=None, input=None, output=None, triggered_by=None):

    etype = etype or "Unknown"
    wfId = wfId or "x01"
    exId = exId or "x02"
    taskId = taskId or ""
    taskName = taskName or ""
    atomId = atomId or ""
    status = status or "unknown"
    input = input or {}
    output = output or {}
    triggered_by = triggered_by or []

    try:
        message = kfk_trace.KfkMessage(etype, wfId, exId, taskId, taskName, atomId, status, input, output, triggered_by)

        msg = message.to_str()
        key = None
        klog.d(msg, ":", key)
        client = mgoclient.client().yihe
        dic = {
            "msg": msg,
            "key": key
        }
        client.evtlog.insert_one(dic)
    except:
        klog.e("Kafka Message build fail: ", "etype=%s,wfId=%s,exId=%s,taskId=%s,taskName=%s" %
                (etype, wfId, exId, taskId, taskName) )
        klog.e(traceback.format_exc())

    pass


def sesRollback(sid):
    # Call all the rollback of saved action

    klog.d("SID: ", sid)

    def gen_rollback_url(url, sid):
        urlp = urlparse.urlparse(url)
        if urlp.query:
            return "%s&rollback=true&sid=%s" % (url, sid)
        else:
            return "%s?rollback=true&sid=%s" % (url, sid)

    try:
        client = mgoclient.client()
        tab = client.yeehaw.session
        res = tab.find_one({"_id": sid})
        if not res:
            klog.e("BAD SID:", sid)
            return False

        klog.d(varfmt(res))

        info = res.get("info")
        kfkMessagePush(etype=kfk_etypes.EXECUTION_ROLLBACK_START,     # etype
                       exId=info.get("wfexid"),           # exId
                       )

        for n in res.get("actions"):
            try:
                # construct the rollback url
                url = gen_rollback_url(n.get("url"), sid)
                klog.d(url)

                method = n.get("method")
                body = n.get("body")
                headers = n.get("headers")
                params = n.get("params")
                actx = n.get("actx")
                cookies = n.get("cookies")
                auth = n.get("auth")
                allow_redirects = n.get("allow_redirects")
                proxies = n.get("proxies")
                verify = n.get("verify")

                # Convert body
                if isinstance(body, dict):
                    body = json.dumps(body, ensure_ascii=False)
                if body:
                    body = body.encode("utf-8")

                r = requests.request(
                    method,
                    url,
                    params=params,
                    data=body,
                    headers=headers,
                    cookies=cookies,
                    auth=auth,
                    allow_redirects=allow_redirects,
                    proxies=proxies,
                    verify=verify
                )
                klog.d("RB: code: ", r.status_code, ", reason: ", r.reason)

                wf_ex_id = actx.get("workflow_execution_id")
                workflow_id = actx.get("workflow_name")
                task_id = actx.get("task_id")

                kfkMessagePush(kfk_etypes.TASK_ROLLBACK,     # etype
                               None,                         # atomId
                               None,                         # status
                               workflow_id,                  # wfId
                               wf_ex_id,                     # exId
                               task_id,                      # taskId
                               None,                         # taskName
                               n,                            # Input
                               {
                                  "status_code": r.status_code,
                                  "reason": r.reason
                               },                            # Output
                               None                          # triggered_by
                               )

            except:
                klog.e("RB: NG\n", traceback.format_exc())

        retval = True
    except:
        klog.e(traceback.format_exc())
        klog.d("push NG")
        retval = False

    finally:
        # Drop this table
        klog.d("drop session information for ", sid)
        tab.remove({"_id": sid})
        klog.d("drop session information for ", sid, " done.")

        client = mgoclient.client()
        tab = client.yeehaw.sessionDone
        tab.insert_one(res)

        kfkMessagePush(etype=kfk_etypes.EXECUTION_ROLLBACK_END,     # etype
                       exId=info.get("wfexid"),           # exId
                       )

    return retval

# vim: sw=4 ts=4 sts=4 ai et
