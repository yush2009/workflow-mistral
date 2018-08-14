# This file used for kafaka messages loging.
# -*- coding: utf_8 -*-

import time
import wf_trace
import json
import kfk_client
import traceback
from mie.xlogger.klog import klog
from mie.bprint import varfmt, todict


def log(etype, atomId, status, wfId, exId, taskId=None, taskName=None, input=None, output=None, triggered_by=None):

    """Kafka调用接口

    :param etype: 事件类型
    :param atomId: 原子操作ID
    :param status: 状态
    :param wfId: 所在工作流的ID
    :param exId: 所在execition的ID
    :param taskId: 正在执行任务的ID
    :param taskName: 正在执行任务的名称
    :param input: 输入对象
    :param output: 输出对象
    :return:
    """
    if not etype:
        etype = "Unknown"
    if not wfId:
        wfId = "x01"
    if not exId:
        exId = "x02"
    if not taskId:
        taskId = ""
    if not taskName:
        taskName = ""
    if not atomId:
        atomId=""
    if not status:
        status="unknown"
    if not input:
        input = {}
    if not output:
        output = {}
    if not triggered_by:
        triggered_by = []

    try:
        message = KfkMessage(etype, wfId, exId, taskId, taskName, atomId, status, input, output, triggered_by)
        # print '#########################################'
        # wf_trace.info(KfkMessage, "Kafka Log : etype=%s,wfId=%s,exId=%s,"
        #                           "taskId =%s,taskName=%s,atomId=%s,"
        #                           "status=%s,input=%s,output=%s, triggered_by:%s, timestamp=%s" %
        #               (message.eType,message.wfId,message.exId,
        #                message.taskId,message.taskName,message.atomId,
        #                message.status,message.input,message.output, message.triggered_by, message.timeStamp))
        kfk_client.produce(message.to_str())
        # print '#########################################'
    except:
        klog.e("Kafka Message build fail: ", "etype=%s,wfId=%s,exId=%s,taskId=%s,taskName=%s" %
                (etype, wfId, exId, taskId, taskName) )
        klog.e(traceback.format_exc())

class KfkMessage():
    """ Mistral Status change message for Kafka

    {
        eType: "string",
        wfId: "string",
        exId: "string",
        taskId: "string",
        taskName: "string",
        atomId:"string",
        status: "string",
        input: "object",
        output: "object",
        timeStamp: "string"
    }
    """
    def __init__(self, eType=None, wfId=None, exId=None, taskId=None, taskName=None,
                 atomId=None, status=None, input=None, output=None, triggered_by=None):
        self.eType = eType
        self.wfId = wfId
        self.exId = exId
        self.taskId = taskId
        self.taskName = taskName
        self.atomId = atomId
        self.status = status
        self.input = json.dumps(input, ensure_ascii=False).encode("utf-8")
        self.output = json.dumps(output, ensure_ascii=False).encode("utf-8")
        self.triggered_by = json.dumps(triggered_by, ensure_ascii=False).encode("utf-8")
        self.timeStamp = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

    def to_str(self):
        str = '{"eType": "%s","wfId": "%s", "exId": "%s", "taskId": "%s", "taskName": "%s", ' \
              '"atomId": "%s", "status": "%s", "input": %s, "output": %s, "triggered_by":%s, ' \
              '"timeStamp": "%s"}' % \
              (self.eType, self.wfId, self.exId, self.taskId, self.taskName,
               self.atomId, self.status, self.input, self.output, self.triggered_by, self.timeStamp)
        return str.encode("UTF-8")
