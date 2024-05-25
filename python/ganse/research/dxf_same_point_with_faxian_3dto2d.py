import numpy as np
import matplotlib.pyplot as plt
import ezdxf

# 定义一个函数，从 DXF 文件中加载曲线，并仅保留 XY 坐标，同时应用偏移和等距离散化
def load_dxf_curve(filename, offset=np.array([0, 0]), segment_length=1.0):
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

# 定义新坐标系的原点
new_origin = np.array([10, 10, 10])
# 定义新坐标系的基矢量（确保它们是单位向量并且相互垂直）
u = np.array([1, 1, 0]) / np.sqrt(2)  # 新坐标系的 x 轴方向
v = np.array([-1, 1, 0]) / np.sqrt(2)  # 新坐标系的 y 轴方向
w = np.array([0, 0, 1])  # 新坐标系的 z 轴方向

# 构建转换矩阵
transformation_matrix = np.array([u, v, w]).T

# 偏移量
offset = np.array([5, -5])
segment_length = 0.1  # 离散化段的长度

# 从 DXF 文件加载曲线，并应用偏移
dxf_filename = 'test.dxf'
curve_points = load_dxf_curve(dxf_filename, offset, segment_length)

# 计算曲线点的法线
normals = compute_normals(curve_points)

# 选择旋转的基准点，这里选择曲线的中点
pivot_index = len(curve_points) // 2
pivot = curve_points[pivot_index]
angle = 10  # 旋转角度

# 旋转点和法线
rotated_points, rotated_normals = rotate_points_and_normals(curve_points, normals, angle, pivot)

# 将旋转后的点转换到新坐标系中
points_translated = rotated_points - new_origin
points_new_coordinate_system = points_translated @ transformation_matrix

# 定义一个函数，将点旋转到新坐标系的 xy 平面
def rotate_to_xy_plane(points):
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

# 将点旋转到新坐标系的 xy 平面
points_2d = rotate_to_xy_plane(points_new_coordinate_system)

# 绘制结果
fig = plt.figure(figsize=(14, 7))

# 绘制原始曲线和法线
ax1 = fig.add_subplot(131)
ax1.plot(curve_points[:, 0], curve_points[:, 1], label='Original Curve with Offset')
ax1.quiver(curve_points[:, 0], curve_points[:, 1], normals[:, 0], normals[:, 1], color='red', scale=20)
ax1.legend()
ax1.set_aspect('equal')
ax1.set_title('Original Curve with Normals')
ax1.set_xlabel('X')
ax1.set_ylabel('Y')

# 绘制旋转后的曲线和法线
ax2 = fig.add_subplot(132, projection='3d')
ax2.plot(rotated_points[:, 0], rotated_points[:, 1], rotated_points[:, 2], label='Rotated Curve')
ax2.quiver(rotated_points[:, 0], rotated_points[:, 1], rotated_points[:, 2], 
           rotated_normals[:, 0], rotated_normals[:, 1], rotated_normals[:, 2], color='red', length=0.5, normalize=True)
ax2.legend()
ax2.set_title('Rotated Curve with Normals')
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_zlabel('Z')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], u[0], u[1], u[2], length=5, color='r', label='New X-axis')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], v[0], v[1], v[2], length=5, color='g', label='New Y-axis')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], w[0], w[1], w[2], length=5, color='b', label='New Z-axis')

# 绘制新坐标系二维平面上的点
ax3 = fig.add_subplot(133)
ax3.plot(points_2d[:, 0], points_2d[:, 1], label='2D Projection in New Coordinate System')
ax3.scatter(points_2d[:, 0], points_2d[:, 1], color='blue')
ax3.legend()
ax3.set_aspect('equal')
ax3.set_title('2D Projection in New Coordinate System')
ax3.set_xlabel('X')
ax3.set_ylabel('Y')

plt.show()