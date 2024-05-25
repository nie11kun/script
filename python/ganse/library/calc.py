import numpy as np
import ezdxf
from scipy.interpolate import make_interp_spline
import sys
import numba

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
@numba.jit(nopython=True)
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

# 删除文本文档中每一行开头的空格
def remove_leading_whitespace(input_file, output_file):
    # 读取文件内容
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 去除每行开头的空格和缩进
    cleaned_lines = [line.lstrip() for line in lines]

    # 将处理后的内容写回到新文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(cleaned_lines)