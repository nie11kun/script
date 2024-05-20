import numpy as np
import matplotlib.pyplot as plt

# 定义半圆弧
def half_circle(radius, num_points=100):
    theta = np.linspace(0, np.pi, num_points)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
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
    translated_points = points - pivot[:2]
    # 添加 z 轴
    points_3d = np.hstack((translated_points, np.zeros((translated_points.shape[0], 1))))
    # 旋转矩阵
    R = rotation_matrix_y(np.radians(angle))
    # 旋转
    rotated_points = points_3d @ R.T
    # 平移回去
    rotated_points[:, :2] += pivot[:2]
    return rotated_points

# 半圆弧的半径
radius = 5
# 半圆弧的点
half_circle_points = half_circle(radius)
# 半圆弧的终点
pivot = np.array([radius, 0])

# 旋转角度
angle = 10

# 旋转后的点
rotated_points = rotate_points(half_circle_points, angle, np.array([pivot[0], pivot[1], 0]))

# 绘制结果
fig = plt.figure(figsize=(10, 5))

# 原始半圆弧
ax1 = fig.add_subplot(121)
ax1.plot(half_circle_points[:, 0], half_circle_points[:, 1], label='Original Half Circle')
ax1.scatter([pivot[0]], [pivot[1]], color='red')  # 绘制终点
ax1.legend()
ax1.set_aspect('equal')
ax1.set_title('Original Half Circle')
ax1.set_xlabel('X')
ax1.set_ylabel('Y')

# 旋转后的圆弧
ax2 = fig.add_subplot(122, projection='3d')
ax2.plot(rotated_points[:, 0], rotated_points[:, 1], rotated_points[:, 2], label='Rotated Half Circle')
ax2.scatter([pivot[0]], [pivot[1]], [0], color='red')  # 绘制终点
ax2.legend()
ax2.set_title('Rotated Half Circle')
ax2.set_xlabel('X')
ax2.set_ylabel('Y')
ax2.set_zlabel('Z')

plt.show()