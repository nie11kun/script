@ECHO OFF
SETLOCAL EnableExtensions

:: save the active code page number parsing "Active code page: NNN" output from CHCP
for /F "tokens=4" %%G in ('chcp') do set "_chcp=%%G"

:: change the active console code page to UTF-8 
>NUL chcp 65001

echo pull last ip list:
cd "C:\Users\Marco Nie\Development\VPN\cloudflare\"
git reset --hard origin/master
git clean -fxd
git pull

echo.
echo test ip list:
cd "C:\Users\Marco Nie\Application\CloudflareST_windows_amd64"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Google Cloud - 日本 东京.txt" -o "result-google-jp.csv"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Google Cloud - 美国 阿什本.txt" -o "result-google-us.csv"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Amazon Web Services - 中国 香港.txt" -o "result-amazon-hk.csv"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Amazon Web Services - 日本 东京.txt" -o "result-amazon-jp.csv"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\CTM - 中国 澳门.txt" -o "result-ctm.csv"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\HGC - 中国 香港.txt" -o "result-hgc.csv"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\HKT - 中国 香港.txt" -o "result-hkt.csv"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Microsoft Azure - 中国 香港.txt" -o "result-azure.csv"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Oracle Cloud - 日本 东京.txt" -o "result-oracle-jp.csv"

:: start notepad "result-google.csv"
:: start notepad "result-amazon.csv"

echo.
echo finded ip:
type "result-google-jp.csv"
type "result-google-us.csv"
type "result-amazon-hk.csv"
type "result-amazon-jp.csv"
type "result-ctm.csv"
type "result-hgc.csv"
type "result-hkt.csv"
type "result-azure.csv"
type "result-oracle-jp.csv"

echo.
echo ip list can be use:
for /f "delims=," %%a in (' type "result-google-jp.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "result-google-us.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "result-amazon-hk.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "result-amazon-jp.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "result-ctm.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "result-hgc.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "result-hkt.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "result-azure.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "result-oracle-jp.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
