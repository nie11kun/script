LogFile[0]="/var/log/nginx/access.log"
LogFile[1]="/var/log/nginx/error.log"
LogFile[2]="/var/log/v2ray/access.log"
LogFile[3]="/var/log/v2ray/error.log"

if [ -f "${LogFile[*]}.*" ]; then
    rm ${LogFile[*]}.*
fi

if [ -f "${LogFile[*]}" ]; then
    cat /dev/null ${LogFile[*]}
fi
