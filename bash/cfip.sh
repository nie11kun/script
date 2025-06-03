#!/usr/bin/env bash

echo test ip list:
cd "/Users/marconie/Apps/CloudflareST_darwin_amd64"
./CloudflareST -url https://niekun.net/cloud/media/speedtest.png -p 0 -tll 50 -tl 300 -n 1000 -o "result.csv"

echo
echo finded ip:
cat "result.csv"

echo
echo ip list can be use:
awk -F, '/\./ {if($6 != "0.00") {print $1}}' result.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done
