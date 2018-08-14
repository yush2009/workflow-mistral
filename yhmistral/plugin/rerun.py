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
tbl = client.yeehaw.session


def sesCreate(dic):
    # Create a new session

    try:
        psid = dic.get("x__psid")

        res = tbl.find_one({"_id": psid})
        if res:
            return psid

        res = tbl.insert_one(dic.todic())
        klog.d(res.inserted_id)
        return str(res.inserted_id)
    except:
        klog.e(traceback.format_exc())
        return "OK"


def sesPush(dic):
    # Add action node

    """
    p.update({"_id":sid},{"$push":{"actions":"Test"}})
    p.update({"_id":sid},{"$addToSet": {"tags":{"$each":["Python","Each"]}}})
    """

    try:
        sid = dic.get("x__sid")

        res = tbl.find_one({"_id": sid})
        if res:
            return ""

        dic.createat = time.time()
        tbl.update({"_id": sid}, {"$push": {"actions": dic.todic()}})
    except:
        pass

    return "OK"


def sesRollback(dic):
    # Call all the rollback of saved action

    def gen_rollback_url(url, sid):
        urlp = urllib.parse.urlparse(url)
        if urlp.query:
            return "%s&action=rollback&sid=%s" % (url, sid)
        else:
            return "%s?action=rollback&sid=%s" % (url, sid)

    sid = dic.get("x__sid")

    res = tbl.find({"_id": sid})
    if not res:
        klog.e("BAD SID:", sid)
        return "OK"
    klog.d(varfmt(res))

    for n in res.nodes:
        try:
            url = gen_rollback_url(n.url, sid)
            klog.d("ROLLBACK: URL: %s" % url)

            param = n.param
            klog.d("ROLLBACK: DAT: %s" % str(param))

            requests.post(url, param)
            klog.d("ROLLBACK: OK")
        except:
            klog.e("ROLLBACK: NG")

    # Drop this table
    tbl.drop()
    return "OK"


def sesDump(dic):
    sid = dic.get("x__sid")

    res = tbl.find({"_id": sid})
    klog.d(res)
    return res


@post("/session")
def doSession():
    """
    {
        # Parent Session ID, Only for sesCreate
        x__psid: xxx

        # Current Session ID, NOT for sesCreate
        x__sid: xxx

        # Command
        x__cmd: xxx

        # Other fields
        ...
    }
    """

    funcMap = {
        # Create a session
        "Create": sesCreate,

        # Rollback/Undo this session
        "Rollback": sesRollback,

        # Push one action/node to session
        "Push": sesPush,

        # Return current session info
        "Dump": sesDump,
    }

    try:
        payload = (request.body.read() or "").decode("utf-8")
        klog.d(payload)
        root = DotDict(json.loads(payload, strict=True))
        klog.d(root)
        calldic = root

        # calldic = bodydic()
        klog.d(calldic)
        klog.d(varfmt(calldic))
        return funcMap.get(calldic.x__cmd, lambda dic: "BadCommand")(calldic)
    except:
        klog.e(traceback.format_exc())
        return "OK"

# vim: sw=4 ts=4 sts=4 ai et
