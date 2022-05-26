#!/bin/sh
# 删除超过 3 天的临时文件

LOCALDIR="/home/www/cloud/temp/"

LOCALAGE="3"

cd ${LOCALDIR} || exit

#find ${LOCALDIR}*

find ${LOCALDIR}* -mtime +${LOCALAGE} -exec rm -rf {} \;
