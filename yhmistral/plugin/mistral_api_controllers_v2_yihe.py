
# Copyright 2014 - Mirantis, Inc.
# Copyright 2015 Huawei Technologies Co., Ltd.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import json
from oslo_log import log as logging
import pecan
from pecan import hooks
from pecan import rest
from mistral.api.controllers.v2 import resources
from mistral import context
from mistral.utils import rest_utils

from mie.xlogger.klog import klog
from mie.bprint import varfmt
import mie.confcenter

import mistral.actions.if_session as ses

LOG = logging.getLogger(__name__)
conf = mie.confcenter.getdefcc()


def doSession(dic):
    exid = dic.get("exid")
    try:
        ses.sesRollback(exid)
        return "Session: %s  , rollback ok." % exid
    except:
        LOG.info("rollback exception...")
        return "Session: %s  , rollback failed!" % exid


class YiheController(rest.RestController, hooks.HookController):
    '''
    '''

    @rest_utils.wrap_pecan_controller_exception
    @pecan.expose(content_type="text/plain")
    def post(self, cmd):
        LOG.info("POST" * 5)
        LOG.info(cmd)
        ctx = context.ctx()
        definition = pecan.request.text
        data = json.loads(definition)
        LOG.info("cmd:" + str(cmd))
        LOG.info("ctx:" + str(ctx))
        LOG.info("body:" + str(definition))
        LOG.info("data:" + str(data))
        LOG.info("POST" * 6)

        if cmd == "sessionRollback":
            # Only support rollback
            return doSession(data)

    #
    # FIXME: Copied from action.py
    #
