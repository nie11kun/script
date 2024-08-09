# 升级 pip 自身
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

# 获取所有已安装的包并升级
Write-Host "Upgrading all packages..."
$packages = pip list --outdated --format=freeze | ForEach-Object { $_.Split('==')[0] }
foreach ($package in $packages) {
    Write-Host "Upgrading $package..."
    pip install --upgrade $package
}

Write-Host "All packages have been upgraded."
