rm /var/log/nginx/access.log.*
rm /var/log/nginx/error.log.*

rm frps.*.log

cat /dev/null > /var/log/v2ray/access.log
cat /dev/null > /var/log/v2ray/error.log
