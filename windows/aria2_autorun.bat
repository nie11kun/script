@echo off
if "%1" == "h" goto begin
mshta vbscript:createobject("wscript.shell").run("""%~nx0"" h",0)(window.close)&&exit
:begin
REM
cd %USERPROFILE%\Application\aria2
aria2c --conf-path=aria2.conf
exit
