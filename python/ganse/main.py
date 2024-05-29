from library.main_cycle import main_cycle
import tkinter as tk
from tkinter import messagebox

# 砂轮杆偏移工件中心最大距离
gan_distance_max = 22

# 砂轮杆偏移工件中心最小距离
gan_distance_min = 21

# 砂轮直径步进
step_dia = 1

# 砂轮安装角
gan_angle = 3.47

# 工件中径
mid_dia = 82.5

# 导程
work_lead = 50

# 滚轮圆弧半径
dresser_r = 1.0

# 最终曲线点密度
shape_num = 600

# dxf 文件地址
dxf_file = 'dxf/19.05.dxf'
# ****************************

def on_submit():

    try:
        gan_distance_max = float(entry_gan_distance_max.get())
        gan_distance_min = float(entry_gan_distance_min.get())
        step_dia = float(entry_step_dia.get())
        gan_angle = float(entry_gan_angle.get())
        mid_dia = float(entry_mid_dia.get())
        work_lead = float(entry_work_lead.get())
        dresser_r = float(entry_dresser_r.get())
        shape_num = int(entry_shape_num.get())
        dxf_file = str(entry_dxf_file.get())

        main_cycle(gan_distance_max, gan_distance_min, step_dia, gan_angle, mid_dia, work_lead, dresser_r, shape_num, dxf_file)
    except ValueError:
        messagebox.showerror("输入错误", "请输入有效的整数")

# 创建主窗口
root = tk.Tk()
root.title("参数输入界面")

# 创建标签和输入框
label_gan_distance_max = tk.Label(root, text="砂轮杆偏移工件中心最大距离:")
label_gan_distance_max.grid(row=0, column=0)
entry_gan_distance_max = tk.Entry(root)
entry_gan_distance_max.grid(row=0, column=1)

label_gan_distance_min = tk.Label(root, text="砂轮杆偏移工件中心最小距离:")
label_gan_distance_min.grid(row=1, column=0)
entry_gan_distance_min = tk.Entry(root)
entry_gan_distance_min.grid(row=1, column=1)

label_step_dia = tk.Label(root, text="砂轮直径步进:")
label_step_dia.grid(row=2, column=0)
entry_step_dia = tk.Entry(root)
entry_step_dia.grid(row=2, column=1)

label_gan_angle = tk.Label(root, text="砂轮安装角:")
label_gan_angle.grid(row=3, column=0)
entry_gan_angle = tk.Entry(root)
entry_gan_angle.grid(row=3, column=1)

label_mid_dia = tk.Label(root, text="工件中径:")
label_mid_dia.grid(row=4, column=0)
entry_mid_dia = tk.Entry(root)
entry_mid_dia.grid(row=4, column=1)

label_work_lead = tk.Label(root, text="导程:")
label_work_lead.grid(row=5, column=0)
entry_work_lead = tk.Entry(root)
entry_work_lead.grid(row=5, column=1)

label_dresser_r = tk.Label(root, text="滚轮圆弧半径:")
label_dresser_r.grid(row=6, column=0)
entry_dresser_r = tk.Entry(root)
entry_dresser_r.grid(row=6, column=1)

label_shape_num = tk.Label(root, text="最终曲线点密度:")
label_shape_num.grid(row=7, column=0)
entry_shape_num = tk.Entry(root)
entry_shape_num.grid(row=7, column=1)

label_dxf_file = tk.Label(root, text="dxf 文件地址:")
label_dxf_file.grid(row=8, column=0)
entry_dxf_file = tk.Entry(root)
entry_dxf_file.grid(row=8, column=1)

# 创建提交按钮
submit_button = tk.Button(root, text="提交", command=on_submit)
submit_button.grid(row=9, columnspan=2)

# 显示结果的标签
result = tk.StringVar()
result_label = tk.Label(root, textvariable=result)
result_label.grid(row=10, columnspan=2)

# 运行主循环
root.mainloop()
