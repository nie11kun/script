LOCALDIR="/home/www/cloud/temp/"

LOCALAGE="1"

cd ${LOCALDIR} || exit

print(find ${LOCALDIR}*)

find ${LOCALDIR}* -mtime +${LOCALAGE} -exec rm -rf {} \;
