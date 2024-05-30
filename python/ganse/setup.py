from cx_Freeze import setup, Executable

# 执行 python setup.py build 打包

executables = [Executable("main.py")]

setup(
    name="InterferenceGrindingDressing",
    version="0.1",
    description="干涉磨削砂轮修整软件",
    executables=executables,
)
