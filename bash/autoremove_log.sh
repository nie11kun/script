#!/bin/bash

cat /dev/null > /opt/nginx/logs/access.log
cat /dev/null > /opt/nginx/logs/error.log

rm /opt/frp/frps.*.log

cat /dev/null > /var/log/v2ray/access.log
cat /dev/null > /var/log/v2ray/error.log

rm /home/log/submit_code.log
