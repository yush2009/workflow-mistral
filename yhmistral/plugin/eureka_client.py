#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import logging

from mie.xlogger.klog import klog
from mie.bprint import varfmt
import mie.confcenter


conf = mie.confcenter.getdefcc()


def _get_app_url(instances):
    """
    Get one url of app from all up app instance
    :param result:
    :return:
    """
    if instances and isinstance(instances, dict):
        for instance in instances["application"]["instance"]:
            if instance["status"] == "UP":
                return instance["homePageUrl"]

    return None

def get_app_url(app_name):
    """

    :param app_name:  string, name of app when register
    :return:
    """
    app_url = None
    if conf.EUREKA_ENABLE:
        url = conf.EUREKA_URL + "/apps/" + app_name
        try:
            resp = requests.get(url=url, headers={"Accept": "application/json"}, timeout=0.5)
            klog.d("Query app <", app_name, "> url:", resp.status_code, resp.content)
            if resp.ok:
                r = resp.json()
                app_url = _get_app_url(r)
        except Exception as e:
            klog.d("Eureka Error: ", e)

    if not app_url:
        if app_name==conf.APP_NAME_API:
            return conf.YIHE_API_HOST
        elif app_name==conf.APP_NAME_CALLBACK:
            return conf.YIHE_ASYNC_CALLBACK_HOST

    return app_url



if __name__ == "__main__":
    if not conf:
        conf = mie.confcenter.XConfCenter(group="yh", rw_cfg="/root/yh.cfg")

    conf.alias("EUREKA_ENABLE", "eureka/enable", True)
    conf.alias("EUREKA_URL", "eureka/base_url", "http://172.16.90.96:3103")
    conf.alias("APP_NAME_CALLBACK", "engine/callback_name", "WORKFLOW-ENGINE-CALLBACK")
    conf.alias("APP_NAME_API", "engine/api_name", "WORKFLOW-ENGINE-API")
    conf.alias("YIHE_API_HOST", "engine/api_host", "http://127.0.0.1:9898")
    conf.alias("YIHE_ASYNC_CALLBACK_HOST", "engine/callback_host", "http://127.0.0.1:9898")

    host = get_app_url(conf.APP_NAME_CALLBACK)
    print host