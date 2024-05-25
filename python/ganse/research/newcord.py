import numpy as np

# 定义新的坐标系的原点
new_origin = np.array([10, 10, 10])

# 定义新的坐标系的基矢量
u = np.array([1, 1, 0]) / np.sqrt(2)
v = np.array([-1, 1, 0]) / np.sqrt(2)
w = np.array([0, 0, 1])

# 构建转换矩阵
transformation_matrix = np.array([u, v, w]).T

# 定义要转换的点
points_cartesian = np.array([
    [11, 12, 13],
    [14, 15, 16],
    [17, 18, 19]
])

# 将原始坐标系中的点平移到新的原点
points_translated = points_cartesian - new_origin

# 将平移后的点旋转到新的坐标系
points_new_coordinate_system = points_translated @ transformation_matrix

print(points_new_coordinate_system)
