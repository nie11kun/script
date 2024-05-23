import numpy as np
import matplotlib.pyplot as plt
import ezdxf
from scipy.interpolate import make_interp_spline

# 砂轮杆偏移工件中心距离
gan_distance = 15

# 砂轮安装角
gan_angle = 3

# 工件中径
mid_dia = 45

# 导程
work_lead = 20

# 螺旋升角
angle = np.rad2deg(np.arctan2(work_lead, np.pi * mid_dia))
print(f'标准螺旋升角: {angle}')

# dxf 曲线离散点个数
segment_length = 0.01

# 螺旋曲面绘制次数
num_turns = 3000
# 每个曲面移动角度
turn_angle = 0.01

# 判断法线是否相交的最小距离
min_distance = 0.001

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
    return np.vstack(surface_points), np.vstack(surface_normals)

# 生成平滑曲线上的点
def smooth_curve(points, num_points):
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

# 定义绕 x 轴旋转和平移的函数，生成螺旋曲面上的点和法线
def generate_helix_surface(points, normals, num_turns=2000, turn_angle=0.01, turn_distance=None):
    if turn_distance is None:
        raise ValueError("turn_distance must be provided or calculated before calling generate_helix_surface.")
    surface_points = []
    surface_normals = []
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
    return np.vstack(surface_points), np.vstack(surface_normals)

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

# 从 DXF 文件加载曲线，并应用偏移
dxf_filename = 'test.dxf'  # DXF 文件名
curve_points = load_dxf_curve(dxf_filename, offset, segment_length)

# 计算曲线点的法线
normals = compute_normals(curve_points)

# 选择旋转的基准点，这里选择曲线的中点
pivot = np.array([0, 0])

# 旋转点和法线
rotated_points, rotated_normals = rotate_points_and_normals(curve_points, normals, angle, pivot)

# 找到与指定直线相交的点
line_point = new_origin  # 新坐标系中直线的一点
line_direction = u  # 新坐标系中直线的方向
intersecting_points = find_intersecting_points(rotated_points, rotated_normals, line_point, line_direction, min_distance)

# 将旋转后的点和法线转换到新坐标系中
points_translated = rotated_points - new_origin
points_new_coordinate_system = points_translated @ transformation_matrix
normals_translated = rotated_normals[:, :3]  # 确保法线是三维的
normals_new_coordinate_system = normals_translated @ transformation_matrix

# 将相交点转换到新坐标系中
intersecting_points_translated = intersecting_points - new_origin
intersecting_points_new_coordinate_system = intersecting_points_translated @ transformation_matrix

# 将相交的点旋转到新坐标系的 xy 平面
points_2d = rotate_to_xy_plane(intersecting_points_new_coordinate_system)

# 自动计算 turn_distance
turn_distance = work_lead / 360

helix_surface_points, helix_surface_normals = generate_helix_surface(rotated_points, rotated_normals, num_turns, turn_angle, turn_distance)

# 计算螺旋曲面上每条曲线上的点的法线是否与新坐标系上的直线相交
helix_intersecting_points = find_intersecting_points(helix_surface_points, helix_surface_normals, line_point, line_direction, min_distance)

# 将 helix_intersecting_points 转换到新坐标系中
helix_intersecting_points_translated = helix_intersecting_points - new_origin
helix_intersecting_points_new_coordinate_system = helix_intersecting_points_translated @ transformation_matrix

# 将 helix_intersecting_points 转换到新坐标系的 xy 平面
helix_intersecting_points_2d = rotate_to_xy_plane(helix_intersecting_points_new_coordinate_system)

# 去掉 helix_intersecting_points_2d 中 x 坐标大于 0 的点
helix_intersecting_points_2d_filtered = helix_intersecting_points_2d[helix_intersecting_points_2d[:, 0] <= 0]

# 镜像复制 helix_intersecting_points_2d_filtered 沿着 X 轴并合并
helix_intersecting_points_2d_mirrored = helix_intersecting_points_2d_filtered.copy()
helix_intersecting_points_2d_mirrored[:, 0] = -helix_intersecting_points_2d_mirrored[:, 0]

# 将 helix_intersecting_points_2d_filtered 反向排序
helix_intersecting_points_2d_filtered = helix_intersecting_points_2d_filtered[::-1]

# 合并点
helix_intersecting_points_2d_combined = np.vstack((helix_intersecting_points_2d_filtered, helix_intersecting_points_2d_mirrored))

# 获取 curve_points 的点个数
num_curve_points = len(curve_points)

# 将 helix_intersecting_points_2d_combined 处理成平滑曲线上的点，点个数与 curve_points 一致
helix_intersecting_points_2d_smoothed = smooth_curve(helix_intersecting_points_2d_combined, num_curve_points)

# 在 x < 0 的点中，当后一个点的 y 坐标小于前一个点的 y 坐标，则删除前面这个点
points_to_keep = []
for i in range(1, len(helix_intersecting_points_2d_smoothed)):
    if helix_intersecting_points_2d_smoothed[i, 0] < 0:
        if helix_intersecting_points_2d_smoothed[i, 1] >= helix_intersecting_points_2d_smoothed[i - 1, 1]:
            points_to_keep.append(helix_intersecting_points_2d_smoothed[i - 1])
    else:
        points_to_keep.append(helix_intersecting_points_2d_smoothed[i - 1])

points_to_keep.append(helix_intersecting_points_2d_smoothed[-1])  # 保留最后一个点

# 更新 helix_intersecting_points_2d_smoothed
helix_intersecting_points_2d_smoothed = np.array(points_to_keep)

# 在 x > 0 的点中，当后一个点的 y 坐标大于前一个点的 y 坐标，则删除后面这个点
points_to_keep = []
for i in range(len(helix_intersecting_points_2d_smoothed) - 1):
    if helix_intersecting_points_2d_smoothed[i, 0] > 0:
        if helix_intersecting_points_2d_smoothed[i + 1, 1] <= helix_intersecting_points_2d_smoothed[i, 1]:
            points_to_keep.append(helix_intersecting_points_2d_smoothed[i + 1])
    else:
        points_to_keep.append(helix_intersecting_points_2d_smoothed[i + 1])

points_to_keep.append(helix_intersecting_points_2d_smoothed[0])  # 保留第一个点

# 更新 helix_intersecting_points_2d_smoothed
helix_intersecting_points_2d_smoothed = np.array(points_to_keep)

# 获取 helix_intersecting_points_2d_smoothed 中 y 坐标最大点
max_y_index_smoothed = np.argmax(helix_intersecting_points_2d_smoothed[:, 1])
max_y_point_smoothed = helix_intersecting_points_2d_smoothed[max_y_index_smoothed]

print(f'砂轮直径: {max_y_point_smoothed[1] * 2}')

# 找到 y 轴最大点作为基准原点
max_y_index = np.argmax(helix_intersecting_points_2d_smoothed[:, 1])
reference_origin = helix_intersecting_points_2d_smoothed[max_y_index]

# 平移所有点到新坐标系
helix_intersecting_points_2d_translated = helix_intersecting_points_2d_smoothed - reference_origin

# 标注 helix_intersecting_points_2d_translated 中 x 坐标小于上一个点的点
anomalies_translated = []
for i in range(1, len(helix_intersecting_points_2d_translated)):
    if helix_intersecting_points_2d_translated[i, 0] < helix_intersecting_points_2d_translated[i-1, 0]:
        anomalies_translated.append(helix_intersecting_points_2d_translated[i])

anomalies_translated = np.array(anomalies_translated)

# 绘制结果
fig = plt.figure(figsize=(28, 7))  # 调整fig大小以包含4张图

# 绘制原始曲线，不显示法线
ax1 = fig.add_subplot(141)
ax1.plot(curve_points[:, 0], curve_points[:, 1], label='Original Curve with Offset')
# 屏蔽法线显示
# ax1.quiver(curve_points[:, 0], curve_points[:, 1], normals[:, 0], normals[:, 1], color='red', scale=20, label='Normals')
ax1.legend()
ax1.set_aspect('equal')
ax1.set_title('Original Curve')
ax1.set_xlabel('X')
ax1.set_ylabel('Y')

# 绘制旋转后的曲线和法线，以及螺旋曲面上的点
ax2 = fig.add_subplot(142, projection='3d')
ax2.plot(helix_surface_points[:, 0], helix_surface_points[:, 1], helix_surface_points[:, 2], label='Helix Surface Points')
ax2.scatter(helix_intersecting_points[:, 0], helix_intersecting_points[:, 1], helix_intersecting_points[:, 2], color='yellow', s=10, label='Helix Intersecting Points')
ax2.legend()
ax2.set_title('Helix Surface')
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
ax3.plot(points_new_coordinate_system[:, 0], points_new_coordinate_system[:, 1], label='Points in New Coordinate System', linewidth=0.5)
ax3.scatter(points_new_coordinate_system[:, 0], points_new_coordinate_system[:, 1], color='blue', s=1, label='Points')
if len(helix_intersecting_points_2d_smoothed) > 0:
    ax3.plot(helix_intersecting_points_2d_smoothed[:, 0], helix_intersecting_points_2d_smoothed[:, 1], label='Helix Intersecting Points', linewidth=0.5)
    ax3.scatter(helix_intersecting_points_2d_smoothed[:, 0], helix_intersecting_points_2d_smoothed[:, 1], color='red', s=1, label='Helix Intersecting Points')
ax3.legend()
ax3.set_aspect('equal')
ax3.set_title('2D Projection of Points and Helix Intersecting Points in New Coordinate System')
ax3.set_xlabel('X')
ax3.set_ylabel('Y')

# 绘制平移后的点到第4张图
ax4 = fig.add_subplot(144)
ax4.plot(helix_intersecting_points_2d_translated[:, 0], helix_intersecting_points_2d_translated[:, 1], label='Translated Points', linewidth=0.5)
ax4.scatter(helix_intersecting_points_2d_translated[:, 0], helix_intersecting_points_2d_translated[:, 1], color='red', s=1, label='Translated Points')

# 标注 x 坐标小于上一个点的点
if len(anomalies_translated) > 0:
    ax4.scatter(anomalies_translated[:, 0], anomalies_translated[:, 1], color='blue', s=10, label='Anomalies')

ax4.legend()
ax4.set_aspect('equal')
ax4.set_title('Translated Helix Intersecting Points')
ax4.set_xlabel('X')
ax4.set_ylabel('Y')

plt.show()

helix_surface_points
