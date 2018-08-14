# 状态通知接口

状态通知接口是由业务系统提供的接口，工作流引擎将内部工作流状态的变化，通过该接口通知给业务系统。

#### 状态通知接口

##### 工作流引擎状态通知
kafka
[topic] service
```json
{
    "serviceName": "string",
    "version": "string",
    "status": "string",
    "timeStamp": "string"
}
```

Example:
 - serviceName=workflow_engine,
 - version=v2.0,
 - status=up,
 - timeStamp=2017-10-28 09:43:12
 
##### 工作流执行状态通知
kafka
[topic] mistral

```json
{
    "eType": "string",
    "wfId": "string",
    "exId": "string",
    "taskId": "string",
    "taskName": "string",
    "atomId": "string",
    "triggeredBy": "object",
    "status": "string",
    "input": "object",
    "output": "object",
    "timeStamp": "string"
}
```

- **eType** - 事件类型：
  - Task
    - **task_start** - 开始执行
    - **task_running** - 执行中
    - **task_end** - 执行结束
    - **task_redo** - 该Task被Retry
    - **task_pass** - 跳过此Task并直接返回指定的结果
    - **task_rollback** - 在rollback过程，那些执行了的Task
  - Execution
    - **execution_start**
    - **execution_end**
    - **execution_abort**
    - **execution_rollback_start**
    - **execution_rollback_end**
- **wfId** - 所在工作流的ID。
- **exId** - 所在Execution的ID。
- **taskId** - 正在执行的Task
- **input** - task_start 时，传递给该action的输入参数。
- **output** - task_end或者task_error时，该action的返回值。
- **timeStamp** - 事件发生时，工作流引擎所在系统的本地时间。


- **Example:**
    ```json
    {
        "eType": "task_start",
        "wfId": "0b9cc8a4-dd52-4e7b-ba09-52fcb9e93166",
        "exId": "8a54c0f2-9927-44f4-953d-8ac72ef12230",
        "taskId": "eac1e35b-ff01-419d-bdf9-997155fdd3ba",
        "taskName": "A27510_7_68366_780_69844",
        "atomId": "Network.Fix-L3-VPN.DCI-RESOURCE-PREEMPTION",
        "triggeredBy": [{"event": "on-success", "taskId": "4fe82c39-25fb-415d-ac7b-074f7919e114"}],
        "status": "RUNNING",
        "input":{},
        "output": {},
        "timeStamp": "2017-10-28 09:43:12"
    }  
    ```

- **说明:**
  - 如果task是异步的调用，则会在调用原子能力（微服务接口）后，通过一条eType=task_running的消息告知原子能力返回的http response，在原子能力回调后会有一条eType=task_end的消息告知原子能力的执行结果

- **triggeredBy字段的约定**
    ```json
    [
      {
        "event": "on-success",
        "taskId": "4fe82c39-25fb-415d-ac7b-074f7919e114"
      },
      {
        "event": "on-success",
        "taskId": "3bb28873-6132-4025-b5fb-f68415c25e37"
      }
    ]
    ```

- **input字段的约定**
    ```json
    {
        "body": {
            "routeEntriesA": "1",
            "custName": "测试电路",
            "vpnLinkCode": "杭州DCIVPN87002A",
            "routeEntriesZ": "",
            "netStruct": "2008039002",
            "cePortIdZ": "",
            "routeProtocol": "2008038002",
            "custIpMaskZ": "",
            "vpnNetCode": "87002",
            "ceDeviceIdA": "9184011f893aff726ddabbb7efc512c9",
            "ctYUNRegEmail": "ctdcitest02@123.com",
            "vpcIpMaskA": "192.168.3.0",
            "ceDeviceIdZ": "",
            "vpcIpMaskZ": "",
            "custIpMaskA": "192.168.1.0/24;192.168.2.0/24",
            "dispatchCode": "中国电信翼翮[2018]480号",
            "cePortIdA": "ea3eb12eb34962a61859875d1179f7e7",
            "custId": "PRTY0000000000258582",
            "proInstId": "146733675",
            "dispatchTitle": "中国电信翼翮[2018]480号",
            "yunRespoolIdZ": "",
            "reqDate": "2018-04-18",
            "worktId": "20390",
            "azFlag": "A",
            "peIpZ": "",
            "ctYUNACCNBR": "ctdcitest02@123.com",
            "speedA": "2008024040",
            "cePortNameZ": "",
            "vpcIdZ": "",
            "ceVlanA": "1000",
            "peIpA": "10.100.194.138/30",
            "ceVlanZ": "",
            "vpcIdA": "967eca59-fb46-4b84-88eb-dfa96fc75f86",
            "cePortNameA": "10GE1/0/40",
            "speedZ": "",
            "yunRespoolIdA": "cn-hz1",
            "dispatchType": "2008098001",
            "workType": "2017110801",
            "vpcAccountA": "2",
            "ceIpA": "10.100.194.137/30",
            "ipSubnetMaskZ": "",
            "yunResCityA": "3001",
            "totalInterVPC": "2",
            "centerPoint": "2008045002",
            "ceDeviceNameZ": "",
            "yunGWPECircuitIdA": "杭州绍兴10GE0155DCI",
            "ceDeviceNameA": "AC-POP-6851-1",
            "asA": "65026",
            "yunGWPECircuitIdZ": "",
            "asZ": "",
            "ipSubnetMaskA": "24",
            "ceIpZ": "",
            "vpcAccountZ": "",
            "yunResCityZ": ""
        },
        "headers": {
            "Content-Type": "application/json"
        },
        "session": "9d0746b4-b5d0-4369-b1b4-4dd25f1cfeae",
        "atom": "Bisop.OrderOrcha.Cloud-Enable-DCI-Related-Task.ZTESoft-Any",
        "url": "http://172.16.158.7:3101/CloudClientService/cloudTaskDispatch",
        "method": "post"
    }
    ```

- **output字段的约定**
  - 成功调用原子能力的情况：output中应该返回完整的http response对象如下所示，其中content部分是http response的body内容
    ```json
    {
        "result": {
            "status": 200, 
            "encoding": "UTF-8", 
            "url": "http://172.16.158.7:3101/crmClientService/singleFinish", 
            "elapsed": 0.472783, 
            "content": {
                "code": 200
            }, 
            "headers": {
                "Date": "Thu, 12 Apr 2018 05:18:02 GMT", 
                "Transfer-Encoding": "chunked", 
                "Content-Type": "application/json;charset=UTF-8", 
                "X-Application-Context": "ite-oss-apigateway:3101"
            }
        } 
    }
    ```
    或
    ```json
    {
        "result": {
            "status": 501, 
            "encoding": "UTF-8", 
            "url": "http://172.16.158.7:3101/crmClientService/singleFinish", 
            "elapsed": 0.472783, 
            "content": {
                "code": 200137,
                "message": "链路带宽无法设置，设置的带宽10G超过限定"
            }, 
            "headers": {
                "Date": "Thu, 12 Apr 2018 05:18:02 GMT", 
                "Transfer-Encoding": "chunked", 
                "Content-Type": "application/json;charset=UTF-8", 
                "X-Application-Context": "ite-oss-apigateway:3101"
            }
        } 
    }

    ```
  - 原子能力无法访问的情况：需要在output中说明错误原因
    ```json
    {
        "result": {
            "status": 598,
            "content": {
                "fault": "http request error!",
                "faultString": "http请求超时，重试3次后依然失败",
                "orgRequest": {    
                    "url": "http://172.16.158.7:3101/CloudClientService/cloudTestTask", 
                    "method": "post",
                    "headers": {
                        "Content-Type": "application/json"
                    }, 
                    "body": {
                        "dispatchCode": "中国电信翼翮[2018]485号", 
                        "reqDate": "2018-04-17", 
                        "worktId": "20540", 
                        "proInstId": "146734465", 
                        "workType": "2017110801"
                    } 
                }
            }     
        }
    }
  
  - 工作流引擎内部出现问题的情况：output中应该返回错误提示，明确说明错误原因，示例如下所示
    ```json
    {
        "result": {
            "status": 599,
            "content": {
                "fault": "workflow engine internal error!",
                "faultString": "解析原子能力返回值发生Exception: ..."
            }
        }
    }
    ```