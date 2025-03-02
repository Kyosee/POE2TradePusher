import tkinter as tk
from tkinter import messagebox
import win32gui
import win32con

def show_message(title, message, level="info"):
    """统一的消息框显示函数"""
    if level == "error":
        messagebox.showerror(title, message)
    elif level == "warning":
        messagebox.showwarning(title, message)
    else:
        messagebox.showinfo(title, message)

def ask_yes_no(title, message):
    """统一的确认对话框函数"""
    return messagebox.askyesno(title, message)

def find_window(window_name):
    """查找窗口句柄"""
    result = [None]
    
    def callback(hwnd, _):
        if win32gui.GetWindowText(hwnd) == window_name:
            result[0] = hwnd
            return False
        return True
    
    try:
        win32gui.EnumWindows(callback, None)
    except:
        pass
    
    return result[0]

def switch_to_window(window_name):
    """切换到指定窗口"""
    hwnd = find_window(window_name)
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return True
    return False

class ConfigMixin:
    """配置管理混入类"""
    def get_config_data(self):
        """获取配置数据"""
        raise NotImplementedError

    def set_config_data(self, data):
        """设置配置数据"""
        raise NotImplementedError

    def validate_config(self):
        """验证配置数据"""
        raise NotImplementedError

class LoggingMixin:
    """日志管理混入类"""
    def __init__(self, log_callback=None, status_callback=None):
        self.log_callback = log_callback
        self.status_callback = status_callback

    def log_message(self, message, level="INFO"):
        """记录日志消息"""
        if self.log_callback:
            self.log_callback(message, level)

    def update_status(self, message):
        """更新状态栏"""
        if self.status_callback:
            self.status_callback(message)
