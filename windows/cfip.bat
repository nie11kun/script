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
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Google Cloud.txt" -o "result-google.csv"
".\CloudflareST.exe" -url https://niekun.net/cloud/other/cfspeedtest.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Amazon Web Services - 中国 香港.txt" -o "result-amazon.csv"

:: start notepad "result-google.csv"
:: start notepad "result-amazon.csv"

echo.
echo finded ip:
type "result-google.csv"
type "result-amazon.csv"

echo.
echo ip list can be use:
for /f "delims=," %%a in (' type "result-google.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "result-amazon.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
