LogFile[0]="/var/log/nginx/access.log"
LogFile[1]="/var/log/nginx/error.log"
LogFile[2]="/var/log/v2ray/access.log"
LogFile[3]="/var/log/v2ray/error.log"

rm ${LogFile[*]}.*

cat /dev/null ${LogFile[*]}
