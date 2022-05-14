@ECHO OFF
SETLOCAL EnableExtensions

:: save the active code page number parsing "Active code page: NNN" output from CHCP
for /F "tokens=4" %%G in ('chcp') do set "_chcp=%%G"

:: change the active console code page to UTF-8 
>NUL chcp 65001

cd "C:\Users\Marco Nie\Development\VPN\cloudflare\"
git reset --hard origin/master
git clean -fxd
git pull

cd "C:\Users\Marco Nie\Application\CloudflareST_windows_amd64"
".\CloudflareST.exe" -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Google Cloud.txt" -o "result-google.csv"
".\CloudflareST.exe" -p 0 -f "C:\Users\Marco Nie\Development\VPN\cloudflare\Amazon Web Services - 中国 香港.txt" -o "result-amazon.csv"

start notepad "result-google.csv"
start notepad "result-amazon.csv"
