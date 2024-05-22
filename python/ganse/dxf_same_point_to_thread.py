import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import ezdxf

# 从DXF文件中读取曲线并提取XY平面坐标，确保离散点间距一致且可自定义离散点个数
def read_dxf_curve(filename, num_points):
    doc = ezdxf.readfile(filename)
    msp = doc.modelspace()
    x_coords = []
    y_coords = []
    
    for entity in msp:
        if entity.dxftype() == 'LWPOLYLINE':  # 曲线是LWPOLYLINE类型
            points = np.array(entity.points())
            distances = np.sqrt(np.sum(np.diff(points, axis=0)**2, axis=1))
            total_distance = np.sum(distances)
            num_segments = len(points) - 1
            segment_length = total_distance / num_points
            for i in range(num_segments):
                segment_points = np.linspace(points[i], points[i+1], int(distances[i] / segment_length) + 1)
                x_coords.extend(segment_points[:, 0])
                y_coords.extend(segment_points[:, 1])
        elif entity.dxftype() == 'LINE':  # 曲线是LINE类型
            start = np.array([entity.dxf.start.x, entity.dxf.start.y])
            end = np.array([entity.dxf.end.x, entity.dxf.end.y])
            segment_points = np.linspace(start, end, num_points)
            x_coords.extend(segment_points[:, 0])
            y_coords.extend(segment_points[:, 1])
        elif entity.dxftype() == 'ARC':  # 曲线是ARC类型
            center = np.array([entity.dxf.center.x, entity.dxf.center.y])
            radius = entity.dxf.radius
            start_angle = np.radians(entity.dxf.start_angle)
            end_angle = np.radians(entity.dxf.end_angle)
            angles = np.linspace(start_angle, end_angle, num_points)
            x_coords.extend(center[0] + radius * np.cos(angles))
            y_coords.extend(center[1] + radius * np.sin(angles))
        # 可以根据需要添加更多类型的处理

    return np.array(x_coords), np.array(y_coords)

# 对曲线进行偏移处理
def offset_curve(x, y, offset_x, offset_y):
    x_offset = x + offset_x
    y_offset = y + offset_y
    return x_offset, y_offset

# 将曲线绕Y轴旋转一定角度
def rotate_around_y(x, y, z, angle):
    x_new = x * np.cos(angle) + z * np.sin(angle)
    z_new = -x * np.sin(angle) + z * np.cos(angle)
    return x_new, y, z_new

# 生成螺旋曲面
def generate_helix_surface(x, y, z, v, k, rotation_angle):
    # 先绕Y轴旋转
    x_rot, y_rot, z_rot = rotate_around_y(x, y, z, rotation_angle)
    
    # 然后生成螺旋曲面
    X = np.outer(x_rot, np.ones_like(v)) + k * v
    Y = np.outer(y_rot, np.cos(v)) - np.outer(z_rot, np.sin(v))
    Z = np.outer(y_rot, np.sin(v)) + np.outer(z_rot, np.cos(v))
    
    return X, Y, Z

# 读取DXF文件中的曲线
filename = 'test.dxf'  # 请替换为实际的DXF文件路径
num_points = 100  # 自定义离散点个数
x_coords, y_coords = read_dxf_curve(filename, num_points)
z_coords = np.zeros_like(x_coords)

# 输入偏移量
offset_x = 5  # X方向偏移量
offset_y = 20  # Y方向偏移量

# 对曲线进行偏移处理
x_coords, y_coords = offset_curve(x_coords, y_coords, offset_x, offset_y)

# 输入旋转角度（绕Y轴旋转，单位为度）
rotation_angle_deg = 0  # 例如45度
rotation_angle_rad = np.radians(rotation_angle_deg)  # 转换为弧度

# 自定义曲线起点坐标
start_x = x_coords[0]
start_y = y_coords[0]

# 计算k值
k = 2 * np.pi * start_y * np.tan(rotation_angle_rad) / (2 * np.pi)

# 参数范围
v = np.linspace(0, 2 * np.pi, 100)  # 控制旋转的参数范围

# 生成螺旋曲面坐标
X, Y, Z = generate_helix_surface(x_coords, y_coords, z_coords, v, k, rotation_angle_rad)

# 创建3D图形
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(X, Y, Z, cmap='viridis')

# 设置图形标题和轴标签
ax.set_title('Helix Surface')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# 设置相同的坐标轴单位
max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max() / 2.0

mid_x = (X.max()+X.min()) * 0.5
mid_y = (Y.max()+Y.min()) * 0.5
mid_z = (Z.max()+Z.min()) * 0.5

ax.set_xlim(mid_x - max_range, mid_x + max_range)
ax.set_ylim(mid_y - max_range, mid_y + max_range)
ax.set_zlim(mid_z - max_range, mid_z + max_range)

# 显示图形
plt.show()
