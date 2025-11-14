@echo off
REM 尝试停止现有的v2ray进程
taskkill /f /im v2ray.exe

REM 清理日志
type nul > "C:\Users\Marco Nie\Application\v2ray\log"\access.log
type nul > "C:\Users\Marco Nie\Application\v2ray\log"\error.log

REM 切换到v2ray目录 (使用 /d 确保可以切换驱动器)
cd /d "C:\Users\Marco Nie\Application\v2ray"

REM 启动v2ray
REM 使用 start /b 可以在批处理退出后让v2ray继续在后台运行
start "V2Ray" /b v2ray run -format jsonv5
exit