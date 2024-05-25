import numpy as np
import matplotlib.pyplot as plt
import ezdxf
from scipy.interpolate import make_interp_spline
import sys
import platform

# 砂轮杆偏移工件中心距离
gan_distance = 18

# 砂轮安装角
gan_angle = 5

# 工件中径
mid_dia = 45

# 导程
work_lead = 45

# 螺旋升角
angle = np.rad2deg(np.arctan2(work_lead, np.pi * mid_dia))
print(f'标准螺旋升角: {angle}')

# dxf 曲线离散点个数
segment_length = 0.01

# 螺旋曲面绘制次数
num_turns = 4500
# 每个曲面移动角度
turn_angle = 0.01

# 判断法线是否相交的最小距离
min_distance = 0.001

# ********************************

# 定义一个函数，从 DXF 文件中加载曲线，并仅保留 XY 坐标，同时应用偏移和等距离散化
def load_dxf_curve(filename, offset=np.array([0, 30]), segment_length=0.01):
    doc = ezdxf.readfile(filename)  # 读取 DXF 文件
    msp = doc.modelspace()  # 获取模型空间
    points = []

    # 定义一个辅助函数，添加等距离散化的线段点
    def add_line_points(start, end, segment_length):
        distance = np.linalg.norm(end - start)  # 计算线段长度
        num_points = int(np.ceil(distance / segment_length))  # 计算需要的点数
        line_points = np.linspace(start, end, num_points)  # 等距生成离散点
        points.extend(line_points)  # 将点添加到列表中

    for entity in msp:
        if entity.dxftype() == 'LWPOLYLINE':
            # 处理轻量级多段线实体
            for i in range(len(entity) - 1):
                start = np.array([entity[i][0], entity[i][1]]) + offset
                end = np.array([entity[i + 1][0], entity[i + 1][1]]) + offset
                add_line_points(start, end, segment_length)
        elif entity.dxftype() == 'LINE':
            # 处理直线实体
            start = np.array([entity.dxf.start.x, entity.dxf.start.y]) + offset
            end = np.array([entity.dxf.end.x, entity.dxf.end.y]) + offset
            add_line_points(start, end, segment_length)
        elif entity.dxftype() == 'ARC':
            # 处理圆弧实体
            center = np.array([entity.dxf.center.x, entity.dxf.center.y]) + offset
            radius = entity.dxf.radius
            start_angle = np.radians(entity.dxf.start_angle)
            end_angle = np.radians(entity.dxf.end_angle)
            arc_length = radius * abs(end_angle - start_angle)  # 计算圆弧长度
            num_points = int(np.ceil(arc_length / segment_length))  # 计算需要的点数
            theta = np.linspace(start_angle, end_angle, num_points)  # 等距生成角度
            arc_points = np.vstack((center[0] + radius * np.cos(theta), center[1] + radius * np.sin(theta))).T
            points.extend(arc_points)  # 将圆弧点添加到列表中
    return np.array(points)

# 定义一个函数，计算一组点的法线向量
def compute_normals(points):
    normals = []
    for i in range(len(points)):
        if i == 0:
            tangent = points[i + 1] - points[i]
        elif i == len(points) - 1:
            tangent = points[i] - points[i - 1]
        else:
            tangent = points[i + 1] - points[i - 1]
        normal = np.array([-tangent[1], tangent[0]])  # 计算法线向量
        normal = normal / np.linalg.norm(normal)  # 归一化法线向量
        normals.append(normal)
    return np.array(normals)

# 定义绕 y 轴旋转的旋转矩阵
def rotation_matrix_y(alpha):
    return np.array([
        [np.cos(alpha), 0, np.sin(alpha)],
        [0, 1, 0],
        [-np.sin(alpha), 0, np.cos(alpha)]
    ])

# 定义一个函数，绕某个轴旋转点和法线
def rotate_points_and_normals(points, normals, angle, pivot=np.array([0, 0])):
    translated_points = points - pivot  # 平移点到原点
    points_3d = np.hstack((translated_points, np.zeros((translated_points.shape[0], 1))))  # 添加 z 轴坐标
    normals_3d = np.hstack((normals, np.zeros((normals.shape[0], 1))))  # 添加 z 轴坐标
    R = rotation_matrix_y(np.radians(angle))  # 计算旋转矩阵
    rotated_points = points_3d @ R.T  # 旋转点
    rotated_normals = normals_3d @ R.T  # 旋转法线
    rotated_points[:, :2] += pivot  # 平移回原位置
    return rotated_points, rotated_normals

# 计算两条直线之间的最短距离
def line_to_line_distance(p1, d1, p2, d2):
    cross_prod = np.cross(d1, d2)
    norm_cross_prod = np.linalg.norm(cross_prod)
    if norm_cross_prod == 0:  # 处理平行的情况
        return np.linalg.norm(np.cross(d1, (p2 - p1))) / np.linalg.norm(d1)
    else:
        return np.abs(np.dot(cross_prod, (p2 - p1))) / norm_cross_prod

# 计算与指定直线相交的点
def find_intersecting_points(points, normals, line_point, line_direction, min_distance=0.001):
    intersecting_points = []
    for i in range(len(points)):
        normal_line_point = points[i]
        normal_line_direction = normals[i]
        distance = line_to_line_distance(normal_line_point, normal_line_direction, line_point, line_direction)
        if distance < min_distance:
            intersecting_points.append(points[i])
    if len(intersecting_points) == 0:
        return np.empty((0, 3))  # 返回一个空的二维数组
    return np.array(intersecting_points)

# 定义绕 x 轴旋转和平移的函数，生成螺旋曲面上的点和法线
def generate_helix_surface(points, normals, num_turns=2000, turn_angle=0.01, turn_distance=None):
    if turn_distance is None:
        raise ValueError("turn_distance must be provided or calculated before calling generate_helix_surface.")
    surface_points = []
    surface_normals = []
    point_indices = []  # 用于存储每个点的来源索引
    for i in range(num_turns):
        angle = turn_angle * i
        distance = turn_distance * angle
        R = np.array([
            [1, 0, 0],
            [0, np.cos(np.radians(angle)), -np.sin(np.radians(angle))],
            [0, np.sin(np.radians(angle)), np.cos(np.radians(angle))]
        ])
        rotated_points = (points @ R.T) + np.array([distance, 0, 0])
        rotated_normals = (normals @ R.T) + np.array([distance, 0, 0])
        surface_points.append(rotated_points)
        surface_normals.append(rotated_normals)
        point_indices.extend([(j, i) for j in range(len(points))])  # 追踪点的来源
    return np.vstack(surface_points), np.vstack(surface_normals), point_indices

# 生成平滑曲线上的点
def smooth_curve(points, num_points):
    try:
        x = points[:, 0]
        y = points[:, 1]
        
        # 使用 make_interp_spline 生成 Bézier 曲线
        spline_x = make_interp_spline(np.arange(len(x)), x, k=2)  # k=2 生成二次 Bézier 曲线
        spline_y = make_interp_spline(np.arange(len(y)), y, k=2)
        
        u_new = np.linspace(0, len(x) - 1, num_points)
        x_new = spline_x(u_new)
        y_new = spline_y(u_new)
        
        # 确保平滑曲线上的点单调过渡
        for i in range(1, len(x_new) - 1):
            if not (x_new[i-1] <= x_new[i] <= x_new[i+1] or x_new[i-1] >= x_new[i] >= x_new[i+1]):
                x_new[i] = (x_new[i-1] + x_new[i+1]) / 2
            if not (y_new[i-1] <= y_new[i] <= y_new[i+1] or y_new[i-1] >= y_new[i] >= y_new[i+1]):
                y_new[i] = (y_new[i-1] + y_new[i+1]) / 2

        return np.vstack((x_new, y_new)).T
    except Exception as e:
        print(f"Error: 曲线不存在")
        sys.exit(1)

# 定义一个函数，将点旋转到新坐标系的 xy 平面
def rotate_to_xy_plane(points):
    if len(points) == 0:
        return np.empty((0, 2))  # 返回一个空的二维数组
    projected_points = []
    for point in points:
        # 计算绕 x 轴旋转的角度
        theta = np.arctan2(point[2], point[1])
        # 绕 x 轴的旋转矩阵
        rotation_matrix = np.array([
            [1, 0, 0],
            [0, np.cos(theta), np.sin(theta)],
            [0, -np.sin(theta), np.cos(theta)]
        ])
        # 旋转并投影到 xy 平面
        rotated_point = rotation_matrix @ point
        projected_point = rotated_point[:2]
        projected_points.append(projected_point)
    return np.array(projected_points)

# 将所有点等距处理 最高点设置为 0,0
def redistribute_points_equally(points, num_points):
    # 找到 Y 轴最高的点，并将其坐标设为 (0,0)
    max_y_index = np.argmax(points[:, 1])
    max_y_point = points[max_y_index]
    translated_points = points - max_y_point

    # 计算每个点到最高点的累积距离
    distances = np.sqrt(np.sum(np.diff(translated_points, axis=0)**2, axis=1))
    cumulative_distances = np.insert(np.cumsum(distances), 0, 0)

    # 生成等距点
    equal_distances = np.linspace(0, cumulative_distances[-1], num_points)

    # 线性插值生成等距点
    x_interp = np.interp(equal_distances, cumulative_distances, translated_points[:, 0])
    y_interp = np.interp(equal_distances, cumulative_distances, translated_points[:, 1])

    equal_points = np.vstack((x_interp, y_interp)).T
    return equal_points

# 计算某一点在曲线上的切线
def calculate_tangent(points, index, window=3):
    """
    计算指定点的切线向量。
    参数:
    - points: 点的数组
    - index: 指定点的索引
    - window: 用于计算切线的窗口大小
    
    返回:
    - 切线向量
    """
    half_window = window // 2
    start = max(index - half_window, 0)
    end = min(index + half_window + 1, len(points))
    x = points[start:end, 0]
    y = points[start:end, 1]
    
    # 多项式拟合
    coeffs = np.polyfit(x, y, 1)
    tangent = np.array([1, coeffs[0]])  # [dx, dy]
    tangent /= np.linalg.norm(tangent)  # 归一化
    return tangent

# 计算切线与垂直方向的夹角
def calculate_angle(tangent, vertical=np.array([0, -1])):
    """
    计算切线与垂直方向的夹角。
    参数:
    - tangent: 切线向量
    - vertical: 垂直方向向量
    
    返回:
    - 夹角（弧度）
    """
    dot_product = np.dot(tangent, vertical)
    angle = np.arccos(dot_product)
    return np.degrees(angle)

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
dxf_filename = 'test.dxf'  # DXF 文件名
curve_points = load_dxf_curve(dxf_filename, offset, segment_length)

# 将 dxf 曲线转换为 3 维坐标并平移到新坐标系原点
fixed_curve_points = np.hstack((curve_points, np.zeros((curve_points.shape[0], 1))))
fixed_curve_points = fixed_curve_points - new_origin

# 计算曲线点的法线
normals = compute_normals(curve_points)

# ********************************

# 选择旋转的基准点，这里选择曲线的中点
pivot = np.array([0, 0])

# 旋转点和法线
rotated_points, rotated_normals = rotate_points_and_normals(curve_points, normals, angle, pivot)

# 找到与指定直线相交的点
line_point = new_origin  # 新坐标系中直线的一点
line_direction = u  # 新坐标系中直线的方向

# 自动计算 turn_distance
turn_distance = work_lead / 360

helix_surface_points_right, helix_surface_normals_right, point_indices_right = generate_helix_surface(rotated_points, rotated_normals, num_turns, turn_angle, turn_distance)
helix_surface_points_left, helix_surface_normals_left, point_indices_left = generate_helix_surface(rotated_points, rotated_normals, num_turns, -1 * turn_angle, turn_distance)

# ********************************

# 计算螺旋曲面上每条曲线上的点的法线是否与新坐标系上的直线相交
helix_intersecting_points_right = find_intersecting_points(helix_surface_points_right, helix_surface_normals_right, line_point, line_direction, min_distance)
helix_intersecting_points_left = find_intersecting_points(helix_surface_points_left, helix_surface_normals_left, line_point, line_direction, min_distance)

# 将 helix_intersecting_points 转换到新坐标系中
helix_intersecting_points_translated_right = helix_intersecting_points_right - new_origin
helix_intersecting_points_new_coordinate_system_right = helix_intersecting_points_translated_right @ transformation_matrix
helix_intersecting_points_translated_left = helix_intersecting_points_left - new_origin
helix_intersecting_points_new_coordinate_system_left = helix_intersecting_points_translated_left @ transformation_matrix

# 将 helix_intersecting_points 转换到新坐标系的 xy 平面
helix_intersecting_points_2d_right = rotate_to_xy_plane(helix_intersecting_points_new_coordinate_system_right)
helix_intersecting_points_2d_left = rotate_to_xy_plane(helix_intersecting_points_new_coordinate_system_left)

# ********************************

# 右侧点 查找第一个 x 和 y 坐标都大于前一个点的点的索引
delete_index_right = None
for i in range(1, len(helix_intersecting_points_2d_right)):
    if helix_intersecting_points_2d_right[i, 0] > helix_intersecting_points_2d_right[i-1, 0] and helix_intersecting_points_2d_right[i, 1] > helix_intersecting_points_2d_right[i-1, 1]:
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

    # 原始曲线中的位置标注
    original_points_abnormal_right = fixed_curve_points[original_point_index_right:]

    # 第一个不符合条件的点在原始曲线中的切线斜率
    tangent_anomalies_index_right = calculate_tangent(fixed_curve_points, original_point_index_right)
    anomalies_ang_right = 90 - np.degrees(np.tan(tangent_anomalies_index_right[0] / tangent_anomalies_index_right[1]))

# 左侧点 查找第一个 x 坐标小于前一个点 和 y 坐标大于前一个点的点的索引
delete_index_left = None
for i in range(1, len(helix_intersecting_points_2d_left)):
    if helix_intersecting_points_2d_left[i, 0] < helix_intersecting_points_2d_left[i-1, 0] and helix_intersecting_points_2d_left[i, 1] > helix_intersecting_points_2d_left[i-1, 1]:
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
    original_points_abnormal_left = fixed_curve_points[:original_point_index_left]

    # 第一个不符合条件的点在原始曲线中的切线斜率
    tangent_anomalies_index_left = calculate_tangent(fixed_curve_points, original_point_index_left)
    anomalies_ang_left = 90 + np.degrees(np.tan(tangent_anomalies_index_left[0] / tangent_anomalies_index_left[1]))

# 整合左右的不正常点
if delete_index_right is not None or delete_index_left is not None:
    original_points_abnormal_combined = np.vstack((original_points_abnormal_right, original_points_abnormal_left))

# ********************************

# 去掉 helix_intersecting_points_2d 右侧 中 x 坐标大于 0 的点 和 左侧 中 x 坐标小于 0 的点
helix_intersecting_points_2d_filtered_right = helix_intersecting_points_2d_right[helix_intersecting_points_2d_right[:, 0] <= 0]
helix_intersecting_points_2d_filtered_left = helix_intersecting_points_2d_left[helix_intersecting_points_2d_left[:, 0] >= 0]

# 将 helix_intersecting_points_2d_filtered 右侧反向排序
helix_intersecting_points_2d_filtered_right= helix_intersecting_points_2d_filtered_right[::-1]

# 合并点
helix_intersecting_points_2d_combined = np.vstack((helix_intersecting_points_2d_filtered_right, helix_intersecting_points_2d_filtered_left))

#找出 helix_intersecting_points_2d 中 右侧 x 坐标大于 0 的点 和 左侧 x 坐标小于 0 的点
helix_intersecting_points_2d_over_right = helix_intersecting_points_2d_right[helix_intersecting_points_2d_right[:, 0] > 0]
helix_intersecting_points_2d_over_left = helix_intersecting_points_2d_left[helix_intersecting_points_2d_left[:, 0] < 0]
helix_intersecting_points_2d_over_combined = np.vstack((helix_intersecting_points_2d_over_right, helix_intersecting_points_2d_over_left))

# ********************************

# 获取 curve_points 的点个数
num_curve_points = len(curve_points)

# 将 helix_intersecting_points_2d_combined 处理成平滑曲线上的点，点个数与 curve_points 一致
helix_intersecting_points_2d_smoothed = smooth_curve(helix_intersecting_points_2d_combined, num_curve_points)

# ********************************

# 标注 helix_intersecting_points_2d_smoothed 中 x 坐标小于上一个点的点
anomalies_smoothed = []

# 当 x 坐标小于 0 时，找到不符合条件的前一个点
for i in range(1, len(helix_intersecting_points_2d_smoothed)):
    if helix_intersecting_points_2d_smoothed[i, 0] < 0:
        if helix_intersecting_points_2d_smoothed[i, 0] < helix_intersecting_points_2d_smoothed[i - 1, 0]:
            anomalies_smoothed.append(helix_intersecting_points_2d_smoothed[i - 1])

# 当 x 坐标大于 0 时，找到不符合条件的后一个点
for i in range(len(helix_intersecting_points_2d_smoothed) - 1):
    if helix_intersecting_points_2d_smoothed[i, 0] > 0:
        if helix_intersecting_points_2d_smoothed[i, 0] > helix_intersecting_points_2d_smoothed[i + 1, 0]:
            anomalies_smoothed.append(helix_intersecting_points_2d_smoothed[i + 1])

anomalies_smoothed = np.array(anomalies_smoothed)

# 如果反向弯折的点过多则报错
if len(anomalies_smoothed / 2) > 50:
    print("干涉曲线齿根反向弯折的点过多,需要加大砂轮安装角或加大砂轮杆偏移工件中心距离")
    sys.exit()

# ********************************

# 获取 helix_intersecting_points_2d_smoothed 中 y 坐标最大点
max_y_index_smoothed = np.argmax(helix_intersecting_points_2d_smoothed[:, 1])
max_y_point_smoothed = helix_intersecting_points_2d_smoothed[max_y_index_smoothed]

# 砂轮直径
wheel_dia = max_y_point_smoothed[1] * 2

# ********************************

# 找到 y 轴最大点作为基准原点
max_y_index = np.argmax(helix_intersecting_points_2d_smoothed[:, 1])
reference_origin = helix_intersecting_points_2d_smoothed[max_y_index]

# 平移所有点到新坐标系
helix_intersecting_points_2d_translated = helix_intersecting_points_2d_smoothed - reference_origin

# 处理 helix_intersecting_points_2d_translated 中的点
points_to_delete = []

# 当 x 坐标小于 0 时，删除不符合条件的前一个点
for i in range(1, len(helix_intersecting_points_2d_translated)):
    if helix_intersecting_points_2d_translated[i, 0] < 0:
        if helix_intersecting_points_2d_translated[i, 0] < helix_intersecting_points_2d_translated[i - 1, 0]:
            points_to_delete.append(i - 1)

# 当 x 坐标大于 0 时，删除不符合条件的后一个点
for i in range(len(helix_intersecting_points_2d_translated) - 1):
    if helix_intersecting_points_2d_translated[i, 0] > 0:
        if helix_intersecting_points_2d_translated[i, 0] > helix_intersecting_points_2d_translated[i + 1, 0]:
            points_to_delete.append(i + 1)

# 删除需要删除的点
helix_intersecting_points_2d_translated = np.delete(helix_intersecting_points_2d_translated, points_to_delete, axis=0)

# 处理 helix_intersecting_points_2d_translated 使其等距，并将最高点设为 (0,0)
helix_intersecting_points_2d_translated = redistribute_points_equally(helix_intersecting_points_2d_translated, num_curve_points)

# ********************************

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

# 最高点的前一个点的切线与垂直向下方向的夹角
if max_y_index > 0:
    tangent_before_max = calculate_tangent(helix_intersecting_points_2d_translated, max_y_index - 1)
    angle_before_max = calculate_angle(-1 * tangent_before_max)
else:
    angle_before_max = None

# 最高点的后一个点的切线与垂直向下方向的夹角
if max_y_index < len(helix_intersecting_points_2d_translated) - 1:
    tangent_after_max = calculate_tangent(helix_intersecting_points_2d_translated, max_y_index + 1)
    angle_after_max = calculate_angle(tangent_after_max)
else:
    angle_after_max = None

# 第二个点的切线与垂直向下方向的夹角
if len(helix_intersecting_points_2d_translated) > 1:
    tangent_second = calculate_tangent(helix_intersecting_points_2d_translated, 1)
    angle_second = calculate_angle(-1 * tangent_second)
else:
    angle_second = None

# 倒数第二个点的切线与垂直向下方向的夹角
if len(helix_intersecting_points_2d_translated) > 1:
    tangent_penultimate = calculate_tangent(helix_intersecting_points_2d_translated, len(helix_intersecting_points_2d_translated) - 2)
    angle_penultimate = calculate_angle(tangent_penultimate)
else:
    angle_penultimate = None

# 获取第一个点和最后一个点的坐标
first_point = helix_intersecting_points_2d_translated[0]
last_point = helix_intersecting_points_2d_translated[-1]

# ********************************

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
IF (WHEEL_DIA<{wheel_dia:.4f}) GOTOF DIA_0000;

;********************************
"""

# 将内容写入文件
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(head_content)

# 拆分成两个数组
right_points = helix_intersecting_points_2d_translated[helix_intersecting_points_2d_translated[:, 0] < 0]
left_points = helix_intersecting_points_2d_translated[helix_intersecting_points_2d_translated[:, 0] >= 0]

# x 坐标小于0的点反向排序
right_points = right_points[::-1]

# 准备写入文件的内容
file_content = f"""
;********************************
DIA_{wheel_dia_str}:
IF DRESSER[40]==1;
;*********************************************
DRESSER[41]={angle_before_max:.4f};外部齿形程序右起点角度(竖直向下夹角)
DRESSER[42]={angle_after_max:.4f};外部齿形程序左起点角度(竖直向下夹角)
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

# 将内容写入文件
with open("output.txt", "a", encoding="utf-8") as f:
    f.write(file_content)

# ********************************

# 设置中文字体

# 检测操作系统
current_os = platform.system()

# 根据操作系统设置字体
if current_os == 'Windows':
    plt.rcParams['font.family'] = 'SimHei'
elif current_os == 'Darwin':  # macOS
    plt.rcParams['font.family'] = 'Heiti TC'
else:
    plt.rcParams['font.family'] = 'Noto Sans CJK JP'

plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号 '-' 显示为方块的问题

# 绘制结果
fig = plt.figure(figsize=(28, 7))  # 调整fig大小以包含4张图

# 绘制原始曲线，不显示法线
ax1 = fig.add_subplot(141)
ax1.plot(curve_points[:, 0], curve_points[:, 1], label='标准齿形轨迹')
# 屏蔽法线显示
# ax1.quiver(curve_points[:, 0], curve_points[:, 1], normals[:, 0], normals[:, 1], color='red', scale=20, label='Normals')
ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -1))  # 调整图例位置
ax1.set_aspect('equal')
ax1.set_title('标准齿形', pad=20)  # 调整标题位置
ax1.set_xlabel('X')
ax1.set_ylabel('Y')

# 绘制旋转后的曲线和法线，以及螺旋曲面上的点
ax2 = fig.add_subplot(142, projection='3d')
ax2.plot(helix_surface_points_right[:, 0], helix_surface_points_right[:, 1], helix_surface_points_right[:, 2], label='右侧螺旋曲面')
ax2.scatter(helix_intersecting_points_right[:, 0], helix_intersecting_points_right[:, 1], helix_intersecting_points_right[:, 2], color='yellow', s=10, label='右侧砂轮接触点')
ax2.plot(helix_surface_points_left[:, 0], helix_surface_points_left[:, 1], helix_surface_points_left[:, 2], label='左侧螺旋曲面')
ax2.scatter(helix_intersecting_points_left[:, 0], helix_intersecting_points_left[:, 1], helix_intersecting_points_left[:, 2], color='yellow', s=10, label='左侧砂轮接触点')

# 标注异常点及后续所有点在曲面中的位置
if delete_index_right is not None:
    ax2.scatter(anomalous_points_right[:, 0], anomalous_points_right[:, 1], anomalous_points_right[:, 2], color='red', s=20, label='右侧异常接触点')
if delete_index_left is not None:
    ax2.scatter(anomalous_points_left[:, 0], anomalous_points_left[:, 1], anomalous_points_left[:, 2], color='red', s=20, label='左侧异常接触点')

ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2))  # 调整图例位置
ax2.set_title('滚道加工面', pad=20)  # 调整标题位置
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_zlabel('Z')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], u[0], u[1], u[2], length=5, color='r', label='New X-axis')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], v[0], v[1], v[2], length=5, color='g', label='New Y-axis')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], w[0], w[1], w[2], length=5, color='b', label='New Z-axis')

# 设置 ax2 的坐标比例
ax2.set_box_aspect([1, 1, 1])  # 设置为等比例

# 绘制螺旋曲面相交点旋转到新坐标系二维平面
ax3 = fig.add_subplot(143)
ax3.plot(fixed_curve_points[:, 0], fixed_curve_points[:, 1], label='标准齿形轨迹', linewidth=0.5)
ax3.scatter(fixed_curve_points[:, 0], fixed_curve_points[:, 1], color='blue', s=1, label='标准齿形轨迹点')
if len(helix_intersecting_points_2d_smoothed) > 0:
    ax3.plot(helix_intersecting_points_2d_smoothed[:, 0], helix_intersecting_points_2d_smoothed[:, 1], label='干涉砂轮齿形轨迹', linewidth=0.5)
    ax3.scatter(helix_intersecting_points_2d_smoothed[:, 0], helix_intersecting_points_2d_smoothed[:, 1], color='red', s=1, label='干涉砂轮齿形轨迹点')

# 标注 x 坐标小于上一个点的点
if len(anomalies_smoothed) > 0:
    ax3.scatter(anomalies_smoothed[:, 0], anomalies_smoothed[:, 1], color='#0053ac', s=10, label='齿底异常点')

# 标注 曲线上有交叉的点
if len(helix_intersecting_points_2d_over_combined) > 0:
    ax3.scatter(helix_intersecting_points_2d_over_combined[:, 0], helix_intersecting_points_2d_over_combined[:, 1], color='#1f5793', s=10, label='齿顶异常点')

# 标注 helix_intersecting_points[delete_index] 的原点位置和来源
if delete_index_right is not None:
    ax3.scatter(original_points_abnormal_right[:, 0], original_points_abnormal_right[:, 1], color='green', s=5, label=f'异常点在原始轨道的右侧位置 (螺旋圈数: {turn_index_right}, 点位号: {original_point_index_right})')
if delete_index_left is not None:
    ax3.scatter(original_points_abnormal_left[:, 0], original_points_abnormal_left[:, 1], color='green', s=5, label=f'异常点在原始轨道的左侧位置 (螺旋圈数: {turn_index_left}, 点位号: {original_point_index_left})')

# 标注原始曲线中第一个不符合条件的点的切线斜率
if tangent_anomalies_index_right is not None:
    ax3.quiver(original_points_abnormal_right[0, 0], original_points_abnormal_right[0, 1], tangent_anomalies_index_right[0], tangent_anomalies_index_right[1], color='red', scale=5, label=f'右侧第一个异常点的切线斜率: {anomalies_ang_right:.4f}')
if tangent_anomalies_index_left is not None:
    ax3.quiver(original_points_abnormal_left[-1, 0], original_points_abnormal_left[-1, 1], tangent_anomalies_index_left[0], tangent_anomalies_index_left[1], color='red', scale=5, label=f'左侧第一个异常点的切线斜率: {anomalies_ang_left:.4f}')

ax3.legend(loc='upper center', bbox_to_anchor=(0.5, -0.5))  # 调整图例位置
ax3.set_aspect('equal')
ax3.set_title('原始轨迹与干涉轨迹对比')
ax3.set_xlabel('X')
ax3.set_ylabel('Y')

# 绘制平移后的点到第4张图
ax4 = fig.add_subplot(144)
ax4.plot(helix_intersecting_points_2d_translated[:, 0], helix_intersecting_points_2d_translated[:, 1], label='优化后的干涉轨迹曲线', linewidth=0.5)
ax4.scatter(helix_intersecting_points_2d_translated[:, 0], helix_intersecting_points_2d_translated[:, 1], color='red', s=1, label='优化后的干涉轨迹点')
ax4.legend(loc='upper center', bbox_to_anchor=(0.5, -1))  # 调整图例位置
ax4.set_aspect('equal')
ax4.set_title('最终干涉轨迹', pad=20)
ax4.set_xlabel('X')
ax4.set_ylabel('Y')

multiline_text = f"钢球直径：3.969\n" \
                 f"钢球接触角：45\n" \
                 f"工件中径：{mid_dia:.4f}\n" \
                 f"工件导程：{work_lead:.4f}\n" \
                 f"螺旋升角：{angle:.4f}\n" \
                 f"砂轮安装角：{gan_angle:.4f}\n" \
                 f"砂轮杆据中心偏移：{gan_distance:.4f}\n" \
                 f"砂轮直径：{wheel_dia:.4f}\n" \
                 f"砂轮齿高：{height_difference:.4f}\n" \
                 f"砂轮齿宽：{width_max:.4f}"
fig.text(0.1, 0.95, multiline_text, fontsize=12, color='#000000', ha='left', va='top', wrap=True)

plt.show()