#!/usr/bin/env python2
# -*- coding: utf_8 -*-

import threading
import traceback
from collections import deque

from mie.xlogger.klog import klog
import mie.confcenter
from mie.miethread import MieThread
from mie.singleton import ClsSingleton
from mongoclient import MgoClient

conf = mie.confcenter.getdefcc()


class MongoThread(MieThread):
    '''Message queue to send data to mongodb'''

    def __init__(self):
        MieThread.__init__(self, name="mongoThread")
        self.lock = threading.RLock()
        self.mque = deque()

        # mongo client
        host = ("ses/mgo/host", '127.0.0.1')
        port = ("ses/mgo/port", 27017)
        ena = ("ses/enable", True)
        self.mgoclient = MgoClient(conf, host, port, ena)

        self.start()

    def mque_put(self, msg, key=None, wakeup=True, left=False):
        klog.d(msg, ":", key)
        self.lock.acquire()
        try:
            if left:
                self.mque.appendleft((msg, key))
            else:
                self.mque.append((msg, key))
            if wakeup:
                self.wakeup()
        except:
            pass
        finally:
            self.lock.release()

    def mque_get_first(self):
        self.lock.acquire()
        try:
            ret = self.mque[0]
        except:
            ret = None
        finally:
            self.lock.release()
        return ret

    def mque_pop_first(self):
        self.lock.acquire()
        try:
            ret = self.mque.popleft()
        except:
            ret = None
        finally:
            self.lock.release()
        return ret

    def mque_clr(self):
        self.lock.acquire()
        self.mque.clear()
        self.lock.release()

    def act(self):
        while True:
            ret = self.mque_pop_first()
            if not ret:
                break

            msg, key = ret
            try:
                client = self.mgoclient.client().yihe
                dic = {
                    "msg": msg,
                    "key": key
                }
                client.evtlog.insert_one(dic)
                klog.d("Push one message to mongodb...")
            except:
                klog.e(traceback.format_exc())
                self.mque_put(msg=msg, key=key, left=True)

        return 60


class MessageSink():
    mgoThread = MongoThread()

    @classmethod
    def put(cls, msg, key=None):
        cls.mgoThread.mque_put(msg, key)


def produce(msg, key=None):
    MessageSink.put(msg, key)


if __name__ == "__main__":
    import time
    klog.to_stdout()
    while True:
        for x in range(100):
            produce(str(x), str(x * x))
            time.sleep(1)
        time.sleep(0.1)
