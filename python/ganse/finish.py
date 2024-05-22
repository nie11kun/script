import numpy as np
import matplotlib.pyplot as plt
import ezdxf

# 定义一个函数，从 DXF 文件中加载曲线，并仅保留 XY 坐标，同时应用偏移和等距离散化
def load_dxf_curve(filename, offset=np.array([0, 0]), segment_length=0.1):
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
def rotate_points_and_normals(points, normals, angle, pivot):
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
def find_intersecting_points(points, normals, line_point, line_direction, min_distance=0.01):
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

# 定义新坐标系的原点
new_origin = np.array([0, 5, 0])
# 定义新坐标系的基矢量（确保它们是单位向量并且相互垂直）
u = np.array([1, 0, 0]) / np.sqrt(2)  # 新坐标系的 x 轴方向
v = np.array([0, 1, 0]) / np.sqrt(2)  # 新坐标系的 y 轴方向
w = np.array([0, 0, 1])  # 新坐标系的 z 轴方向

# 构建转换矩阵
transformation_matrix = np.array([u, v, w]).T

# 偏移量
offset = np.array([0, 30])
segment_length = 1.0  # 离散化段的长度

# 从 DXF 文件加载曲线，并应用偏移
dxf_filename = 'test.dxf'  # DXF 文件名
curve_points = load_dxf_curve(dxf_filename, offset, segment_length)

# 计算曲线点的法线
normals = compute_normals(curve_points)

# 选择旋转的基准点，这里选择曲线的中点
pivot_index = len(curve_points) // 2
pivot = [5,15]
angle = 0  # 旋转角度

# 旋转点和法线
rotated_points, rotated_normals = rotate_points_and_normals(curve_points, normals, angle, pivot)

# 找到与指定直线相交的点
line_point = new_origin  # 新坐标系中直线的一点
line_direction = u  # 新坐标系中直线的方向
min_distance = 0.001  # 最小距离
intersecting_points = find_intersecting_points(rotated_points, rotated_normals, line_point, line_direction, min_distance)

# 将旋转后的点和法线转换到新坐标系中
points_translated = rotated_points - new_origin
points_new_coordinate_system = points_translated @ transformation_matrix
normals_translated = rotated_normals[:, :3]  # 确保法线是三维的
normals_new_coordinate_system = normals_translated @ transformation_matrix

# 将相交点转换到新坐标系中
intersecting_points_translated = intersecting_points - new_origin
intersecting_points_new_coordinate_system = intersecting_points_translated @ transformation_matrix

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

# 将相交的点旋转到新坐标系的 xy 平面
points_2d = rotate_to_xy_plane(intersecting_points_new_coordinate_system)

# 定义绕 x 轴旋转和平移的函数，生成螺旋曲面上的点和法线
def generate_helix_surface(points, normals, num_turns, turn_angle, turn_distance):
    surface_points = []
    surface_normals = []
    for i in range(num_turns):
        angle = turn_angle * i
        distance = turn_distance * i * turn_angle
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

# 生成螺旋曲面
num_turns = 100
turn_angle = 0.1  # 每次旋转 36 度，相当于 10 次旋转一圈

# 自动计算 turn_distance
turn_distance = 2 * np.pi * rotated_points[0, 1] * np.tan(np.radians(angle)) / 360

# 生成螺旋曲面
helix_surface_points, helix_surface_normals = generate_helix_surface(rotated_points, rotated_normals, num_turns, turn_angle, turn_distance)

# 计算螺旋曲面上每条曲线上的点的法线是否与新坐标系上的直线相交
helix_intersecting_points = find_intersecting_points(helix_surface_points, helix_surface_normals, line_point, line_direction, min_distance)

# 将相交点转换到新坐标系中
helix_intersecting_points_translated = helix_intersecting_points - new_origin
helix_intersecting_points_new_coordinate_system = helix_intersecting_points_translated @ transformation_matrix

# 将相交的点旋转到新坐标系的 xy 平面
helix_points_2d = rotate_to_xy_plane(helix_intersecting_points_new_coordinate_system)

print(f"{rotated_points} to {helix_points_2d}")

# 绘制结果
fig = plt.figure(figsize=(21, 7))

# 绘制原始曲线和法线
ax1 = fig.add_subplot(131)
ax1.plot(curve_points[:, 0], curve_points[:, 1], label='Original Curve with Offset')
ax1.quiver(curve_points[:, 0], curve_points[:, 1], normals[:, 0], normals[:, 1], color='red', scale=20, label='Normals')
ax1.legend()
ax1.set_aspect('equal')
ax1.set_title('Original Curve with Normals')
ax1.set_xlabel('X')
ax1.set_ylabel('Y')

# 绘制旋转后的曲线和法线，以及螺旋曲面上的点和法线
ax2 = fig.add_subplot(132, projection='3d')
ax2.plot(rotated_points[:, 0], rotated_points[:, 1], rotated_points[:, 2], label='Rotated Curve')
ax2.quiver(rotated_points[:, 0], rotated_points[:, 1], rotated_points[:, 2], 
           rotated_normals[:, 0], rotated_normals[:, 1], rotated_normals[:, 2], color='red', length=0.5, normalize=True, label='Rotated Normals')
ax2.scatter(intersecting_points[:, 0], intersecting_points[:, 1], intersecting_points[:, 2], color='green', s=50, label='Intersecting Points')
ax2.plot(helix_surface_points[:, 0], helix_surface_points[:, 1], helix_surface_points[:, 2], label='Helix Surface Points')
# ax2.quiver(helix_surface_points[:, 0], helix_surface_points[:, 1], helix_surface_points[:, 2],
#            helix_surface_normals[:, 0], helix_surface_normals[:, 1], helix_surface_normals[:, 2],
#            color='blue', length=0.5, normalize=True, label='Helix Surface Normals')
ax2.scatter(helix_intersecting_points[:, 0], helix_intersecting_points[:, 1], helix_intersecting_points[:, 2], color='yellow', s=50, label='Helix Intersecting Points')
ax2.legend()
ax2.set_title('Rotated Curve with Normals and Helix Surface')
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_zlabel('Z')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], u[0], u[1], u[2], length=5, color='r', label='New X-axis')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], v[0], v[1], v[2], length=5, color='g', label='New Y-axis')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], w[0], w[1], w[2], length=5, color='b', label='New Z-axis')

# 设置 ax2 的坐标比例
ax2.set_box_aspect([1, 1, 1])  # 设置为等比例

# 绘制相交点旋转到新坐标系二维平面
ax3 = fig.add_subplot(133)
if len(helix_points_2d) > 0:
    ax3.plot(helix_points_2d[:, 0], helix_points_2d[:, 1], label='2D Projection in New Coordinate System')
    ax3.scatter(helix_points_2d[:, 0], helix_points_2d[:, 1], color='blue', label='Points')
    ax3.legend()
ax3.set_aspect('equal')
ax3.set_title('2D Projection in New Coordinate System')
ax3.set_xlabel('X')
ax3.set_ylabel('Y')

plt.show()

helix_surface_points
