#!/bin/bash

LOGFILE="/home/log/submit_code.log"

telegram-cli -W -e "msg yeyeye test" >> ${LOGFILE}
