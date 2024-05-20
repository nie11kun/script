import numpy as np

# 定义新的坐标系的原点
new_origin = np.array([0, 0, 0])

# 定义新的坐标系的基矢量（确保它们是单位向量并且相互垂直）
u = np.array([1, 1, 0]) / np.sqrt(2)  # 新坐标系的 x 轴方向
v = np.array([-1, 1, 0]) / np.sqrt(2)  # 新坐标系的 y 轴方向
w = np.array([0, 0, 1])  # 新坐标系的 z 轴方向

# 构建转换矩阵
transformation_matrix = np.array([u, v, w]).T

# 定义要转换的点
points_cartesian = np.array([
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
])

# 将原始坐标系中的点平移到新的原点
points_translated = points_cartesian - new_origin

# 将平移后的点旋转到新的坐标系
points_new_coordinate_system = points_translated @ transformation_matrix

# 定义函数，将点绕新坐标系的 x 轴旋转到二维平面
def rotate_to_xy_plane(points):
    projected_points = []
    for point in points:
        # 计算绕x轴旋转的角度
        theta = np.arctan2(point[2], point[1])
        
        # 绕x轴的旋转矩阵
        rotation_matrix = np.array([
            [1, 0, 0],
            [0, np.cos(theta), np.sin(theta)],
            [0, -np.sin(theta), np.cos(theta)]
        ])
        
        # 应用旋转
        rotated_point = rotation_matrix @ point
        
        # 投影到xy平面
        projected_point = rotated_point[:2]
        projected_points.append(projected_point)
    
    return np.array(projected_points)

# 将点绕新坐标系的 x 轴旋转到二维平面
points_2d = rotate_to_xy_plane(points_new_coordinate_system)

print("转换到新坐标系的点：")
print(points_new_coordinate_system)
print("\n旋转到二维平面的点：")
print(points_2d)
