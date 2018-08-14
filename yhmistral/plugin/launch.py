#!/usr/bin/env python
# Copyright 2016 - Brocade Communications Systems, Inc.
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
import os

import eventlet

### #####################################################################
## Mie stuff
#
from mie.xlogger.klog import klog
from mie.xlogger.confmon import ccmon as ccmlog
from mie.confcenter import XConfCenter
from mie.roar.confmon import ccmon as ccmroar

alias = (
        # Support session and roll back
        ("SES_ENA", "ses/enable", True),
        ("SES_URL", "ses/url", "http://10.9.63.168:10000/session"),

        # Use log to record the event
        ("LOG_ENA", "log/enable", True),

        # api.py: Trace db call time cost
        ("DB_TRACE", "trace/db", True),

        # eureka_client.py
        ("EUREKA_ENABLE", "eureka/enable", True),
        ("EUREKA_URL", "eureka/base_url", "http://172.16.90.96:3103"),
        ("APP_NAME_CALLBACK", "engine/callback_name", "WORKFLOW-ENGINE-CALLBACK"),
        ("APP_NAME_API", "engine/api_name", "WORKFLOW-ENGINE-API"),
        ("YIHE_API_HOST", "engine/api_host", "http://127.0.0.1:9898"),
        ("YIHE_ASYNC_CALLBACK_HOST", "engine/callback_host", "http://127.0.0.1:9898"),
)

rwcfg = os.environ.get("YH_CFG") or "%s/yh.cfg" % exedir
conf = XConfCenter(group="yh", rw_cfg=rwcfg, alias=alias)
ccmlog(conf)
ccmroar(conf)

## Mie stuff done

eventlet.monkey_patch(
    os=True,
    select=True,
    socket=True,
    thread=False if '--use-debugger' in sys.argv else True,
    time=True)



reload(sys)
sys.setdefaultencoding('utf-8')

# If ../mistral/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
POSSIBLE_TOPDIR = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(POSSIBLE_TOPDIR, 'mistral', '__init__.py')):
    sys.path.insert(0, POSSIBLE_TOPDIR)



from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service

from mistral.api import service as api_service
from mistral import config
from mistral.engine import engine_server
from mistral.event_engine import event_engine_server
from mistral.executors import executor_server
from mistral.rpc import base as rpc
from mistral import version


CONF = cfg.CONF
SERVER_THREAD_MANAGER = None
SERVER_PROCESS_MANAGER = None


def launch_thread(server, workers=1):
    try:
        global SERVER_THREAD_MANAGER

        if not SERVER_THREAD_MANAGER:
            SERVER_THREAD_MANAGER = service.ServiceLauncher(CONF)

        SERVER_THREAD_MANAGER.launch_service(server, workers=workers)
    except Exception as e:
        sys.stderr.write("ERROR: %s\n" % e)
        sys.exit(1)


def launch_process(server, workers=1):
    try:
        global SERVER_PROCESS_MANAGER

        if not SERVER_PROCESS_MANAGER:
            SERVER_PROCESS_MANAGER = service.ProcessLauncher(CONF)

        SERVER_PROCESS_MANAGER.launch_service(server, workers=workers)
    except Exception as e:
        sys.stderr.write("ERROR: %s\n" % e)
        sys.exit(1)


def launch_executor():
    launch_thread(executor_server.get_oslo_service())


def launch_engine():
    launch_thread(engine_server.get_oslo_service())


def launch_event_engine():
    launch_thread(event_engine_server.get_oslo_service())


def launch_api():
    server = api_service.WSGIService('mistral_api')
    launch_process(server, workers=server.workers)


def launch_any(options):
    for option in options:
        LAUNCH_OPTIONS[option]()

    global SERVER_PROCESS_MANAGER
    global SERVER_THREAD_MANAGER

    if SERVER_PROCESS_MANAGER:
        SERVER_PROCESS_MANAGER.wait()

    if SERVER_THREAD_MANAGER:
        SERVER_THREAD_MANAGER.wait()


# Map cli options to appropriate functions. The cli options are
# registered in mistral's config.py.
LAUNCH_OPTIONS = {
    'api': launch_api,
    'engine': launch_engine,
    'executor': launch_executor,
    'event-engine': launch_event_engine
}


MISTRAL_TITLE = """
|\\\    //|           ||                       ||
||\\\  //||      __   ||      __      __       ||
|| \\\// || ||  //  ||||||  ||  \\\  //  \\\     ||
||  \\/  ||     \\\    ||    ||     ||    \\\    ||
||      || ||   \\\   ||    ||     ||    /\\\   ||
||      || || __//   ||_// ||      \\\__// \\\_ ||
Mistral Workflow Service, version %s
""" % version.version_string()


def print_server_info():
    print(MISTRAL_TITLE)

    comp_str = ("[%s]" % ','.join(LAUNCH_OPTIONS)
                if cfg.CONF.server == ['all'] else cfg.CONF.server)

    print('Launching server components %s...' % comp_str)


def get_properly_ordered_parameters():
    """Orders launch parameters in the right order.

    In oslo it's important the order of the launch parameters.
    if --config-file came after the command line parameters the command
    line parameters are ignored.
    So to make user command line parameters are never ignored this method
    moves --config-file to be always first.
    """
    args = sys.argv[1:]

    for arg in sys.argv[1:]:
        if arg == '--config-file' or arg.startswith('--config-file='):
            if "=" in arg:
                conf_file_value = arg.split("=", 1)[1]
            else:
                conf_file_value = args[args.index(arg) + 1]
                args.remove(conf_file_value)
            args.remove(arg)
            args.insert(0, "--config-file")
            args.insert(1, conf_file_value)

    return args


def main():
    try:
        config.parse_args(get_properly_ordered_parameters())
        print_server_info()

        logging.setup(CONF, 'Mistral')

        # Please refer to the oslo.messaging documentation for transport
        # configuration. The default transport for oslo.messaging is
        # rabbitMQ. The available transport drivers are listed in the
        # setup.cfg file in oslo.messaging under the entry_points section for
        # oslo.messaging.drivers. The transport driver is specified using the
        # rpc_backend option in the default section of the oslo configuration
        # file. The expected value for the rpc_backend is one of the key
        # values available for the oslo.messaging.drivers (i.e. rabbit, fake).
        # There are additional options such as ssl and credential that can be
        # specified depending on the driver.  Please refer to the driver
        # implementation for those additional options. It's important to note
        # that the "fake" transport should only be used if "all" the Mistral
        # servers are launched on the same process. Otherwise, messages do not
        # get delivered if the Mistral servers are launched on different
        # processes because the "fake" transport is using an in process queue.
        rpc.get_transport()

        if cfg.CONF.server == ['all']:
            # Launch all servers.
            launch_any(LAUNCH_OPTIONS.keys())
        else:
            # Validate launch option.
            if set(cfg.CONF.server) - set(LAUNCH_OPTIONS.keys()):
                raise Exception('Valid options are all or any combination of '
                                ', '.join(LAUNCH_OPTIONS.keys()))

            # Launch distinct set of server(s).
            launch_any(set(cfg.CONF.server))

    except RuntimeError as excp:
        sys.stderr.write("ERROR: %s\n" % excp)
        sys.exit(1)


# Helper method used in unit tests to reset the service launchers.
def reset_server_managers():
    global SERVER_THREAD_MANAGER
    global SERVER_PROCESS_MANAGER
    SERVER_THREAD_MANAGER = None
    SERVER_PROCESS_MANAGER = None


# Helper method used in unit tests to access the service launcher.
def get_server_thread_manager():
    global SERVER_THREAD_MANAGER
    return SERVER_THREAD_MANAGER


# Helper method used in unit tests to access the process launcher.
def get_server_process_manager():
    global SERVER_PROCESS_MANAGER
    return SERVER_PROCESS_MANAGER


if __name__ == '__main__':
    sys.exit(main())
