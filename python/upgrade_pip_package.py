import subprocess
import sys

def upgrade_all_packages():
    # 获取所有可升级的包
    result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--outdated'], capture_output=True, text=True)
    packages = result.stdout.splitlines()[2:]  # 跳过前两行标题行

    for package in packages:
        package_name = package.split()[0]
        print(f"Upgrading {package_name}...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', package_name])

if __name__ == "__main__":
    upgrade_all_packages()