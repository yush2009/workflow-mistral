#!/bin/bash
mkdir config-bak
docker cp yh:/root/yh.cfg /root/yh/config-bak/
docker cp yh:/root/yh_kfk.cfg /root/yh/config-bak/
docker cp yh:/etc/if.cfg /root/yh/config-bak/
docker cp yh:/etc/mistral/mistral.conf /root/yh/config-bak/
docker cp yh:/etc/mistral/logging.conf /root/yh/config-bak/
