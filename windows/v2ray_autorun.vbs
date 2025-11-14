Option Explicit
Dim WshShell, BatPath

' 创建WScript.Shell对象
Set WshShell = CreateObject("WScript.Shell")

' 获取当前VBS脚本所在的目录
BatPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' 拼接 .bat 文件的完整路径
BatPath = """" & BatPath & "v2ray_autorun.bat" & """"

' 运行 .bat 文件
' 语法: WshShell.Run (路径, 窗口样式, 是否等待执行完毕)
' 0 = 隐藏窗口
' False = 不等待脚本执行完毕
WshShell.Run BatPath, 0, False

Set WshShell = Nothing
WScript.Quit