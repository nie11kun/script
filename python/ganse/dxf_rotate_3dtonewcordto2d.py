import numpy as np
import matplotlib.pyplot as plt
import ezdxf

# 定义一个函数，从 DXF 文件中加载曲线，并仅保留 XY 坐标，同时应用偏移
def load_dxf_curve(filename, offset=np.array([0, 0]), num_points=100):
    doc = ezdxf.readfile(filename)  # 读取 DXF 文件
    msp = doc.modelspace()  # 获取模型空间
    points = []
    for entity in msp:
        if entity.dxftype() == 'LWPOLYLINE':
            # 处理轻量级多段线实体
            points.extend([(point[0] + offset[0], point[1] + offset[1]) for point in entity])
        elif entity.dxftype() == 'LINE':
            # 处理直线实体，将其分割为等距的离散点
            start = np.array([entity.dxf.start.x, entity.dxf.start.y]) + offset
            end = np.array([entity.dxf.end.x, entity.dxf.end.y]) + offset
            line_points = np.linspace(start, end, num_points)
            points.extend(line_points)
        elif entity.dxftype() == 'ARC':
            # 处理圆弧实体，将其分割为等距的角度采样点
            center = np.array([entity.dxf.center.x, entity.dxf.center.y]) + offset
            radius = entity.dxf.radius
            start_angle = np.radians(entity.dxf.start_angle)
            end_angle = np.radians(entity.dxf.end_angle)
            theta = np.linspace(start_angle, end_angle, num_points)
            arc_points = np.vstack((center[0] + radius * np.cos(theta), center[1] + radius * np.sin(theta))).T
            points.extend(arc_points)
    return np.array(points)

# 定义绕 y 轴旋转的旋转矩阵
def rotation_matrix_y(alpha):
    return np.array([
        [np.cos(alpha), 0, np.sin(alpha)],
        [0, 1, 0],
        [-np.sin(alpha), 0, np.cos(alpha)]
    ])

# 定义一个函数，绕某个轴旋转点
def rotate_points(points, angle, pivot):
    # 将点平移到原点
    translated_points = points - pivot
    # 添加 z 轴坐标
    points_3d = np.hstack((translated_points, np.zeros((translated_points.shape[0], 1))))
    # 计算旋转矩阵
    R = rotation_matrix_y(np.radians(angle))
    # 进行旋转
    rotated_points = points_3d @ R.T
    # 将点平移回去
    rotated_points[:, :2] += pivot
    return rotated_points

# 定义新坐标系的原点
new_origin = np.array([5, -5, 0])
# 定义新坐标系的基矢量（确保它们是单位向量并且相互垂直）
u = np.array([0, 1, 0]) / np.sqrt(2)  # 新坐标系的 x 轴方向
v = np.array([-1, 0, 0]) / np.sqrt(2)  # 新坐标系的 y 轴方向
w = np.array([0, 0, 1])  # 新坐标系的 z 轴方向

# 构建转换矩阵
transformation_matrix = np.array([u, v, w]).T

# 偏移量
offset = np.array([5, -5])

# 从 DXF 文件加载曲线，并应用偏移
dxf_filename = 'test.dxf'
curve_points = load_dxf_curve(dxf_filename, offset)

# 选择旋转的基准点，这里选择曲线的中点
pivot_index = len(curve_points) // 2
# pivot = curve_points[pivot_index]
pivot = [5,-5]
angle = 10  # 旋转角度

# 旋转后的点
rotated_points = rotate_points(curve_points, angle, pivot)

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
        # 进行旋转
        rotated_point = rotation_matrix @ point
        # 投影到 xy 平面
        projected_point = rotated_point[:2]
        projected_points.append(projected_point)
    return np.array(projected_points)

# 将点旋转到新坐标系的 xy 平面
points_2d = rotate_to_xy_plane(points_new_coordinate_system)

# 绘制结果
fig = plt.figure(figsize=(14, 7))

# 绘制原始曲线
ax1 = fig.add_subplot(131)
ax1.plot(curve_points[:, 0], curve_points[:, 1], label='Original Curve with Offset')
ax1.scatter(curve_points[:, 0], curve_points[:, 1], color='blue')
ax1.legend()
ax1.set_aspect('equal')
ax1.set_title('Original Curve with Offset')
ax1.set_xlabel('X')
ax1.set_ylabel('Y')

# 绘制旋转后的曲线
ax2 = fig.add_subplot(132, projection='3d')
ax2.plot(rotated_points[:, 0], rotated_points[:, 1], rotated_points[:, 2], label='Rotated Curve')
ax2.scatter(rotated_points[:, 0], rotated_points[:, 1], rotated_points[:, 2], color='blue')
ax2.legend()
ax2.set_title('Rotated Curve')
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_zlabel('Z')

# 绘制新坐标系的基矢量
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

points_2d
