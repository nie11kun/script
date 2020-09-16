rm /opt/nginx/logs/access.log.*
rm /opt/nginx/logs/error.log.*

rm /opt/frp/frps.*.log

cat /dev/null > /var/log/v2ray/access.log
cat /dev/null > /var/log/v2ray/error.log
