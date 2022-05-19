#!/usr/bin/env bash

echo pull last ip list:
cd "/Users/marconie/Development/VPN/cloudflare"
git reset --soft HEAD^ && git reset && git checkout . && git add * && git stash && git pull

echo
echo test ip list:
cd "/Users/marconie/Apps/CloudflareST_darwin_amd64"
#./CloudflareST -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Google Cloud.txt" -o "result-google.csv"
#./CloudflareST -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Amazon Web Services - 中国 香港.txt" -o "result-amazon.csv"

echo
echo finded ip:
cat "result-google.csv"
cat "result-amazon.csv"

echo
echo ip list can be use:
awk -F, ' /\./ {print $1}' result-google.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, ' /\./ {print $1}' result-amazon.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done
