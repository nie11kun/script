LOCALDIR="/home/www/cloud/temp/"

LOCALAGE="1"

cd ${LOCALDIR} || exit

find ${LOCALDIR}*

find ${LOCALDIR}* -mtime +${LOCALAGE} -exec rm -rf {} \;