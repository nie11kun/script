#!/usr/bin/env bash

echo pull last ip list:
cd "/Users/marconie/Development/VPN/cloudflare"
git reset --soft HEAD^ && git reset && git checkout . && git add * && git stash && git pull

echo
echo test ip list:
cd "/Users/marconie/Apps/CloudflareST_darwin_amd64"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Google Cloud.txt" -o "result-google.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Amazon Web Services - 中国 香港.txt" -o "result-amazon.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/BGP Network - 中国 香港.txt" -o "result-bgp.csv"

echo
echo finded ip:
cat "result-google.csv"
cat "result-amazon.csv"
cat "result-bgp.csv"

echo
echo ip list can be use:
awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-google.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-amazon.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-bgp.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done
