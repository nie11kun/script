$WinNetIP=$(Get-NetIPAddress -InterfaceAlias 'vEthernet (WSLCore)' -AddressFamily IPV4) # get android network gateway addr
adb connect 127.0.0.1:58526 # android port
adb shell settings put global http_proxy "$($WinNetIP.IPAddress):1082" # local proxy port
