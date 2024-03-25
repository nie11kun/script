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
".\CloudflareST.exe" -url https://nie11kun.github.io/usr/uploads/2024/03/1281212428.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\IPDB\bestcf.txt" -o "bestcf.csv"
".\CloudflareST.exe" -url https://nie11kun.github.io/usr/uploads/2024/03/1281212428.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\IPDB\bestproxy.txt" -o "bestproxy.csv"
".\CloudflareST.exe" -url https://nie11kun.github.io/usr/uploads/2024/03/1281212428.png -p 0 -f "C:\Users\Marco Nie\Development\VPN\IPDB\proxy.txt" -o "proxy.csv"

:: start notepad "result-google.csv"
:: start notepad "result-amazon.csv"

echo.
echo finded ip:
type "bestcf.csv"
type "bestproxy.csv"
type "proxy.csv"

echo.
echo ip list can be use:
for /f "delims=," %%a in (' type "bestcf.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "bestproxy.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
for /f "delims=," %%a in (' type "proxy.csv" ') do ping -n 1 %%a >nul && (echo %%a ok)
