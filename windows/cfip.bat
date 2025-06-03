@ECHO OFF
SETLOCAL EnableExtensions

:: save the active code page number parsing "Active code page: NNN" output from CHCP
for /F "tokens=4" %%G in ('chcp') do set "_chcp=%%G"

:: change the active console code page to UTF-8 
>NUL chcp 65001

:: echo pull last ip list:
:: cd "C:\Users\Marco Nie\Development\VPN\IPDB\"
:: git reset --hard origin/master
:: git clean -fxd
:: git pull

echo.
echo test ip list:
cd "C:\Users\Marco Nie\Application\CloudflareST_windows_amd64"
".\CloudflareST.exe" -url https://niekun.net/cloud/media/speedtest.png -p 0 -tll 50 -tl 300 -n 1000 -o "result.csv"

:: start notepad "result.csv"

echo.
echo finded ip:
type "result.csv"

echo.
echo ip list can be use:
for /f "delims=," %%a in (' type "result.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
