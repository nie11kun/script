#!/bin/bash

# 创建临时文件
temp_file=$(mktemp)

# 确保脚本结束时删除临时文件
trap "rm -f $temp_file" EXIT

# 获取所有已安装的包列表
pip freeze > "$temp_file"

# 读取临时文件并卸载包
while IFS= read -r package
do
    # 跳过pip、setuptools和wheel
    if [[ $package != pip==* && $package != setuptools==* && $package != wheel==* ]]; then
        package_name=$(echo "$package" | cut -d'=' -f1)
        echo "Uninstalling $package_name..."
        pip uninstall -y "$package_name"
    fi
done < "$temp_file"

echo "All packages have been uninstalled except pip, setuptools, and wheel."
