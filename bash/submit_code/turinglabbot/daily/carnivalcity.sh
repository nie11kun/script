#!/bin/sh

LOGFILE="/home/log/submit_code.log"

docker exec -it jd_scripts /bin/sh -c 'node /scripts/jd_carnivalcity.js'

sleep 1m

CODE=$(awk -F】 '/京东手机狂欢城好友互助码/ {print $NF}' /opt/jd_scripts/logs/jd_carnivalcity.log  | tail -1)

telegram-cli -e "msg @TuringLabbot /submit_activity_codes carnivalcity ${CODE}"
