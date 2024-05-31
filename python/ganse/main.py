from library.main_cycle import main_cycle
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import json
import threading
import sys
import time
import platform
import subprocess
import requests
import math

# 配置文件
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".InterferenceGrindingDressing.json")

LOCAL_ADMIN_USERNAME = "marco"
LOCAL_ADMIN_PASSWORD = "464116963"
SERVER_URL = "https://your-server-url.com/api/auth"  # 替换为你的服务器URL

# 加载语言文件
def load_languages():
    with open("languages.json", "r", encoding="utf-8") as file:
        return json.load(file)

languages = load_languages()

# 定义全局变量
current_language_code = "zh"
current_language = languages[current_language_code]

class CTkMessageBox(ctk.CTkToplevel):
    global current_language
    def __init__(self, master, title=current_language["message"], message=""):
        super().__init__(master)
        self.title(title)
        self.geometry("300x150")
        center_window(self, 300, 150)

        self.label = ctk.CTkLabel(self, text=message, font=FONT)
        self.label.pack(pady=20)

        self.button = ctk.CTkButton(self, text=current_language["submit"], command=self.destroy, font=FONT)
        self.button.pack(pady=10)

        self.transient(master)
        self.grab_set()
        master.wait_window(self)

def update_ui_language():
    switch_lang_button.configure(text="Switch to English" if current_language_code == "zh" else "切换到中文")
    title_label.configure(text=current_language["parameter_configuration"])
    submit_button.configure(text=current_language["generate_code"])
    
    # 更新选项卡
    create_tabs()

def switch_language(lang_code):
    global current_language_code, current_language

    # 先删除之前的选项卡
    tabview.delete(current_language["tabview_1"])
    tabview.delete(current_language["tabview_2"])

    current_language_code = lang_code
    current_language = languages[lang_code]
    update_ui_language()

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

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def on_submit():
    global current_language
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
            CTkMessageBox(root, title=current_language["invalid_input_title"], message=current_language["invalid_input_text"])
        finally:
            # 操作完成后启用提交按钮并停止进度条
            submit_button.configure(state=tk.NORMAL, fg_color=None)  # 启用提交按钮并恢复颜色
            stop_animation()

    # 开始提交操作时禁用提交按钮
    submit_button.configure(state=tk.DISABLED, fg_color="grey")  # 禁用提交按钮并改为灰色
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

def remote_validate(username, password):
    try:
        response = requests.post(SERVER_URL, json={"username": username, "password": password})
        response_data = response.json()
        return response_data.get("status") == "success"
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return False

def login():
    global current_language
    username = username_entry.get()
    password = password_entry.get()

    if username == LOCAL_ADMIN_USERNAME and password == LOCAL_ADMIN_PASSWORD:
        login_window.destroy()
        show_main_window()
    elif remote_validate(username, password):
        login_window.destroy()
        show_main_window()
    else:
        CTkMessageBox(login_window, title=current_language["login_failed_title"], message=current_language["login_failed_text"])

# 验证是否输入值是正实数
def validate_positive_float(value_if_allowed):
    if value_if_allowed == "":
        return True
    try:
        value = float(value_if_allowed)
        return value > 0
    except ValueError:
        return False

# 验证输入值是否是正整数
def validate_positive_int(value_if_allowed):
    if value_if_allowed == "":
        return True
    try:
        value = int(value_if_allowed)
        return value > 0
    except ValueError:
        return False

def update_angle_result(*args):
    try:
        mid_dia_str = entry_mid_dia.get()
        work_lead_str = entry_work_lead.get()

        mid_dia = float(mid_dia_str) if mid_dia_str else 0
        work_lead = float(work_lead_str) if work_lead_str else 0

        if mid_dia > 0 and work_lead >= 0:
            angle = math.degrees(math.atan(work_lead / (math.pi * mid_dia)))
            angle_result_label.configure(text=f"{angle:.2f}°")
        else:
            angle_result_label.configure(text="")
    except ValueError:
        angle_result_label.configure(text="")

# 设置全局字体变量
if platform.system() == "Windows":
    FONT = ("Microsoft YaHei", 14)
elif platform.system() == "Darwin":
    FONT = ("PingFang SC", 14)
else:
    FONT = ("WenQuanYi Zen Hei", 14)

def create_tabs():
    global tabview, entry_mid_dia, entry_work_lead, entry_gan_distance_max, entry_gan_distance_min, entry_step_dia, entry_gan_angle, entry_dxf_file, entry_dresser_r, entry_shape_num, entry_save_path

    tabview.add(current_language["tabview_1"])
    tabview.add(current_language["tabview_2"])

    # 参数1中的控件
    tab1 = tabview.tab(current_language["tabview_1"])
    ctk.CTkLabel(tab1, text=current_language["workpiece_diameter"], font=FONT).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    global entry_mid_dia
    entry_mid_dia = ctk.CTkEntry(tab1, validate="key", validatecommand=vcmd_float)
    entry_mid_dia.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    entry_mid_dia.bind("<FocusOut>", update_angle_result)

    ctk.CTkLabel(tab1, text=current_language["lead"], font=FONT).grid(row=1, column=0, padx=10, pady=10, sticky="w")
    global entry_work_lead
    entry_work_lead = ctk.CTkEntry(tab1, validate="key", validatecommand=vcmd_float)
    entry_work_lead.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    entry_work_lead.bind("<FocusOut>", update_angle_result)

    ctk.CTkLabel(tab1, text=current_language["max_distance"], font=FONT).grid(row=2, column=0, padx=10, pady=10, sticky="w")
    global entry_gan_distance_max
    entry_gan_distance_max = ctk.CTkEntry(tab1, validate="key", validatecommand=vcmd_float)
    entry_gan_distance_max.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

    ctk.CTkLabel(tab1, text=current_language["min_distance"], font=FONT).grid(row=3, column=0, padx=10, pady=10, sticky="w")
    global entry_gan_distance_min
    entry_gan_distance_min = ctk.CTkEntry(tab1, validate="key", validatecommand=vcmd_float)
    entry_gan_distance_min.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

    ctk.CTkLabel(tab1, text=current_language["step_diameter"], font=FONT).grid(row=4, column=0, padx=10, pady=10, sticky="w")
    global entry_step_dia
    entry_step_dia = ctk.CTkEntry(tab1, validate="key", validatecommand=vcmd_float)
    entry_step_dia.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

    ctk.CTkLabel(tab1, text=current_language["wheel_angle"], font=FONT).grid(row=5, column=0, padx=10, pady=10, sticky="w")
    global entry_gan_angle
    entry_gan_angle = ctk.CTkEntry(tab1, validate="key", validatecommand=vcmd_float)
    entry_gan_angle.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

    # 添加一个用于显示角度结果的 Label
    global angle_result_label
    angle_result_label = ctk.CTkLabel(tab1, text="", font=FONT)
    angle_result_label.grid(row=5, column=2, padx=10, pady=10, sticky="w")

    ctk.CTkLabel(tab1, text=current_language["dxf_file_path"], font=FONT).grid(row=6, column=0, padx=10, pady=10, sticky="w")
    global entry_dxf_file
    entry_dxf_file = ctk.CTkEntry(tab1)
    entry_dxf_file.grid(row=6, column=1, padx=10, pady=10, sticky="ew")
    select_dxf_button = ctk.CTkButton(tab1, text=current_language["choice_file"], command=select_dxf_file, font=FONT)
    select_dxf_button.grid(row=6, column=2, padx=10, pady=10)

    # 参数2中的控件
    tab2 = tabview.tab(current_language["tabview_2"])
    ctk.CTkLabel(tab2, text=current_language["wheel_radius"], font=FONT).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    global entry_dresser_r
    entry_dresser_r = ctk.CTkEntry(tab2, validate="key", validatecommand=vcmd_float)
    entry_dresser_r.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    ctk.CTkLabel(tab2, text=current_language["point_density"], font=FONT).grid(row=1, column=0, padx=10, pady=10, sticky="w")
    global entry_shape_num
    entry_shape_num = ctk.CTkEntry(tab2, validate="key", validatecommand=vcmd_int)
    entry_shape_num.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

    ctk.CTkLabel(tab2, text=current_language["output_path"], font=FONT).grid(row=2, column=0, padx=10, pady=10, sticky="w")
    global entry_save_path
    entry_save_path = ctk.CTkEntry(tab2)
    entry_save_path.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
    select_save_path_button = ctk.CTkButton(tab2, text=current_language["choice_path"], command=select_save_path, font=FONT)
    select_save_path_button.grid(row=2, column=2, padx=10, pady=10)

    # 添加空白标签来填充空白区域，使元素上下对齐
    for i in range(3, 7):
        ctk.CTkLabel(tab2, text="").grid(row=i, column=0, padx=10, pady=10, sticky="w")

    # 加载保存的参数
    load_saved_values()

    # 计算螺旋升角
    update_angle_result()

    # 确保选项卡中的元素自适应窗体左右和上下大小
    tab1.grid_columnconfigure(1, weight=1)
    tab1.grid_rowconfigure(0, weight=1)
    tab1.grid_rowconfigure(1, weight=1)
    tab1.grid_rowconfigure(2, weight=1)
    tab1.grid_rowconfigure(3, weight=1)
    tab1.grid_rowconfigure(4, weight=1)
    tab1.grid_rowconfigure(5, weight=1)
    tab1.grid_rowconfigure(6, weight=1)

    tab2.grid_columnconfigure(1, weight=1)
    tab2.grid_rowconfigure(0, weight=1)
    tab2.grid_rowconfigure(1, weight=1)
    tab2.grid_rowconfigure(2, weight=1)
    tab2.grid_rowconfigure(3, weight=1)
    tab2.grid_rowconfigure(4, weight=1)
    tab2.grid_rowconfigure(5, weight=1)
    tab2.grid_rowconfigure(6, weight=1)

# 在主窗口中使用 grid 布局管理器，并配置列和行的 weight 属性
def show_main_window():
    global root, progress_bar, progress_var, current_language, switch_lang_button, title_label, tabview, vcmd_float, vcmd_int
    root = ctk.CTk()
    root.title(current_language["software_name"])
    center_window(root, 800, 600)  # 居中显示窗口

    vcmd_float = (root.register(validate_positive_float), "%P")
    vcmd_int = (root.register(validate_positive_int), "%P")

    # 创建主框架
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    # 创建一个用于标题的框架
    title_frame = ctk.CTkFrame(main_frame)
    title_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

    title_label = ctk.CTkLabel(title_frame, text=current_language["parameter_configuration"], font=FONT)
    title_label.pack(side=tk.LEFT, expand=True)

    # 语言切换按钮放在另一个框架
    switch_lang_button_frame = ctk.CTkFrame(main_frame)
    switch_lang_button_frame.grid(row=0, column=2, padx=10, pady=10, sticky="e")

    switch_lang_button = ctk.CTkButton(switch_lang_button_frame, text="Switch to English" if current_language_code == "zh" else "切换到中文", command=lambda: switch_language("en" if current_language_code == "zh" else "zh"))
    switch_lang_button.pack(side=tk.RIGHT)

    # 创建选项卡框架
    tab_frame = ctk.CTkFrame(main_frame)
    tab_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")

    # 创建选项卡视图
    tabview = ctk.CTkTabview(tab_frame)
    tabview.pack(expand=True, fill=tk.BOTH)

    # 创建选项卡
    create_tabs()

    # 创建提交按钮框架
    button_frame = ctk.CTkFrame(main_frame)
    button_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")

    # 创建提交按钮
    global submit_button
    submit_button = ctk.CTkButton(button_frame, text=current_language["generate_code"], command=on_submit, font=FONT)
    submit_button.pack(pady=10)

    # 创建进度条
    progress_var = tk.IntVar(value=0)
    global progress_bar
    progress_bar = ctk.CTkProgressBar(button_frame, variable=progress_var, mode='indeterminate')
    progress_bar.pack(pady=10)

    # 全局变量用于控制动画
    global animation_running
    animation_running = False

    # 绑定关闭事件
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # 确保布局不变
    main_frame.grid_rowconfigure(1, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_rowconfigure(2, weight=0)

    # 运行主循环
    root.mainloop()

# 优化后的登录窗口
login_window = ctk.CTk()
login_window.title(current_language["login"])
center_window(login_window, 350, 250)  # 居中显示窗口

login_frame = ctk.CTkFrame(login_window)
login_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

title_label = ctk.CTkLabel(login_frame, text=current_language["login"], font=FONT)
title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="ew")

username_label = ctk.CTkLabel(login_frame, text=current_language["username"], font=FONT)
username_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
username_entry = ctk.CTkEntry(login_frame)
username_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
username_entry.focus_set()  # 默认选中用户名输入栏

password_label = ctk.CTkLabel(login_frame, text=current_language["password"], font=FONT)
password_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
password_entry = ctk.CTkEntry(login_frame, show="*")
password_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

login_button = ctk.CTkButton(login_frame, text=current_language["login"], command=login, font=FONT)
login_button.grid(row=3, column=0, columnspan=2, pady=20)

# 配置列的 weight，使其自适应窗体左右大小
login_frame.grid_columnconfigure(0, weight=1)
login_frame.grid_columnconfigure(1, weight=1)
# 配置行的 weight，使其自适应窗体上下大小
login_frame.grid_rowconfigure(1, weight=1)
login_frame.grid_rowconfigure(2, weight=1)

# 绑定回车键事件到登录按钮
login_window.bind("<Return>", lambda event: login())

# 运行登录窗口主循环
login_window.mainloop()
