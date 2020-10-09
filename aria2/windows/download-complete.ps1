$var1 = $args[0]

# Write-Output $var1
Add-Type -AssemblyName System.Windows.Forms
$global:balmsg = New-Object System.Windows.Forms.NotifyIcon
$path = (Get-Process -id $pid).Path
$balmsg.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon($path)
$balmsg.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Warning
$balmsg.BalloonTipText = "Path is $var1"
$balmsg.BalloonTipTitle = "download complete"
$balmsg.Visible = $true
$balmsg.ShowBalloonTip(20000)
