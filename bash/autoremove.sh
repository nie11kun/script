LOCALDIR="/home/www/cloud/temp/*"

LOCALAGE="1"

cd ${LOCALDIR} || exit

find ${LOCALDIR} -type f -mtime +${LOCALAGE} -exec rm -f {} \;
find ${LOCALDIR} -mtime +${LOCALAGE} -exec rm -rf {} \;
