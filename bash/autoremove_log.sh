#!/bin/sh
# 删除日志文件

cat /dev/null > /opt/nginx/logs/access.log
cat /dev/null > /opt/nginx/logs/error.log

rm /opt/frp/frps.*.log

rm /home/backups/backup.log

cat /dev/null > /var/log/v2ray/access.log
cat /dev/null > /var/log/v2ray/error.log

# rm /home/log/submit_code.log
