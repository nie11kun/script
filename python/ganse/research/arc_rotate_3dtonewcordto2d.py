import numpy as np
import matplotlib.pyplot as plt

# 定义半圆弧，允许自定义起点
def half_circle(start_point, end_point, num_points=100):
    # 计算半圆弧的中心和半径
    center = (start_point + end_point) / 2
    radius = np.linalg.norm(start_point - end_point) / 2
    theta_start = np.arctan2(start_point[1] - center[1], start_point[0] - center[0])
    theta_end = np.arctan2(end_point[1] - center[1], end_point[0] - center[0])
    
    # 生成角度
    theta = np.linspace(theta_start, theta_end, num_points)
    x = center[0] + radius * np.cos(theta)
    y = center[1] + radius * np.sin(theta)
    return np.vstack((x, y)).T

# 定义旋转矩阵绕 y 轴旋转
def rotation_matrix_y(alpha):
    return np.array([
        [np.cos(alpha), 0, np.sin(alpha)],
        [0, 1, 0],
        [-np.sin(alpha), 0, np.cos(alpha)]
    ])

# 计算旋转后的点
def rotate_points(points, angle, pivot):
    # 平移到原点
    translated_points = points - pivot
    # 添加 z 轴
    points_3d = np.hstack((translated_points, np.zeros((translated_points.shape[0], 1))))
    # 旋转矩阵
    R = rotation_matrix_y(np.radians(angle))
    # 旋转
    rotated_points = points_3d @ R.T
    # 平移回去
    rotated_points[:, :2] += pivot
    return rotated_points

# 定义新的坐标系的原点
new_origin = np.array([10, 5, 0])

# 定义新的坐标系的基矢量（确保它们是单位向量并且相互垂直）
u = np.array([0, 1, 0]) / np.sqrt(2)
v = np.array([-1, 0, 0]) / np.sqrt(2)
w = np.array([0, 0, 1])

# 构建转换矩阵
transformation_matrix = np.array([u, v, w]).T

# 半圆弧的起点和终点
start_point = np.array([5, 5])
end_point = np.array([15, 5])

# 半圆弧的点
half_circle_points = half_circle(start_point, end_point)

# 选择旋转的基准点，假设选取半圆弧的中点
pivot_index = len(half_circle_points) // 2
pivot = half_circle_points[pivot_index]

# 旋转角度
angle = 10

# 旋转后的点
rotated_points = rotate_points(half_circle_points, angle, pivot)

# 将半圆弧点转换到新坐标系中
points_translated = rotated_points - new_origin
points_new_coordinate_system = points_translated @ transformation_matrix

# 定义函数，将点绕新坐标系的 x 轴旋转到二维平面
def rotate_to_xy_plane(points):
    projected_points = []
    for point in points:
        theta = np.arctan2(point[2], point[1])
        rotation_matrix = np.array([
            [1, 0, 0],
            [0, np.cos(theta), np.sin(theta)],
            [0, -np.sin(theta), np.cos(theta)]
        ])
        rotated_point = rotation_matrix @ point
        projected_point = rotated_point[:2]
        projected_points.append(projected_point)
    return np.array(projected_points)

# 将点绕新坐标系的 x 轴旋转到二维平面
points_2d = rotate_to_xy_plane(points_new_coordinate_system)

# 绘制结果
fig = plt.figure(figsize=(14, 7))

# 原始半圆弧
ax1 = fig.add_subplot(131)
ax1.plot(half_circle_points[:, 0], half_circle_points[:, 1], label='Original Half Circle')
ax1.scatter([start_point[0]], [start_point[1]], color='green', label='Start Point')
ax1.scatter([end_point[0]], [end_point[1]], color='red', label='End Point')
ax1.scatter([pivot[0]], [pivot[1]], color='blue', label='Pivot Point')
ax1.legend()
ax1.set_aspect('equal')
ax1.set_title('Original Half Circle')
ax1.set_xlabel('X')
ax1.set_ylabel('Y')

# 旋转后的圆弧
ax2 = fig.add_subplot(132, projection='3d')
ax2.plot(rotated_points[:, 0], rotated_points[:, 1], rotated_points[:, 2], label='Rotated Half Circle')
ax2.scatter([pivot[0]], [pivot[1]], [0], color='blue', label='Pivot Point')
ax2.legend()
ax2.set_title('Rotated Half Circle')
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_zlabel('Z')

# 绘制新坐标系的基矢量
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], u[0], u[1], u[2], length=5, color='r', label='New X-axis')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], v[0], v[1], v[2], length=5, color='g', label='New Y-axis')
ax2.quiver(new_origin[0], new_origin[1], new_origin[2], w[0], w[1], w[2], length=5, color='b', label='New Z-axis')

# 新坐标系二维平面上的点
ax3 = fig.add_subplot(133)
ax3.plot(points_2d[:, 0], points_2d[:, 1], label='2D Projection in New Coordinate System')
ax3.legend()
ax3.set_aspect('equal')
ax3.set_title('2D Projection in New Coordinate System')
ax3.set_xlabel('X')
ax3.set_ylabel('Y')

plt.show()