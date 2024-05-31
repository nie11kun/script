# windows 执行 python setup.py build 打包
# macOS 执行 python3 setup.py bdist_mac 打包

from cx_Freeze import setup, Executable
import sys

# 安装依赖
build_exe_options = {
    "packages": [
        "pandas", "numpy", "scipy", "plotly", "tkinter", "ezdxf", 
        "llvmlite", "numba", "packaging", "pyparsing", "customtkinter", 
        "pytz", "six", "tenacity", "typing_extensions", "tzdata",
        "certifi", "idna", "requests", "urllib3"
    ],
    "excludes": ["unittest", "email"],
    "include_files": [
        # 在这里添加你需要的额外文件，例如数据文件或配置文件
        # ("path/to/datafile", "datafile"),
        # ("path/to/configfile", "configfile"),
    ],
    "includes": [
        "pandas._libs.tslibs.np_datetime",
        "pandas._libs.tslibs.nattype",
        "pandas._libs.tslibs.period",
        "pandas._libs.tslibs.timedeltas",
        "pandas._libs.tslibs.timestamps",
    ],
}

# 基础设置
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # 如果是 GUI 程序（无控制台），将其设置为 "Win32GUI"

# 主执行文件
executables = [
    Executable(
        "main.py",  # 你的主脚本文件
        base=base,
        target_name="InterferenceGrindingDressing" if sys.platform == "darwin" else "InterferenceGrindingDressing.exe",
        icon="icon.icns" if sys.platform == "darwin" else "icon.ico",  # 图标文件
    )
]

# 配置 setup 函数
setup(
    name="InterferenceGrindingDressing",
    version="1.0",
    description="干涉磨削砂轮修整软件",
    options={"build_exe": build_exe_options},
    executables=executables,
)
