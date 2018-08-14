#!/bin/bash
docker rm -f yh
docker run -d -v /root/yh:/ttt --name yh -e YH_CFG=/root/yh.cfg -e YH_HOOK_CMD=/ttt/yhhook.sh -e MYNAME=yh -p 8989:8989 -p 9898:9898 ctbri/mistral-all

