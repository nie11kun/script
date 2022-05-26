#!/bin/bash
# 批量修改文件夹内视频文件名称为标准名称
# 需要两个传递参数：媒体所在文件夹路径，标准媒体名称
# 例如 bash rename_media.sh /video/love love

cd "$1"
if [ $? == 1 ]; then
    exit
fi

reg='^([^0-9]*)([0-9][0-9]*)[^0-9]*([0-9][0-9]*).*(\....)$'
for filename in *.*; do
    if [[ $filename =~ $reg ]]; then
        printf -v newname "$2 - S%02dE%02d - 第 %d 集%s" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}" "${BASH_REMATCH[3]}" "${BASH_REMATCH[4]}"
        mv "$filename" "$newname"
    fi
done
exit
