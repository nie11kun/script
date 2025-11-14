@echo off
REM 尝试停止现有的frpc进程
taskkill /f /im frpc.exe

REM 切换到 frp 目录 (使用 /d 确保可以切换驱动器)
cd /d C:\frp

REM 启动 frpc 客户端
REM 使用 start /b 可以在批处理退出后让 frpc 继续在后台运行
start "FRP_Client" /b frpc -c frpc.toml

exit