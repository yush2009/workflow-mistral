#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import time
import requests
import traceback
import urllib
import json

from bottle import post, request
import pymongo

from mie.bottlemisc import bodydic
from mie.xlogger.klog import klog
from mie.bprint import varfmt
from mie.dotdict import DotDict
import mie.confcenter

conf = mie.confcenter.getdefcc()
conf.alias("MGO_IPADDR", "ses/mgo/ipAddr", "10.9.63.168")

client = pymongo.MongoClient(conf.MGO_IPADDR)

rrque = client.yeehaw.rrQueue   # not run yet
rrdone = client.yeehaw.rrDone   # Already called.


def rrAdd(dic):
    inserted_id = exId + taskId + etc
    # TODO: save to db
    '''
    1. use user.input
    2. use user.output - means do not call requests.method()
    3. use user.status - force set r.status
    '''
    res = rrque.insert_one(dic.todic())
    return res.inserted_id

def rrRem(rrId):
    # TODO
    rrque.remove(rrId)
    res = rrDone.insert_one("_id": rrId, dic.todic())

def rrClr(rrId):
    rrque.remove(rrId)
    rrdone.remove(rrId)


# vim: sw=4 ts=4 sts=4 ai et
