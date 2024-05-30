from library.main_cycle import main_cycle
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import json
import threading
import sys
from itertools import cycle
import platform
import subprocess

# 配置文件
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".InterferenceGrindingDressing.json")

VALID_USERNAME = "marco"  # 替换为你的用户名
VALID_PASSWORD = "464116963"  # 替换为你的密码

# 加载配置文件
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

# 保存配置文件
def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

def open_directory(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

def on_submit():
    def run():
        try:
            gan_distance_max = float(entry_gan_distance_max.get())
            gan_distance_min = float(entry_gan_distance_min.get())
            step_dia = float(entry_step_dia.get())
            gan_angle = float(entry_gan_angle.get())
            mid_dia = float(entry_mid_dia.get())
            work_lead = float(entry_work_lead.get())
            dresser_r = float(entry_dresser_r.get())
            shape_num = int(entry_shape_num.get())
            dxf_file = entry_dxf_file.get()
            save_path = entry_save_path.get()

            config = {
                "gan_distance_max": gan_distance_max,
                "gan_distance_min": gan_distance_min,
                "step_dia": step_dia,
                "gan_angle": gan_angle,
                "mid_dia": mid_dia,
                "work_lead": work_lead,
                "dresser_r": dresser_r,
                "shape_num": shape_num,
                "dxf_file": dxf_file,
                "save_path": save_path
            }
            # 保存参数
            save_config(config)

            # 主循环
            main_cycle(gan_distance_max, gan_distance_min, step_dia, gan_angle, mid_dia, work_lead, dresser_r, shape_num, dxf_file, save_path)

            # 打开保存路径目录
            open_directory(save_path)

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字")
        finally:
            # 操作完成后启用提交按钮并隐藏动画和提示信息
            submit_button.config(state=tk.NORMAL)
            stop_animation()
            info_label.grid_remove()

    # 开始提交操作时禁用提交按钮并显示动画和提示信息
    submit_button.config(state=tk.DISABLED)
    info_label.grid(row=13, columnspan=3, pady=10)
    start_animation()
    thread = threading.Thread(target=run)
    thread.daemon = True  # 将线程设置为守护线程
    thread.start()

# 选择 dxf 文件路径
def select_dxf_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("DXF files", "*.dxf")],
        title="选择 DXF 文件"
    )
    if file_path:
        entry_dxf_file.delete(0, tk.END)
        entry_dxf_file.insert(0, file_path)

# 选择保存路径
def select_save_path():
    directory = filedialog.askdirectory(
        title="选择保存路径"
    )
    if directory:
        entry_save_path.delete(0, tk.END)
        entry_save_path.insert(0, directory)

# 加载配置文件到界面
def load_saved_values():
    config = load_config()
    if config:
        entry_gan_distance_max.insert(0, config.get("gan_distance_max", ""))
        entry_gan_distance_min.insert(0, config.get("gan_distance_min", ""))
        entry_step_dia.insert(0, config.get("step_dia", ""))
        entry_gan_angle.insert(0, config.get("gan_angle", ""))
        entry_mid_dia.insert(0, config.get("mid_dia", ""))
        entry_work_lead.insert(0, config.get("work_lead", ""))
        entry_dresser_r.insert(0, config.get("dresser_r", ""))
        entry_shape_num.insert(0, config.get("shape_num", ""))
        entry_dxf_file.insert(0, config.get("dxf_file", ""))
        entry_save_path.insert(0, config.get("save_path", ""))

# 关闭 ui 时强制关闭程序
def on_closing():
    root.destroy()
    sys.exit()

# 动画相关函数
def start_animation():
    global animation_running
    animation_running = True
    canvas.grid(row=12, columnspan=3, pady=10)
    animate_loading()

def stop_animation():
    global animation_running
    animation_running = False
    canvas.grid_remove()

def animate_loading():
    colors = cycle(["#3498db", "#e74c3c", "#f1c40f", "#2ecc71"])
    canvas.delete("all")
    x0, y0, x1, y1 = 20, 20, 80, 80
    arc = canvas.create_arc(x0, y0, x1, y1, start=0, extent=90, style=tk.ARC, outline=next(colors), width=3)
    angle = 0

    def rotate():
        nonlocal angle
        if not animation_running:
            return
        angle = (angle + 5) % 360
        color = next(colors)
        canvas.itemconfig(arc, start=angle, outline=color)
        canvas.after(50, rotate)
    
    rotate()

def login():
    username = username_entry.get()
    password = password_entry.get()
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        login_window.destroy()
        show_main_window()
    else:
        messagebox.showerror("登录失败", "用户名或密码错误")

def show_main_window():
    global root
    root = tk.Tk()
    root.title("干涉磨削砂轮修整软件")

    # 创建主框架
    main_frame = tk.Frame(root, padx=10, pady=10)
    main_frame.grid(row=0, column=0, sticky="nsew")

    # 创建标签和输入框
    label_gan_distance_max = tk.Label(main_frame, text="砂轮杆偏移工件中心最大距离:")
    label_gan_distance_max.grid(row=0, column=0, sticky="e", pady=5)
    global entry_gan_distance_max
    entry_gan_distance_max = tk.Entry(main_frame)
    entry_gan_distance_max.grid(row=0, column=1, pady=5)

    label_gan_distance_min = tk.Label(main_frame, text="砂轮杆偏移工件中心最小距离:")
    label_gan_distance_min.grid(row=1, column=0, sticky="e", pady=5)
    global entry_gan_distance_min
    entry_gan_distance_min = tk.Entry(main_frame)
    entry_gan_distance_min.grid(row=1, column=1, pady=5)

    label_step_dia = tk.Label(main_frame, text="砂轮直径步进:")
    label_step_dia.grid(row=2, column=0, sticky="e", pady=5)
    global entry_step_dia
    entry_step_dia = tk.Entry(main_frame)
    entry_step_dia.grid(row=2, column=1, pady=5)

    label_gan_angle = tk.Label(main_frame, text="砂轮安装角:")
    label_gan_angle.grid(row=3, column=0, sticky="e", pady=5)
    global entry_gan_angle
    entry_gan_angle = tk.Entry(main_frame)
    entry_gan_angle.grid(row=3, column=1, pady=5)

    label_mid_dia = tk.Label(main_frame, text="工件中径:")
    label_mid_dia.grid(row=4, column=0, sticky="e", pady=5)
    global entry_mid_dia
    entry_mid_dia = tk.Entry(main_frame)
    entry_mid_dia.grid(row=4, column=1, pady=5)

    label_work_lead = tk.Label(main_frame, text="导程:")
    label_work_lead.grid(row=5, column=0, sticky="e", pady=5)
    global entry_work_lead
    entry_work_lead = tk.Entry(main_frame)
    entry_work_lead.grid(row=5, column=1, pady=5)

    label_dresser_r = tk.Label(main_frame, text="滚轮圆弧半径:")
    label_dresser_r.grid(row=6, column=0, sticky="e", pady=5)
    global entry_dresser_r
    entry_dresser_r = tk.Entry(main_frame)
    entry_dresser_r.grid(row=6, column=1, pady=5)

    label_shape_num = tk.Label(main_frame, text="最终曲线点密度:")
    label_shape_num.grid(row=7, column=0, sticky="e", pady=5)
    global entry_shape_num
    entry_shape_num = tk.Entry(main_frame)
    entry_shape_num.grid(row=7, column=1, pady=5)

    label_dxf_file = tk.Label(main_frame, text="dxf 文件地址:")
    label_dxf_file.grid(row=8, column=0, sticky="e", pady=5)
    global entry_dxf_file
    entry_dxf_file = tk.Entry(main_frame)
    entry_dxf_file.grid(row=8, column=1, pady=5)
    select_dxf_button = tk.Button(main_frame, text="选择文件", command=select_dxf_file)
    select_dxf_button.grid(row=8, column=2, padx=5, pady=5)

    label_save_path = tk.Label(main_frame, text="输出程序路径:")
    label_save_path.grid(row=9, column=0, sticky="e", pady=5)
    global entry_save_path
    entry_save_path = tk.Entry(main_frame)
    entry_save_path.grid(row=9, column=1, pady=5)
    select_save_path_button = tk.Button(main_frame, text="选择路径", command=select_save_path)
    select_save_path_button.grid(row=9, column=2, padx=5, pady=5)

    # 创建提交按钮
    global submit_button
    submit_button = tk.Button(main_frame, text="提交", command=on_submit)
    submit_button.grid(row=10, columnspan=3, pady=10)

    # 显示结果的标签
    global result
    result = tk.StringVar()
    result_label = tk.Label(main_frame, textvariable=result, wraplength=400)
    result_label.grid(row=11, columnspan=3, pady=10)

    # 创建 Canvas 用于动画
    global canvas
    canvas = tk.Canvas(main_frame, width=100, height=100)
    canvas.grid(row=12, columnspan=3, pady=10)
    canvas.grid_remove()  # 初始隐藏动画

    # 提示信息标签
    global info_label
    info_label = tk.Label(main_frame, text="正在生成齿形程序中...", fg="blue")
    info_label.grid(row=13, columnspan=3, pady=10)
    info_label.grid_remove()  # 初始隐藏提示信息

    # 全局变量用于控制动画
    global animation_running
    animation_running = False

    # 加载保存的参数
    load_saved_values()

    # 绑定关闭事件
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # 运行主循环
    root.mainloop()

# 优化后的登录窗口
login_window = tk.Tk()
login_window.title("登录")

login_window.geometry("300x200")
login_window.configure(bg="#f0f0f0")

login_frame = tk.Frame(login_window, padx=20, pady=20, bg="#f0f0f0")
login_frame.pack(expand=True)

title_label = tk.Label(login_frame, text="用户登录", font=("Helvetica", 16), bg="#f0f0f0")
title_label.grid(row=0, columnspan=2, pady=(0, 10))

username_label = tk.Label(login_frame, text="用户名:", bg="#f0f0f0")
username_label.grid(row=1, column=0, sticky="e", pady=5)
username_entry = tk.Entry(login_frame)
username_entry.grid(row=1, column=1, pady=5)

password_label = tk.Label(login_frame, text="密码:", bg="#f0f0f0")
password_label.grid(row=2, column=0, sticky="e", pady=5)
password_entry = tk.Entry(login_frame, show="*")
password_entry.grid(row=2, column=1, pady=5)

login_button = tk.Button(login_frame, text="登录", command=login, bg="#4CAF50", fg="white", padx=10, pady=5)
login_button.grid(row=3, columnspan=2, pady=(10, 0))

# 运行登录窗口主循环
login_window.mainloop()
