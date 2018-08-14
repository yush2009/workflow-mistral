#!/usr/bin/env python2
# -*- coding: utf_8 -*-

import os
import time
import pymongo
import json

from pykafka import KafkaClient

from mie.xlogger.klog import klog

from mie.xlogger.confmon import ccmon as ccmlog
from mie.confcenter import XConfCenter

rwcfg = os.environ.get("YH_CFG") or "%s/yh.cfg" % exedir
conf = XConfCenter(group="yh", rw_cfg=rwcfg)
ccmlog(conf)

klog.to_stdout()


def main():
    #
    # kafka
    #
    urls = conf.xget("kafka/url", '')
    topic = conf.xget("kafka/topic", 'mistral')

    klog.d("Trying to connect kafka server...")
    klog.d("Server: ", urls)
    klog.d("Topic: ", topic)
    kfkclients = kfkproducer = None
    while True:

        kfkclients = KafkaClient(hosts=urls)
        kfkproducer = kfkclients.topics[topic].get_producer(sync=True)

        if kfkclients and kfkproducer:
            break
        time.sleep(60)

    #
    # mongodb
    #
    host = conf.xget("ses/mgo/host", '127.0.0.1')
    port = conf.xget("ses/mgo/port", 27017)

    klog.d("Trying to connect mongodb server...")
    klog.d("Server: ", host, "  Port: ", port)
    mgoclient = evtlog = None
    while True:
        mgoclient = pymongo.MongoClient(host=host, port=port)
        evtlog = mgoclient.yihe.evtlog

        if mgoclient and evtlog:
            break
        time.sleep(60)

    #
    # working loop
    #
    broker_error_count = 0
    while True:
        cursor = evtlog.find().sort("$natural", 1).limit(100)
        if cursor.count() <= 0:
            time.sleep(0.2)
            continue

        klog.d("Kafka Message Count:", cursor.count())
        idfirst = idlast = None
        for item in cursor:
            if not idfirst:
                idfirst = item.get("_id")
            idlast = item.get("_id")

            msg = item.get("msg")
            key = item.get("key")
            try:
                klog.d(idlast, json.dumps(msg))
                msg = msg.encode('utf-8')
                kfkproducer.produce(msg, key)
                evtlog.remove({"_id": idlast})
                broker_error_count = 0
            except Exception as e:
                klog.e(str(e))
                broker_error_count = broker_error_count + 1
                break

        # calculate sleep time
        wait = 0.5 if broker_error_count < 10 else 0.5 * min(broker_error_count, 1000)
        time.sleep(wait)


if __name__ == "__main__":
    main()
