#!/usr/bin/env bash

echo pull last ip list:
cd "/Users/marconie/Development/VPN/cloudflare"
git reset --soft HEAD^ && git reset && git checkout . && git add * && git stash && git pull

echo
echo test ip list:
cd "/Users/marconie/Apps/CloudflareST_darwin_amd64"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Google Cloud - 日本 东京.txt" -o "result-google-jp.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Google Cloud - 美国 阿什本.txt" -o "result-google-us.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Amazon Web Services - 中国 香港.txt" -o "result-amazon-hk.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Amazon Web Services - 日本 东京.txt" -o "result-amazon-jp.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/CTM - 中国 澳门.txt.txt" -o "result-ctm.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/HGC - 中国 香港.txt" -o "result-hgc.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/HKT - 中国 香港.txt" -o "result-hkt.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Microsoft Azure - 中国 香港.txt" -o "result-azure.csv"
./CloudflareST -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "/Users/marconie/Development/VPN/cloudflare/Oracle Cloud - 日本 东京.txt" -o "result-oracle-jp.csv"

echo
echo finded ip:
cat "result-google-jp.csv"
cat "result-google-us.csv"
cat "result-amazon-hk.csv"
cat "result-amazon-jp.csv"
cat "result-ctm.csv"
cat "result-hgc.csv"
cat "result-hkt.csv"
cat "result-azure.csv"
cat "result-oracle-jp.csv"

echo
echo ip list can be use:
awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-google-jp.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-google-us.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-amazon-hk.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-amazon-jp.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-ctm.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-hgc.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-hkt.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-azure.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done

awk -F, '/\./ {if($6 != "0.00") {print $1}}' result-oracle-jp.csv | while read output; do
    ping -c 1 "$output" >/dev/null
    if [ $? -eq 0 ]; then
        echo "$output is ok"
    fi
done
