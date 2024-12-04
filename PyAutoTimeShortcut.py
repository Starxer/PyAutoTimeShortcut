import json
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import pyautogui
from pywinauto import Desktop

# 读取设置中保存的快捷键，如果没有就创建设置文件且使用默认值
def load_settings():
    global interval_entry, counts_entry, hotkey_entry
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            interval_entry.insert(0, str(settings['interval']))
            counts_entry.insert(0, str(settings['counts']))
            # hotkey_entry.delete(0, tk.END)
            hotkey_entry.insert(0, settings['hotkey'])
    except FileNotFoundError:
        settings = {
            "interval": 1,
            "counts": 1,
            "hotkey": "ctrl+shift+esc"
        }
        # 初始化输入框默认值
        interval_entry.insert(0, str(settings['interval']))
        counts_entry.insert(0, str(settings['counts']))
        hotkey_entry.insert(0, settings['hotkey'])
        # 保存默认设置
        save_settings()
    return settings


# 保存设置
def save_settings(quiet=True):
    global interval_entry, counts_entry, hotkey_entry
    with open('settings.json', 'w') as f:
        json.dump({
            "interval": float(interval_entry.get()),
            "counts": int(counts_entry.get()) if counts_entry.get().strip() != '' else None,
            "hotkey": hotkey_entry.get()
        }, f)
    if not quiet:
        messagebox.showinfo("保存成功", "设置已保存")


# 定义一个全局变量来控制线程
stop_event = threading.Event()


def convert_seconds_to_hms(seconds):
    seconds = round(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# 定义开始计时器的函数，获取用户输入的间隔时间、次数和快捷键，然后调用press_hotkey函数
def start_timer():
    global stop_event, interval_entry, counts_entry, hotkey_entry, stop_button, start_button, status_label
    stop_event.clear()  # 清除之前的事件
    try:
        interval = float(interval_entry.get())
        counts = int(counts_entry.get()) if counts_entry.get().strip() != '' else None
        hotkey = hotkey_entry.get()
        if interval <= 0:
            raise ValueError("间隔时间必须大于0")
        if counts is not None and counts <= 0:
            raise ValueError("次数必须大于0或留空")
        if not hotkey:
            raise ValueError("快捷键不能为空")
        # 保存默认设置
        save_settings()
        # 启动一个新线程来执行定时任务
        threading.Thread(target=press_hotkey, args=(interval, counts, hotkey)).start()
    except ValueError as e:
        messagebox.showerror("输入错误", str(e))


# 定义按下快捷键的函数，根据用户输入的间隔时间和次数循环执行
def press_hotkey(interval, counts, hotkey):
    global stop_event, treeview_status, start_button, stop_button, status_label
    count = 0
    # 更新状态
    start_button.config(state=tk.DISABLED, bg="yellow")
    status_label.config(text="运行中...", fg="green")
    stop_button.config(state=tk.NORMAL)

    # tkinter最小化窗口
    # root.iconify()

    while counts is None or count < counts:
        if stop_event.is_set():
            break
        # pyautogui聚焦到指定程序
        focus_window()
        # 执行快捷键
        pyautogui.hotkey(*hotkey.split('+'))
        count += 1
        if counts is not None:
            treeview_status.insert("", 0, values=(count, convert_seconds_to_hms(count * interval),
                                                  convert_seconds_to_hms((counts - count) * interval),
                                                  convert_seconds_to_hms(counts * interval)))
        else:
            treeview_status.insert("", 0, values=(count, convert_seconds_to_hms(count * interval),
                                                  "无限循环", "无限循环"))
        time.sleep(interval)
    # 任务结束后，更新状态
    stop_button.config(state=tk.DISABLED)
    start_button.config(state=tk.NORMAL, bg="light grey")
    status_label.config(text="已停止", fg="red")


# 定义停止任务的函数
def stop_task():
    global stop_event
    stop_event.set()


def focus_window():
    # 将窗口带到前台并聚焦
    global windows, lock_combobox
    if lock_combobox.current() == -1 or lock_combobox.current() == 0:
        return
    w = windows[lock_combobox.current() - 1]
    w.set_focus()


# 创建主窗口
root = tk.Tk()
root.title("定时快捷键")

frame_settings = ttk.LabelFrame(root, text="设置", padding="10")
frame_settings.pack(anchor='w', fill=tk.BOTH, expand=True)

frame_settings_left = ttk.Frame(frame_settings, padding="10")
frame_settings_left.pack(side='left')

frame_settings_right = ttk.Frame(frame_settings, padding="10")
frame_settings_right.pack(side='right', fill=tk.BOTH, expand=True)

# 创建输入间隔时间的文本框
interval_label = tk.Label(frame_settings_left, text="间隔(秒):")
interval_label.pack(anchor='w')

interval_entry = tk.Entry(frame_settings_right)
# interval_entry.insert(0, "3")
# 设置输入框自适应大小
interval_entry.pack(fill=tk.BOTH, expand=True)

# 创建输入次数的文本框
counts_label = tk.Label(frame_settings_left, text="次数(留空为无限循环):")
counts_label.pack(anchor='w')

counts_entry = tk.Entry(frame_settings_right)
counts_entry.pack(fill=tk.BOTH, expand=True)

# 创建输入快捷键的文本框
hotkey_label = tk.Label(frame_settings_left, text="快捷键(例如:Ctrl+Shift+Esc):")
hotkey_label.pack(anchor='w')

hotkey_entry = tk.Entry(frame_settings_right)
# hotkey_entry.insert(0, "win")
hotkey_entry.pack(fill=tk.BOTH, expand=True)

# 创建锁定窗口下拉框combobox

lock_label = tk.Label(frame_settings_left, text="锁定窗口(聚焦到指定窗口):")
lock_label.pack(anchor='w')

# 获取所有顶层窗口
windows = Desktop(backend="uia").windows()
windows_name = [w.window_text() for w in windows]
windows_name.insert(0, "None")

# 创建下拉框
lock_combobox = ttk.Combobox(frame_settings_right)
lock_combobox['values'] = windows_name
lock_combobox.current(0)

lock_combobox.pack(fill=tk.BOTH, expand=True)
lock_combobox.config(width=50)

frame_button = ttk.LabelFrame(root, text="控制", padding="10")
frame_button.pack(fill=tk.BOTH, expand=True)

# 创建停止任务的按钮
stop_button = tk.Button(frame_button, text="停止", command=stop_task, bd=3, relief=tk.GROOVE, bg="light grey")
stop_button.config(state=tk.DISABLED)
stop_button.pack(side='left', fill=tk.BOTH, expand=True)

# 创建启动任务的按钮
start_button = tk.Button(frame_button, text="启动", command=start_timer, bd=3, relief=tk.GROOVE, bg="light grey")
start_button.pack(side='left', fill=tk.BOTH, expand=True)

frame_status = ttk.LabelFrame(root, text="状态", padding="10")
frame_status.pack(anchor='w', fill=tk.BOTH, expand=True)

# 创建运行状态标签
status_label = tk.Label(frame_status, text="未启动", bd=3, width=10)
status_label.pack(side='left')

# 创建一个表格
treeview_status = ttk.Treeview(frame_status, columns=("完成次数", "已用时间", "剩余时间", "总时间"), show="headings",
                               height=1)
treeview_status.pack(side='left', fill=tk.BOTH, expand=True, padx=5, pady=5)
treeview_status.heading("完成次数", text="完成次数")
treeview_status.heading("已用时间", text="已用时间")
treeview_status.heading("剩余时间", text="剩余时间")
treeview_status.heading("总时间", text="总时间")
treeview_status.column("完成次数", anchor="center")
treeview_status.column("已用时间", anchor="center")
treeview_status.column("剩余时间", anchor="center")
treeview_status.column("总时间", anchor="center")
treeview_status.insert("", "end", values=(0, *([convert_seconds_to_hms(0)] * 3)), )

# ---------------------------------------------------------
# def print_combo():
#     print(lock_combobox.get())
#     print(lock_combobox.current())
#
#
# # 测试按钮，用于print下拉框的选项
# test_button = tk.Button(root, text="Test", command=print_combo)
# test_button.grid(row=9, column=0)
# -----------------------------------------------------------

# 载入设置
load_settings()

# 启动Tkinter事件循环
root.mainloop()

# 打包为exe程序
# pyinstaller -wF time_key_gui.py
