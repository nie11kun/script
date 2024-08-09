#!/bin/bash

# 升级 pip 自身
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# 获取所有已安装的包并升级
echo "Upgrading all packages..."
packages=$(pip list --format=json | python3 -c "import sys, json; print('\n'.join([pkg['name'] for pkg in json.load(sys.stdin) if pkg['name'] != 'pip']))")

for package in $packages
do
    echo "Upgrading $package..."
    pip install --upgrade "$package"
done

echo "All packages have been upgraded."
