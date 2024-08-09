# 创建一个临时文件
$tempFile = New-TemporaryFile

try {
    # 运行pip freeze并将结果保存到临时文件
    pip freeze | Out-File -FilePath $tempFile.FullName

    # 读取临时文件内容
    $packages = Get-Content -Path $tempFile.FullName

    # 遍历包列表并卸载
    foreach ($package in $packages) {
        if ($package -notmatch '^(pip|setuptools|wheel)==') {
            $packageName = ($package -split '==')[0]
            Write-Host "Uninstalling $packageName..."
            pip uninstall -y $packageName
        }
    }
}
finally {
    # 删除临时文件
    Remove-Item -Path $tempFile.FullName -Force
}

Write-Host "All packages have been uninstalled except pip, setuptools, and wheel."
