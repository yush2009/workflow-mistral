#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import traceback
import pymongo

from mie.xlogger.klog import klog


class MgoClient():
    def __init__(self, conf, host, port, ena, sens=True):
        self._client = None

        self._conf = conf
        self._host = host
        self._port = port
        self._ena = ena

        self._sens = True

        self._conf.setmonitor(self.conf_reload)
        self.conf_reload(True)

        self._sens = sens

    def sensitive(self, sens=True):
        self._sens = sens

    def conf_reload(self, force=None):
        if not force and not self._sens:
            return

        path, defv = self._host
        host = self._conf.xget(path, defv)

        path, defv = self._port
        port = self._conf.xget(path, defv)

        path, defv = self._ena
        ena = self._conf.xget(path, defv)

        if force is True:
            self._host = self._port = self._ena = None

        if self._host == host and self._port == port and self._ena == ena:
            return

        if self._ena != ena:
            self._ena = ena
            if not ena:
                if self._client:
                    del self._client
                self._client = self._host = self._port = None
                return
            else:
                self._host = None
                self._port = None

        if self._host != host or self._port != port:
            self._host = host
            self._port = port

            try:
                self._client = pymongo.MongoClient(host=host, port=port, connect=False)
            except:
                klog.e(traceback.format_exc())

    def client(self):
        return self._client


# vim: sw=4 ts=4 sts=4 ai et
