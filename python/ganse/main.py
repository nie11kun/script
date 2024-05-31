from library.main_cycle import main_cycle
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import json
import threading
import sys
import time
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
            mid_dia = float(entry_mid_dia.get())
            work_lead = float(entry_work_lead.get())
            gan_distance_max = float(entry_gan_distance_max.get())
            gan_distance_min = float(entry_gan_distance_min.get())
            step_dia = float(entry_step_dia.get())
            gan_angle = float(entry_gan_angle.get())
            dxf_file = entry_dxf_file.get()
            dresser_r = float(entry_dresser_r.get())
            shape_num = int(entry_shape_num.get())
            save_path = entry_save_path.get()

            config = {
                "mid_dia": mid_dia,
                "work_lead": work_lead,
                "gan_distance_max": gan_distance_max,
                "gan_distance_min": gan_distance_min,
                "step_dia": step_dia,
                "gan_angle": gan_angle,
                "dxf_file": dxf_file,
                "dresser_r": dresser_r,
                "shape_num": shape_num,
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
            # 操作完成后启用提交按钮并停止进度条
            submit_button.configure(state=ctk.NORMAL)
            stop_animation()

    # 开始提交操作时禁用提交按钮
    submit_button.configure(state=ctk.DISABLED)
    start_animation()  # 启动进度条动画
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
        entry_mid_dia.insert(0, config.get("mid_dia", ""))
        entry_work_lead.insert(0, config.get("work_lead", ""))
        entry_gan_distance_max.insert(0, config.get("gan_distance_max", ""))
        entry_gan_distance_min.insert(0, config.get("gan_distance_min", ""))
        entry_step_dia.insert(0, config.get("step_dia", ""))
        entry_gan_angle.insert(0, config.get("gan_angle", ""))
        entry_dxf_file.insert(0, config.get("dxf_file", ""))
        entry_dresser_r.insert(0, config.get("dresser_r", ""))
        entry_shape_num.insert(0, config.get("shape_num", ""))
        entry_save_path.insert(0, config.get("save_path", ""))

# 关闭 ui 时强制关闭程序
def on_closing():
    root.destroy()
    sys.exit()

# 动画相关函数
def update_progress():
    while animation_running:
        progress_bar.step(1)  # 每次递增一步
        time.sleep(0.1)  # 控制进度条更新速度

def start_animation():
    global animation_running
    animation_running = True
    progress_var.set(0)  # 确保进度条从0开始
    progress_bar.pack(pady=10)  # 显示进度条
    progress_bar.start()  # 启动进度条动画
    root.update_idletasks()  # 强制刷新界面

def stop_animation():
    global animation_running
    animation_running = False
    progress_bar.stop()  # 停止进度条动画
    progress_bar.pack_forget()  # 隐藏进度条

def login():
    username = username_entry.get()
    password = password_entry.get()
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        login_window.destroy()
        show_main_window()
    else:
        messagebox.showerror("登录失败", "用户名或密码错误")

def show_main_window():
    global root, frame1, frame2, progress_bar, progress_var
    root = ctk.CTk()
    root.title("干涉磨削砂轮修整软件")
    root.geometry("800x600")  # 设置固定窗口大小

    # 创建主框架
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    title_label = ctk.CTkLabel(main_frame, text="参数配置", font=("Helvetica", 18))
    title_label.pack(pady=10)

    # 创建切换框架和按钮的容器
    tab_frame = ctk.CTkFrame(main_frame)
    tab_frame.pack(side=tk.TOP, fill=tk.X)

    # 创建内容框架
    content_frame = ctk.CTkFrame(main_frame)
    content_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    # 创建 frame1 和 frame2 放在 content_frame 中，并设置为 grid 布局
    frame1 = ctk.CTkFrame(content_frame)
    frame1.grid(row=0, column=0, sticky="nsew")

    frame2 = ctk.CTkFrame(content_frame)
    frame2.grid(row=0, column=0, sticky="nsew")

    content_frame.grid_rowconfigure(0, weight=1)
    content_frame.grid_columnconfigure(0, weight=1)

    # 初始显示 frame1
    frame1.tkraise()

    # 创建选项卡切换按钮
    tab1_button = ctk.CTkButton(tab_frame, text="参数1", command=lambda: frame1.tkraise())
    tab1_button.pack(side=tk.LEFT, padx=10, pady=10)

    tab2_button = ctk.CTkButton(tab_frame, text="参数2", command=lambda: frame2.tkraise())
    tab2_button.pack(side=tk.LEFT, padx=10, pady=10)

    # frame1中的控件
    ctk.CTkLabel(frame1, text="工件中径:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    global entry_mid_dia
    entry_mid_dia = ctk.CTkEntry(frame1)
    entry_mid_dia.grid(row=0, column=1, padx=10, pady=10)

    ctk.CTkLabel(frame1, text="导程:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    global entry_work_lead
    entry_work_lead = ctk.CTkEntry(frame1)
    entry_work_lead.grid(row=1, column=1, padx=10, pady=10)

    ctk.CTkLabel(frame1, text="砂轮杆偏移工件中心最大距离:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    global entry_gan_distance_max
    entry_gan_distance_max = ctk.CTkEntry(frame1)
    entry_gan_distance_max.grid(row=2, column=1, padx=10, pady=10)

    ctk.CTkLabel(frame1, text="砂轮杆偏移工件中心最小距离:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    global entry_gan_distance_min
    entry_gan_distance_min = ctk.CTkEntry(frame1)
    entry_gan_distance_min.grid(row=3, column=1, padx=10, pady=10)

    ctk.CTkLabel(frame1, text="砂轮直径步进:").grid(row=4, column=0, padx=10, pady=10, sticky="w")
    global entry_step_dia
    entry_step_dia = ctk.CTkEntry(frame1)
    entry_step_dia.grid(row=4, column=1, padx=10, pady=10)

    ctk.CTkLabel(frame1, text="砂轮安装角:").grid(row=5, column=0, padx=10, pady=10, sticky="w")
    global entry_gan_angle
    entry_gan_angle = ctk.CTkEntry(frame1)
    entry_gan_angle.grid(row=5, column=1, padx=10, pady=10)

    ctk.CTkLabel(frame1, text="dxf 文件地址:").grid(row=6, column=0, padx=10, pady=10, sticky="w")
    global entry_dxf_file
    entry_dxf_file = ctk.CTkEntry(frame1)
    entry_dxf_file.grid(row=6, column=1, padx=10, pady=10)
    select_dxf_button = ctk.CTkButton(frame1, text="选择文件", command=select_dxf_file)
    select_dxf_button.grid(row=6, column=2, padx=10, pady=10)

    # frame2中的控件
    ctk.CTkLabel(frame2, text="滚轮圆弧半径:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    global entry_dresser_r
    entry_dresser_r = ctk.CTkEntry(frame2)
    entry_dresser_r.grid(row=0, column=1, padx=10, pady=10)

    ctk.CTkLabel(frame2, text="最终曲线点密度:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    global entry_shape_num
    entry_shape_num = ctk.CTkEntry(frame2)
    entry_shape_num.grid(row=1, column=1, padx=10, pady=10)

    ctk.CTkLabel(frame2, text="输出程序路径:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    global entry_save_path
    entry_save_path = ctk.CTkEntry(frame2)
    entry_save_path.grid(row=2, column=1, padx=10, pady=10)
    select_save_path_button = ctk.CTkButton(frame2, text="选择路径", command=select_save_path)
    select_save_path_button.grid(row=2, column=2, padx=10, pady=10)

    # 创建提交按钮框架
    button_frame = ctk.CTkFrame(main_frame)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # 创建提交按钮
    global submit_button
    submit_button = ctk.CTkButton(button_frame, text="提交", command=on_submit)
    submit_button.pack(pady=10)

    # 创建进度条
    progress_var = tk.IntVar(value=0)
    global progress_bar
    progress_bar = ctk.CTkProgressBar(button_frame, variable=progress_var, mode='indeterminate')
    progress_bar.pack(pady=10)

    # 显示结果的标签
    global result
    result = tk.StringVar()
    result_label = ctk.CTkLabel(button_frame, textvariable=result, wraplength=400)
    result_label.pack(pady=10)

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
login_window = ctk.CTk()
login_window.title("登录")

login_frame = ctk.CTkFrame(login_window)
login_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

title_label = ctk.CTkLabel(login_frame, text="用户登录", font=("Helvetica", 16))
title_label.pack(pady=10)

username_label = ctk.CTkLabel(login_frame, text="用户名:")
username_label.pack(fill=tk.X, pady=5)
username_entry = ctk.CTkEntry(login_frame)
username_entry.pack(fill=tk.X, pady=5)

password_label = ctk.CTkLabel(login_frame, text="密码:")
password_label.pack(fill=tk.X, pady=5)
password_entry = ctk.CTkEntry(login_frame, show="*")
password_entry.pack(fill=tk.X, pady=5)

login_button = ctk.CTkButton(login_frame, text="登录", command=login)
login_button.pack(pady=10)

# 运行登录窗口主循环
login_window.mainloop()
