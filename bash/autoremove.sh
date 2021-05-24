#!/bin/sh

LOCALDIR="/home/www/cloud/temp/"

LOCALAGE="3"

cd ${LOCALDIR} || exit

#find ${LOCALDIR}*

find ${LOCALDIR}* -mtime +${LOCALAGE} -exec rm -rf {} \;
