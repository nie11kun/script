from library.curve_to_wheel_points import curve_to_wheel_points
from library.calc import remove_leading_whitespace, parse_coordinates, plot_coordinates
from decimal import Decimal

# 砂轮杆偏移工件中心最大距离
gan_distance_max = 17.8

# 砂轮杆偏移工件中心最小距离
gan_distance_min = 17.5

# 砂轮直径步进
step_dia = 0.2

# 砂轮安装角
gan_angle = 5

# 工件中径
mid_dia = 45

# 导程
work_lead = 45

# ****************************

# 齿型程序个数
dia_num = int((Decimal(f'{gan_distance_max}') - Decimal(f'{gan_distance_min}')) / Decimal(f'{step_dia / 2}'))

size = 100
wheel_dia = [i for i in range(size)]
wheel_dia_str = [i for i in range(size)]
file_content = [i for i in range(size)]
point_string = [i for i in range(size)]

for i in range(dia_num+1):
    wheel_dia[i], file_content[i], point_string[i] = curve_to_wheel_points(gan_distance=gan_distance_min+step_dia/2*i, gan_angle=gan_angle, mid_dia=mid_dia, work_lead=work_lead, if_plot=False)

    # 将直径转换为4位小数的字符串 并替换小数点为下划线
    wheel_dia_str[i] = f"{wheel_dia[i]:.4f}".replace('.', '_')

head_content = f"""
;********************************
DEF REAL VER_MODE,WHEEL_DIA
DEF AXIS AX_HORI,AX_VER
AX_HORI=AXNAME(AXIS_HORI)
AX_VER=AXNAME(AXIS_VER)
VER_MODE=DRESSER[50]
WHEEL_DIA=DRESSER[24]
;********************************

IF (WHEEL_DIA>={wheel_dia[0]:.4f}) GOTOF DIA_{wheel_dia_str[0]};
"""

for i in range(1,dia_num+1):
    head_content += f'IF (WHEEL_DIA<{wheel_dia[i-1]:.4f}) AND (WHEEL_DIA>={wheel_dia[i]:.4f}) GOTOF DIA_{wheel_dia_str[i]};\n'

head_content += f"""
IF (WHEEL_DIA<{wheel_dia[dia_num]:.4f}) GOTOF DIA_{wheel_dia_str[dia_num]};

;********************************
"""

# 将内容写入文件
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(head_content)

for i in range(dia_num+1):
    # 将内容写入文件
    with open("output.txt", "a", encoding="utf-8") as f:
        f.write(file_content[i])

# 删除文本中的缩进
remove_leading_whitespace("output.txt","output.txt")

# 解析坐标
points1 = parse_coordinates(point_string[0])
points2 = parse_coordinates(point_string[1])

# 绘制坐标
plot_coordinates(points1, points2)
