from library.curve_to_wheel_points import curve_to_wheel_points
from library.calc import remove_leading_whitespace

# 砂轮杆偏移工件中心距离
gan_distance = 18

# 砂轮安装角
gan_angle = 5

# 工件中径
mid_dia = 45

# 导程
work_lead = 45

wheel_dia, file_content = curve_to_wheel_points(gan_distance=gan_distance, gan_angle=gan_angle, mid_dia=mid_dia, work_lead=work_lead)

# 将直径转换为4位小数的字符串
wheel_dia_str = f"{wheel_dia:.4f}"

# 将小数点替换为下划线
wheel_dia_str = wheel_dia_str.replace('.', '_')

head_content = f"""
;********************************
DEF REAL VER_MODE,WHEEL_DIA
DEF AXIS AX_HORI,AX_VER
AX_HORI=AXNAME(AXIS_HORI)
AX_VER=AXNAME(AXIS_VER)
VER_MODE=DRESSER[50]
WHEEL_DIA=DRESSER[24]
;********************************

IF (WHEEL_DIA>={wheel_dia:.4f}) GOTOF DIA_{wheel_dia_str};
IF (WHEEL_DIA<{wheel_dia:.4f}) GOTOF DIA_{wheel_dia_str};

;********************************
"""

# 将内容写入文件
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(head_content)

# 将内容写入文件
with open("output.txt", "a", encoding="utf-8") as f:
    f.write(file_content)

# 删除文本中的缩进
remove_leading_whitespace("output.txt","output.txt")
