import numpy as np

# 定义函数，将3D点投影到xy平面，通过绕x轴旋转
def project_to_xy_plane(points, center_axis=(100, 0, 0)):
    projected_points = []
    for point in points:
        # 将点平移，使旋转轴位于原点
        translated_point = point - np.array(center_axis)
        
        # 计算绕x轴旋转的角度
        theta = np.arctan2(translated_point[2], translated_point[1])
        
        # 绕x轴的旋转矩阵
        rotation_matrix = np.array([
            [1, 0, 0],
            [0, np.cos(theta), np.sin(theta)],
            [0, -np.sin(theta), np.cos(theta)]
        ])
        
        # 应用旋转
        rotated_point = rotation_matrix @ translated_point
        
        # 平移回去并投影到xy平面
        projected_point = rotated_point[:2] + np.array(center_axis[:2])
        projected_points.append(projected_point)
    
    return np.array(projected_points)

# 示例3D点
points_3d = np.array([
    [101, 2, 3],
    [102, 3, 4],
    [103, 5, 6],
    [104, 4, 4],
    [105, 6, 7]
])

# 将点投影到xy平面
projected_points = project_to_xy_plane(points_3d)

print(projected_points)
