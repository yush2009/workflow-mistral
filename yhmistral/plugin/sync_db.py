# Copyright 2014 - Mirantis, Inc.
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

import sys


### #####################################################################
## Mie stuff
#
from mie.confcenter import XConfCenter

alias = (
        # Support session and roll back
        ("SES_ENA", "ses/enable", False),
        ("SES_URL", "ses/url", ""),

        # Use log to record the event
        ("LOG_ENA", "log/enable", False),

        # api.py: Trace db call time cost
        ("DB_TRACE", "trace/db", False),
)

conf = XConfCenter(group="yh", alias=alias)
## Mie stuff done


import keystonemiddleware.opts as keystonemw_opts
from oslo_config import cfg
from oslo_log import log as logging

from mistral import config
from mistral.db.v2 import api as db_api
from mistral.services import action_manager
from mistral.services import workflows

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def main():
    # NOTE(jaosorior): This is needed in order for db-sync to also register the
    # keystonemiddleware options. Those options are used by clients that need a
    # keystone session in order to be able to register their actions.
    # This can be removed when mistral moves out of using keystonemiddleware in
    # favor of keystoneauth1.
    for group, opts in keystonemw_opts.list_auth_token_opts():
        CONF.register_opts(opts, group=group)

    CONF.register_cli_opt(config.os_actions_mapping_path)

    logging.register_options(CONF)

    config.parse_args()

    if len(CONF.config_file) == 0:
        print("Usage: sync_db --config-file <path-to-config-file>")
        return exit(1)
    logging.setup(CONF, 'Mistral')

    LOG.info("Starting db_sync")

    LOG.debug("Setting up db")
    db_api.setup_db()

    LOG.debug("populating db")
    action_manager.sync_db()
    workflows.sync_db()

    return 0


if __name__ == '__main__':
    import os
    os._exit(main())
