#!/bin/bash

# 升级 pip 自身
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# 获取所有已安装的包并升级
echo "Upgrading all packages..."
pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U

echo "All packages have been upgraded."
