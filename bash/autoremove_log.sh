LogDir[0]="/var/log/nginx/"
LogDir[1]="/var/log/v2ray/"

LogFile[0]="access.log"
LogFile[1]="error.log"

rm ${LogFile[*]}${LogFile[*]}*

cat /dev/null ${LogFile[*]}${LogFile[*]}
