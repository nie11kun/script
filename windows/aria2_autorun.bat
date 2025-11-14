@echo off
REM 尝试停止现有的 aria2c 进程
taskkill /f /im aria2c.exe

REM 切换到 aria2 目录 (USERPROFILE 路径)
cd /d %USERPROFILE%\Application\aria2

REM 启动 aria2c 进程
REM 使用 start /b 可以在批处理退出后让 aria2c 继续在后台运行
start "Aria2c" /b aria2c --conf-path=aria2.conf

exit