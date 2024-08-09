import tempfile
import os
import subprocess

def uninstall_all_packages():
    # 创建一个临时文件
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        # 运行pip freeze并将输出写入临时文件
        subprocess.run(['pip', 'freeze'], stdout=temp_file, text=True)
        
        # 将文件指针移到文件开头
        temp_file.seek(0)
        
        # 读取文件内容
        packages = temp_file.read().splitlines()
    
    # 临时文件名
    temp_filename = temp_file.name
    
    # 卸载包
    for package in packages:
        if not package.startswith('pip'):
            subprocess.run(['pip', 'uninstall', '-y', package])
    
    # 删除临时文件
    os.unlink(temp_filename)

# 运行函数
uninstall_all_packages()