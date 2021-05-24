#!/bin/sh

LOGFILE="/home/log/submit_code.log"

telegram-cli -U root -W -e "msg yeyeye test" >> ${LOGFILE}
