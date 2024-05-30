import numpy as np
import sys
import platform
import library.calc as libs
import plotly.graph_objs as go

def curve_to_wheel_points(dxf_file, gan_distance, gan_angle, mid_dia, work_lead, dresser_r=0, shape_num=500, if_plot=False, save_path=''):
    # 螺旋升角
    angle = np.rad2deg(np.arctan2(work_lead, np.pi * mid_dia))
    print(f'标准螺旋升角: {angle:.4f}')

    # dxf 曲线离散点精度
    segment_length = 0.01

    # 螺旋曲面绘制次数
    num_turns = 4500
    # 每个曲面移动角度
    turn_angle = 0.01

    # 判断法线是否相交的最小距离
    min_distance = 0.0001

    # ********************************

    # 定义新坐标系的原点
    new_origin = np.array([0, gan_distance, 0])

    # 将 gan_angle 转换为弧度
    gan_angle_rad = np.radians(gan_angle)

    # 定义新的坐标系基矢量 u 和 w
    u = np.array([np.cos(gan_angle_rad), 0, -np.sin(gan_angle_rad)])  # 顺时针旋转 gan_angle
    w = np.array([np.sin(gan_angle_rad), 0, np.cos(gan_angle_rad)])  # 顺时针旋转 gan_angle

    # 新坐标系的 y 轴方向
    v = np.array([0, 1, 0])

    # 构建转换矩阵
    transformation_matrix = np.array([u, v, w]).T

    # 偏移量
    offset = np.array([0, mid_dia / 2])

    # ********************************

    # 从 DXF 文件加载曲线，并应用偏移
    dxf_filename = dxf_file  # DXF 文件名
    curve_points = libs.load_dxf_curve(dxf_filename, offset, segment_length)

    # 如果没有 x0 这一点则添加
    curve_points = libs.add_point_if_missing(curve_points=curve_points, x0=0)

    # 按照逆时针 x0 为原点 小于 x0 递减 大于 x0 递增
    curve_points = libs.sort_points(curve_points, mode='apart')

    # 获取 curve_points 的点个数
    num_curve_points = len(curve_points)

    # 将 dxf 曲线转换为 3 维坐标并平移到新坐标系原点
    fixed_curve_points = np.hstack((curve_points, np.zeros((curve_points.shape[0], 1))))
    fixed_curve_points = fixed_curve_points - new_origin

    # 提取 x 负向和正向部分
    fixed_curve_points_right = libs.sort_points(fixed_curve_points[fixed_curve_points[:, 0] <= 0], mode='desc')
    fixed_curve_points_left = libs.sort_points(fixed_curve_points[fixed_curve_points[:, 0] >= 0], mode='asc')

    # 计算曲线点的法线
    normals = libs.compute_normals(curve_points)

    # ********************************

    # 选择旋转的基准点，这里选择曲线的中点
    pivot = np.array([0, 0])

    # 旋转点和法线
    rotated_points, rotated_normals = libs.rotate_points_and_normals(curve_points, normals, angle, pivot)

    # 找到与指定直线相交的点
    line_point = new_origin  # 新坐标系中直线的一点
    line_direction = u  # 新坐标系中直线的方向

    # 自动计算 turn_distance
    turn_distance = work_lead / 360

    helix_surface_points_right, helix_surface_normals_right, point_indices_right = libs.generate_helix_surface(rotated_points, rotated_normals, num_turns, turn_angle, turn_distance)
    helix_surface_points_left, helix_surface_normals_left, point_indices_left = libs.generate_helix_surface(rotated_points, rotated_normals, num_turns, -1 * turn_angle, turn_distance)

    # ********************************

    # 计算螺旋曲面上每条曲线上的点的法线是否与新坐标系上的直线相交
    # 5度范围都没找到相交点则不继续找
    helix_intersecting_points_right = libs.find_intersecting_points(helix_surface_points_right, helix_surface_normals_right, line_point, line_direction, min_distance, break_num=num_curve_points * 500)
    helix_intersecting_points_left = libs.find_intersecting_points(helix_surface_points_left, helix_surface_normals_left, line_point, line_direction, min_distance, break_num=num_curve_points * 500)

    # 将 helix_intersecting_points 转换到新坐标系中
    helix_intersecting_points_translated_right = helix_intersecting_points_right - new_origin
    helix_intersecting_points_new_coordinate_system_right = helix_intersecting_points_translated_right @ transformation_matrix
    helix_intersecting_points_translated_left = helix_intersecting_points_left - new_origin
    helix_intersecting_points_new_coordinate_system_left = helix_intersecting_points_translated_left @ transformation_matrix

    # 将 helix_intersecting_points 转换到新坐标系的 xy 平面
    helix_intersecting_points_2d_right = libs.rotate_to_xy_plane(helix_intersecting_points_new_coordinate_system_right)
    helix_intersecting_points_2d_left = libs.rotate_to_xy_plane(helix_intersecting_points_new_coordinate_system_left)

    # 不按照 x 排序  按照原始点的顺序处理点
    # helix_intersecting_points_2d_right = libs.sort_points(helix_intersecting_points_2d_right, positive=False)
    # helix_intersecting_points_2d_left = libs.sort_points(helix_intersecting_points_2d_left, positive=True)

    # ********************************

    # 右侧点 查找第一个 x 和 y 坐标都大于前一个点的点的索引 不检测前10个点 防止误判
    delete_index_right = None
    for i in range(10, len(helix_intersecting_points_2d_right)-1):
        if helix_intersecting_points_2d_right[i, 0] > helix_intersecting_points_2d_right[i-1, 0] and helix_intersecting_points_2d_right[i, 1] > helix_intersecting_points_2d_right[i-1, 1] and helix_intersecting_points_2d_right[i+1, 0] > helix_intersecting_points_2d_right[i, 0] and helix_intersecting_points_2d_right[i+1, 1] > helix_intersecting_points_2d_right[i, 1]:
            delete_index_right = i
            break

    tangent_anomalies_index_right = None

    # 如果找到这样的点
    if delete_index_right is not None:
        # 标注该点及后续所有点在 helix_intersecting_points 中的曲面位置
        anomalous_points_right = helix_intersecting_points_right[delete_index_right:]
        
        # 删除该点及后续所有点
        helix_intersecting_points_2d_right = helix_intersecting_points_2d_right[:delete_index_right]

        # 找到不正常点在原始曲线中的位置
        point_to_find = helix_intersecting_points_right[delete_index_right]
        helix_index = np.where((helix_surface_points_right == point_to_find).all(axis=1))[0][0]
        original_point_index_right, turn_index_right = point_indices_right[helix_index]

        # # 原始曲线中的位置标注
        original_points_abnormal_right = fixed_curve_points_right[original_point_index_right - len(fixed_curve_points_right):]

        # # 第一个不符合条件的点在原始曲线中的切线斜率
        tangent_anomalies_index_right = libs.calculate_tangent(fixed_curve_points_right, original_point_index_right - len(fixed_curve_points_right))
        anomalies_ang_right = 90 - np.degrees(np.tan(tangent_anomalies_index_right[0] / tangent_anomalies_index_right[1]))

    # 左侧点 查找第一个 x 坐标小于前一个点 和 y 坐标大于前一个点的点的索引  不检测前10个点 防止误判
    delete_index_left = None
    for i in range(10, len(helix_intersecting_points_2d_left)-1):
        if helix_intersecting_points_2d_left[i, 0] < helix_intersecting_points_2d_left[i-1, 0] and helix_intersecting_points_2d_left[i, 1] > helix_intersecting_points_2d_left[i-1, 1] and helix_intersecting_points_2d_left[i+1, 0] < helix_intersecting_points_2d_left[i, 0] and helix_intersecting_points_2d_left[i+1, 1] > helix_intersecting_points_2d_left[i, 1]:
            delete_index_left = i
            break

    tangent_anomalies_index_left = None

    if delete_index_left is not None:
        # 标注该点及后续所有点在 helix_intersecting_points 中的曲面位置
        anomalous_points_left = helix_intersecting_points_left[delete_index_left:]
        
        # 删除该点及后续所有点
        helix_intersecting_points_2d_left = helix_intersecting_points_2d_left[:delete_index_left]

        # 找到不正常点在原始曲线中的位置
        point_to_find = helix_intersecting_points_left[delete_index_left]
        helix_index = np.where((helix_surface_points_left == point_to_find).all(axis=1))[0][0]
        original_point_index_left, turn_index_left = point_indices_left[helix_index]

        # 原始曲线中的位置标注
        original_points_abnormal_left = fixed_curve_points_left[original_point_index_left:]

        # 第一个不符合条件的点在原始曲线中的切线斜率
        tangent_anomalies_index_left = libs.calculate_tangent(fixed_curve_points_left, original_point_index_left)
        anomalies_ang_left = 90 + np.degrees(np.tan(tangent_anomalies_index_left[0] / tangent_anomalies_index_left[1]))

    # ********************************

    # 去掉 helix_intersecting_points_2d 右侧 中 x 坐标大于 0 的点 和 左侧 中 x 坐标小于 0 的点
    helix_intersecting_points_2d_filtered_right = helix_intersecting_points_2d_right[helix_intersecting_points_2d_right[:, 0] <= 0]
    helix_intersecting_points_2d_filtered_left = helix_intersecting_points_2d_left[helix_intersecting_points_2d_left[:, 0] >= 0]

    # 将 helix_intersecting_points_2d_filtered 右侧反向排序
    helix_intersecting_points_2d_filtered_right= helix_intersecting_points_2d_filtered_right[::-1]

    # 合并点
    helix_intersecting_points_2d_combined = np.vstack((helix_intersecting_points_2d_filtered_right, helix_intersecting_points_2d_filtered_left))

    # 将 helix_intersecting_points_2d_combined 处理成平滑曲线上的点，点间距与原图形一致
    helix_intersecting_points_2d_smoothed = libs.smooth_curve(helix_intersecting_points_2d_combined, segment_length)

    # 拆分成大于0 和 小于0 两部分
    helix_intersecting_points_2d_smoothed_right, helix_intersecting_points_2d_smoothed_left = libs.split_and_sort_points(helix_intersecting_points_2d_smoothed)
    # ********************************

    # 找出 helix_intersecting_points_2d 中 右侧 x 坐标大于 0 的点 和 左侧 x 坐标小于 0 的点
    # 如果安装角和螺旋升角很接近 可能某一侧的相交点覆盖整个干涉曲线 而不是只有x轴一侧的相交点
    helix_intersecting_points_2d_over_right = helix_intersecting_points_2d_right[helix_intersecting_points_2d_right[:, 0] > 0]
    helix_intersecting_points_2d_over_left = helix_intersecting_points_2d_left[helix_intersecting_points_2d_left[:, 0] < 0]
    helix_intersecting_points_2d_over_combined = np.vstack((helix_intersecting_points_2d_over_right, helix_intersecting_points_2d_over_left))

    # ********************************

    # 标注 helix_intersecting_points_2d_smoothed 中 x 坐标小于上一个点的点
    anomalies_smoothed = np.empty((0, 2))

    # 当 x 坐标小于 0 时，找到不符合条件的前一个点
    for i in range(1, len(helix_intersecting_points_2d_smoothed_right) - 1):
        if helix_intersecting_points_2d_smoothed_right[i, 0] < 0:
            if helix_intersecting_points_2d_smoothed_right[i - 1, 0] < helix_intersecting_points_2d_smoothed_right[i, 0] < helix_intersecting_points_2d_smoothed_right[i + 1, 0]:
                anomalies_smoothed = np.vstack((anomalies_smoothed, helix_intersecting_points_2d_smoothed_right[i-1], helix_intersecting_points_2d_smoothed_right[i]))

    for i in range(10, len(helix_intersecting_points_2d_smoothed_right) - 1):
        if helix_intersecting_points_2d_smoothed_right[i, 0] < 0:
            if helix_intersecting_points_2d_smoothed_right[i - 1, 1] < helix_intersecting_points_2d_smoothed_right[i, 1] < helix_intersecting_points_2d_smoothed_right[i + 1, 1]:
                anomalies_smoothed = np.vstack((anomalies_smoothed, helix_intersecting_points_2d_smoothed_right[i-1], helix_intersecting_points_2d_smoothed_right[i]))

    # 当 x 坐标大于 0 时，找到不符合条件的后一个点
    for i in range(1, len(helix_intersecting_points_2d_smoothed_left) - 1):
        if helix_intersecting_points_2d_smoothed_left[i, 0] > 0:
            if helix_intersecting_points_2d_smoothed_left[i - 1, 0] > helix_intersecting_points_2d_smoothed_left[i, 0] > helix_intersecting_points_2d_smoothed_left[i + 1, 0]:
                anomalies_smoothed = np.vstack((anomalies_smoothed, helix_intersecting_points_2d_smoothed_left[i-1], helix_intersecting_points_2d_smoothed_left[i]))

    for i in range(10,len(helix_intersecting_points_2d_smoothed_left) - 1):
        if helix_intersecting_points_2d_smoothed_left[i, 0] > 0:
            if helix_intersecting_points_2d_smoothed_left[i - 1, 1] < helix_intersecting_points_2d_smoothed_left[i, 1] < helix_intersecting_points_2d_smoothed_left[i + 1, 1]:
                anomalies_smoothed = np.vstack((anomalies_smoothed, helix_intersecting_points_2d_smoothed_left[i-1], helix_intersecting_points_2d_smoothed_left[i]))

    anomalies_smoothed = np.array(anomalies_smoothed)

    # 如果反向弯折的点过多则报错
    # if len(anomalies_smoothed) / 2 > 5000:
    #     print(f"干涉曲线齿根反向弯折的点过多:{len(anomalies_smoothed) / 2},需要加大砂轮安装角或加大砂轮杆偏移工件中心距离")
    #     sys.exit()

    # 删掉反折点
    helix_intersecting_points_2d_smoothed = libs.remove_points(helix_intersecting_points_2d_smoothed, anomalies_smoothed)
    # ********************************

    # 获取 helix_intersecting_points_2d_smoothed 中 y 坐标最大点
    max_y_index_smoothed = np.argmax(helix_intersecting_points_2d_smoothed[:, 1])
    max_y_point_smoothed = helix_intersecting_points_2d_smoothed[max_y_index_smoothed]

    # 砂轮直径
    wheel_dia = max_y_point_smoothed[1] * 2

    # ********************************

    # 找到 x 轴坐标最接近 0 的一点
    x_zero_index = libs.find_closest_point_to_zero(helix_intersecting_points_2d_smoothed)
    reference_origin = helix_intersecting_points_2d_smoothed[x_zero_index]

    # 数组值传递给 helix_intersecting_points_2d_translated 不能直接赋值 否则后续计算会影响原数组
    helix_intersecting_points_2d_translated = helix_intersecting_points_2d_smoothed - 0

    # 平移所有点的 y 坐标到指定点为原点
    helix_intersecting_points_2d_translated[:, 1] += - reference_origin[1] - dresser_r

    # 处理 helix_intersecting_points_2d_translated 使其等距
    helix_intersecting_points_2d_translated = libs.redistribute_points_equally(helix_intersecting_points_2d_translated, num_curve_points)

    # 如果 y坐标 有大于 指定值 的点 则修改其 y 为指定值
    helix_intersecting_points_2d_translated = libs.limit_y_coordinate(helix_intersecting_points_2d_translated, -dresser_r)

    # 修整轮廓线
    helix_intersecting_points_2d_translated_contour = libs.generate_contour_points(helix_intersecting_points_2d_translated, contour_distance=dresser_r, point_spacing=segment_length)

    # 处理 helix_intersecting_points_2d_translated_contour 使其等距
    helix_intersecting_points_2d_translated_contour = libs.redistribute_points_equally(helix_intersecting_points_2d_translated_contour, shape_num)

    # 如果 y坐标 有大于 0 的点 则修改其 y 为 0
    helix_intersecting_points_2d_translated_contour = libs.limit_y_coordinate(helix_intersecting_points_2d_translated_contour, 0)

    # ********************************

    # 将所有点坐标放入字符串中，每行按照 'x 空格 y' 的模式
    point_string = "\n".join([f"{x} {y}" for x, y in helix_intersecting_points_2d_translated_contour])

    # 获取最高点
    max_y_index = np.argmax(helix_intersecting_points_2d_translated[:, 1])
    min_y_index = np.argmin(helix_intersecting_points_2d_translated[:, 1])
    max_y_point = helix_intersecting_points_2d_translated[max_y_index]
    min_y_point = helix_intersecting_points_2d_translated[min_y_index]
    max_x_index = np.argmax(helix_intersecting_points_2d_translated[:, 0])
    min_x_index = np.argmin(helix_intersecting_points_2d_translated[:, 0])
    max_x_point = helix_intersecting_points_2d_translated[max_x_index]
    min_x_point = helix_intersecting_points_2d_translated[min_x_index]

    # 计算高度差
    height_difference = max_y_point[1] - min_y_point[1]
    # 计算齿宽
    width_max = max_x_point[0] - min_x_point[0]

    # 获取滚轮修整最高点
    max_y_index_contour = np.argmax(helix_intersecting_points_2d_translated_contour[:, 1])
    min_y_index_contour = np.argmin(helix_intersecting_points_2d_translated_contour[:, 1])
    max_y_point_contour = helix_intersecting_points_2d_translated_contour[max_y_index_contour]
    min_y_point_contour = helix_intersecting_points_2d_translated_contour[min_y_index_contour]
    max_x_index_contour = np.argmax(helix_intersecting_points_2d_translated_contour[:, 0])
    min_x_index_contour = np.argmin(helix_intersecting_points_2d_translated_contour[:, 0])
    max_x_point_contour = helix_intersecting_points_2d_translated_contour[max_x_index_contour]
    min_x_point_contour = helix_intersecting_points_2d_translated_contour[min_x_index_contour]

    # 计算修整高度差
    height_difference_contour = max_y_point_contour[1] - min_y_point_contour[1]
    # 计算修整齿宽
    width_max_contour = max_x_point_contour[0] - min_x_point_contour[0]

    # 最高点的前一个点的切线与垂直向下方向的夹角
    if max_y_index > 0:
        tangent_before_max = libs.calculate_tangent(helix_intersecting_points_2d_translated_contour, max_y_index_contour - 1)
        angle_before_max = libs.calculate_angle(-1 * tangent_before_max)
    else:
        angle_before_max = None

    # 最高点的后一个点的切线与垂直向下方向的夹角
    if max_y_index < len(helix_intersecting_points_2d_translated_contour) - 1:
        tangent_after_max = libs.calculate_tangent(helix_intersecting_points_2d_translated_contour, max_y_index_contour + 1)
        angle_after_max = libs.calculate_angle(tangent_after_max)
    else:
        angle_after_max = None

    # 第二个点的切线与垂直向下方向的夹角
    if len(helix_intersecting_points_2d_translated_contour) > 1:
        tangent_second = libs.calculate_tangent(helix_intersecting_points_2d_translated_contour, 1)
        angle_second = libs.calculate_angle(-1 * tangent_second)
    else:
        angle_second = None

    # 倒数第二个点的切线与垂直向下方向的夹角
    if len(helix_intersecting_points_2d_translated_contour) > 1:
        tangent_penultimate = libs.calculate_tangent(helix_intersecting_points_2d_translated_contour, len(helix_intersecting_points_2d_translated_contour) - 2)
        angle_penultimate = libs.calculate_angle(tangent_penultimate)
    else:
        angle_penultimate = None

    # 获取第一个点和最后一个点的坐标
    first_point = helix_intersecting_points_2d_translated_contour[0]
    last_point = helix_intersecting_points_2d_translated_contour[-1]

    # ********************************

    # 拆分成两个数组
    right_points = helix_intersecting_points_2d_translated_contour[helix_intersecting_points_2d_translated_contour[:, 0] < 0]
    left_points = helix_intersecting_points_2d_translated_contour[helix_intersecting_points_2d_translated_contour[:, 0] >= 0]

    # x 坐标小于0的点反向排序
    right_points = right_points[::-1]

    # 左右两边第一个点都为 0,0
    right_points = np.vstack((np.array([[0, 0]]), right_points))
    left_points = np.vstack((np.array([[0, 0]]), left_points))

    # 将直径转换为4位小数的字符串
    wheel_dia_str = f"{wheel_dia:.4f}"

    # 将小数点替换为下划线
    wheel_dia_str = wheel_dia_str.replace('.', '_')

    # 准备写入文件的内容
    file_content = f"""
    ;********************************
    DIA_{wheel_dia_str}:
    IF DRESSER[40]==1;
    ;*********************************************
    DRESSER[41]=90;外部齿形程序右起点角度(竖直向下夹角)
    DRESSER[42]=90;外部齿形程序左起点角度(竖直向下夹角)
    DRESSER[43]=0;外部齿形程序顶部平台长度(预留参数)
    DRESSER[45]=0;齿形右终点角度(竖直向下夹角)
    DRESSER[46]=0;齿形左终点角度(竖直向下夹角)
    DRESSER[51]={first_point[0]:.4f};外部齿形程序右终点水平坐标
    DRESSER[131]={-1 * first_point[1]:.4f};外部齿形程序右终点垂直坐标(考虑VER_MODE)
    DRESSER[115]={last_point[0]:.4f};外部齿形程序左终点水平坐标
    DRESSER[138]={-1 * last_point[1]:.4f};外部齿形程序左终点垂直坐标(考虑VER_MODE)
    DRESSER[99]=1.900000
    ;***********************************************
    RET
    ENDIF
    ;齿形部分
    CASE DRESSER[44] OF 0 GOTOF RIGHT_SIDE 1 GOTOF LEFT_SIDE DEFAULT GOTOF RIGHT_SIDE
    ;右侧齿形
    RIGHT_SIDE:
    G64 G90 G01
    """

    # 添加右侧点位坐标
    for point in right_points:
        file_content += f"AX[AX_VER]={-1 * point[1]:.4f}*VER_MODE   AX[AX_HORI]={point[0]:.4f}\n"

    file_content += "RET\n;左侧齿形\nLEFT_SIDE:\nG64 G90 G01\n"

    # 添加左侧点位坐标
    for point in left_points:
        file_content += f"AX[AX_VER]={-1 * point[1]:.4f}*VER_MODE   AX[AX_HORI]={point[0]:.4f}\n"

    file_content += "RET\n"

    # ********************************

    if if_plot:
        # 设置中文字体
        current_os = platform.system()
        if current_os == 'Windows':
            font_family = 'SimHei'
        elif current_os == 'Darwin':  # macOS
            font_family = 'Heiti TC'
        else:
            font_family = 'Noto Sans CJK JP'
        
        # 创建第一个子图
        fig = go.Figure()

        # 标准齿形轨迹点
        fig.add_trace(go.Scatter(x=curve_points[:, 0], y=curve_points[:, 1], mode='markers', 
                                marker=dict(color='blue', size=5), name='标准齿形轨迹点'))
        
        # 统一比例尺
        fig.update_layout(
            xaxis=dict(scaleanchor="y", scaleratio=1),
            yaxis=dict(scaleanchor="x", scaleratio=1),
            title='标准齿形轨迹点'
        )

        # 创建第二个子图（3D），使用采样来减少点的数量
        def sample_data(data, sample_rate):
            num_points = data.shape[0]
            sample_size = max(1, int(num_points * sample_rate))
            sampled_indices = np.random.choice(num_points, size=sample_size, replace=False)
            return data[sampled_indices]

        sample_rate = 0.005  # 采样率

        sampled_helix_surface_points_right = sample_data(helix_surface_points_right, sample_rate)
        sampled_helix_surface_points_left = sample_data(helix_surface_points_left, sample_rate)
        sampled_helix_intersecting_points_right = sample_data(helix_intersecting_points_right, 1)
        sampled_helix_intersecting_points_left = sample_data(helix_intersecting_points_left, 1)

        fig_3d = go.Figure()

        fig_3d.add_trace(go.Scatter3d(x=sampled_helix_surface_points_right[:, 0], 
                                      y=sampled_helix_surface_points_right[:, 1], 
                                      z=sampled_helix_surface_points_right[:, 2], 
                                      mode='lines', name='右侧螺旋曲面'))
        fig_3d.add_trace(go.Scatter3d(x=sampled_helix_surface_points_left[:, 0], 
                                      y=sampled_helix_surface_points_left[:, 1], 
                                      z=sampled_helix_surface_points_left[:, 2], 
                                      mode='lines', name='左侧螺旋曲面'))
        fig_3d.add_trace(go.Scatter3d(x=sampled_helix_intersecting_points_right[:, 0], 
                                      y=sampled_helix_intersecting_points_right[:, 1], 
                                      z=sampled_helix_intersecting_points_right[:, 2], 
                                      mode='markers', marker=dict(color='#93cd00', size=3), name='右侧砂轮接触点'))
        fig_3d.add_trace(go.Scatter3d(x=sampled_helix_intersecting_points_left[:, 0], 
                                      y=sampled_helix_intersecting_points_left[:, 1], 
                                      z=sampled_helix_intersecting_points_left[:, 2], 
                                      mode='markers', marker=dict(color='#d6c400', size=3), name='左侧砂轮接触点'))

        if delete_index_right is not None:
            fig_3d.add_trace(go.Scatter3d(x=anomalous_points_right[:, 0], y=anomalous_points_right[:, 1], z=anomalous_points_right[:, 2], 
                                          mode='markers', marker=dict(color='#cd0000', size=4), name='右侧异常接触点'))
        if delete_index_left is not None:
            fig_3d.add_trace(go.Scatter3d(x=anomalous_points_left[:, 0], y=anomalous_points_left[:, 1], z=anomalous_points_left[:, 2], 
                                          mode='markers', marker=dict(color='#cd6700', size=4), name='左侧异常接触点'))

        # 创建第三个子图
        fig_2d = go.Figure()

        fig_2d.add_trace(go.Scatter(x=fixed_curve_points[:, 0], y=fixed_curve_points[:, 1], 
                                    mode='markers', marker=dict(color='blue', size=2), name='标准齿形轨迹点'))
        if len(helix_intersecting_points_2d_smoothed) > 0:
            fig_2d.add_trace(go.Scatter(x=helix_intersecting_points_2d_smoothed[:, 0], y=helix_intersecting_points_2d_smoothed[:, 1], 
                                        mode='markers', marker=dict(color='red', size=2), name='干涉砂轮齿形轨迹点'))

        if len(anomalies_smoothed) > 0:
            fig_2d.add_trace(go.Scatter(x=anomalies_smoothed[:, 0], y=anomalies_smoothed[:, 1], 
                                        mode='markers', marker=dict(color='#1ae621', size=6), name='齿底异常点'))
        if len(helix_intersecting_points_2d_over_right) > 0:
            fig_2d.add_trace(go.Scatter(x=helix_intersecting_points_2d_over_right[:, 0], y=helix_intersecting_points_2d_over_right[:, 1], 
                                        mode='markers', marker=dict(color='#1f5793', size=6), name='右侧齿顶异常点'))
        if len(helix_intersecting_points_2d_over_left) > 0:
            fig_2d.add_trace(go.Scatter(x=helix_intersecting_points_2d_over_left[:, 0], y=helix_intersecting_points_2d_over_left[:, 1], 
                                        mode='markers', marker=dict(color='#2cb5ff', size=6), name='左侧齿顶异常点'))

        if delete_index_right is not None:
            fig_2d.add_trace(go.Scatter(x=original_points_abnormal_right[:, 0], y=original_points_abnormal_right[:, 1], 
                                        mode='markers', marker=dict(color='green', size=4), 
                                        name=f'异常点在原始轨道的右侧位置 (螺旋圈数: {turn_index_right}, 点位号: {original_point_index_right - len(fixed_curve_points_right)})'))
        if delete_index_left is not None:
            fig_2d.add_trace(go.Scatter(x=original_points_abnormal_left[:, 0], y=original_points_abnormal_left[:, 1], 
                                        mode='markers', marker=dict(color='green', size=4), 
                                        name=f'异常点在原始轨道的左侧位置 (螺旋圈数: {turn_index_left}, 点位号: {original_point_index_left})'))

        if tangent_anomalies_index_right is not None:
            fig_2d.add_trace(go.Scatter(x=[original_points_abnormal_right[0, 0]], y=[original_points_abnormal_right[0, 1]], 
                                        mode='markers+text', text=[f'右侧第一个异常点的切线斜率: {anomalies_ang_right:.4f}'], 
                                        marker=dict(color='#e80505', size=8), name='右侧第一个异常点'))
        if tangent_anomalies_index_left is not None:
            fig_2d.add_trace(go.Scatter(x=[original_points_abnormal_left[0, 0]], y=[original_points_abnormal_left[0, 1]], 
                                        mode='markers+text', text=[f'左侧第一个异常点的切线斜率: {anomalies_ang_left:.4f}'], 
                                        marker=dict(color='#d406a4', size=8), name='左侧第一个异常点'))
        
        fig_2d.update_layout(
            xaxis=dict(scaleanchor="y", scaleratio=1),
            yaxis=dict(scaleanchor="x", scaleratio=1),
            title='原始轨迹与干涉轨迹对比'
        )

        # 创建第四个子图
        fig_translated = go.Figure()

        fig_translated.add_trace(go.Scatter(x=helix_intersecting_points_2d_translated[:, 0], y=helix_intersecting_points_2d_translated[:, 1], 
                                            mode='markers', marker=dict(color='red', size=2), name='优化后的干涉轨迹点'))
        fig_translated.add_trace(go.Scatter(x=helix_intersecting_points_2d_translated_contour[:, 0], y=helix_intersecting_points_2d_translated_contour[:, 1], 
                                            mode='markers', marker=dict(color='blue', size=2), name='滚轮修整轮廓点'))

        fig_translated.update_layout(
            xaxis=dict(scaleanchor="y", scaleratio=1),
            yaxis=dict(scaleanchor="x", scaleratio=1),
            title='最终干涉轨迹'
        )

        # 保存图表到 HTML 文件
        fig.write_html(f"{save_path}/plot_curve_original.html")
        fig_3d.write_html(f"{save_path}/plot_helix_surface_intersecting_points.html")
        fig_2d.write_html(f"{save_path}/plot_intersecting_points_compare_with_original.html")
        fig_translated.write_html(f"{save_path}/plot_contour_curve.html")

    return wheel_dia, file_content, point_string
