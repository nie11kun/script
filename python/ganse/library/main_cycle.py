from library.curve_to_wheel_points import curve_to_wheel_points
from library.calc import remove_leading_whitespace, parse_coordinates, plot_coordinates, read_file
from decimal import Decimal
import numpy as np
import matplotlib.pyplot as plt

def main_cycle(gan_distance_max, gan_distance_min, step_dia, gan_angle, mid_dia, work_lead, dresser_r, shape_num, dxf_file, save_path):
    # 齿型程序个数
    dia_num = int((Decimal(f'{gan_distance_max}') - Decimal(f'{gan_distance_min}')) / Decimal(f'{step_dia / 2}'))

    size = 100
    wheel_dia = [i for i in range(size)]
    wheel_dia_str = [i for i in range(size)]
    file_content = [i for i in range(size)]
    point_string = [i for i in range(size)]

    for i in range(dia_num+1):
        if i == 0:
            is_plot = True
        else:
            if i == dia_num:
                is_plot = True
            else:
                is_plot = False
        
        wheel_dia[i], file_content[i], point_string[i] = curve_to_wheel_points(dxf_file=dxf_file, gan_distance=gan_distance_min+step_dia/2*i, gan_angle=gan_angle, mid_dia=mid_dia, work_lead=work_lead, dresser_r=dresser_r, shape_num=shape_num, if_plot=is_plot)

        # 将直径转换为4位小数的字符串 并替换小数点为下划线
        wheel_dia_str[i] = f"{wheel_dia[i]:.4f}".replace('.', '_')

    head_content = f"""
    ;砂轮直径范围:{wheel_dia[0]:.4f} - {wheel_dia[dia_num]:.4f}
    ;砂轮杆安装角:{gan_angle}
    ;工件螺旋升角:{np.rad2deg(np.arctan2(work_lead, np.pi * mid_dia)):.4f}
    ;工件中径:{mid_dia}
    ;工件导程:{work_lead}
    ;滚轮圆弧半径:{dresser_r}
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
    """

    file_name = f"{save_path}/" + f"GS_{mid_dia}_{work_lead}".replace('.', '_') + '.SPF'

    # 将内容写入文件
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(head_content)

    for i in range(dia_num+1):
        # 将内容写入文件
        with open(file_name, "a", encoding="utf-8") as f:
            f.write(file_content[i])

    # 删除文本中的缩进
    remove_leading_whitespace(file_name,file_name)

    # 比较文件路径
    # file1_path = 'file1.txt'

    # 读取文件内容
    # str1 = read_file(file1_path)

    if dia_num >= 1:
        # 解析坐标
        points1 = parse_coordinates(point_string[0])
        points2 = parse_coordinates(point_string[1])

        # 绘制坐标
        plot_coordinates(points1, points2)

    plt.show()
