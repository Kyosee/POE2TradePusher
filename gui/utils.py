from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
import win32gui
import win32con

def show_message(title, message, level="info"):
    """统一的消息框显示函数"""
    msg_box = QMessageBox()
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if level == "error":
        msg_box.setIcon(QMessageBox.Critical)
    elif level == "warning":
        msg_box.setIcon(QMessageBox.Warning)
    else:
        msg_box.setIcon(QMessageBox.Information)
    
    # 获取活动窗口并检查是否有置顶标志
    from PySide6.QtWidgets import QApplication
    active_window = QApplication.activeWindow()
    if active_window and active_window.windowFlags() & Qt.WindowStaysOnTopHint:
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
        
    msg_box.exec_()

def ask_yes_no(title, message):
    """统一的确认对话框函数"""
    msg_box = QMessageBox(QMessageBox.Question, title, message, QMessageBox.Yes | QMessageBox.No)
    
    # 获取活动窗口并检查是否有置顶标志
    from PySide6.QtWidgets import QApplication
    active_window = QApplication.activeWindow()
    if active_window and active_window.windowFlags() & Qt.WindowStaysOnTopHint:
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
    
    reply = msg_box.exec_()
    return reply == QMessageBox.Yes

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
    def init_config(self):
        """初始化配置对象"""
        from core.config import Config
        self.config = Config()

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
        """
        初始化日志混入类
        :param log_callback: 日志回调函数，接收消息和级别两个参数
        :param status_callback: 状态栏回调函数，接收消息参数
        """
        self.log_callback = log_callback
        self.status_callback = status_callback

    def log_message(self, message, level="INFO"):
        """
        记录日志消息
        :param message: 日志消息
        :param level: 日志级别，可选值：INFO, DEBUG, WARN, ERROR, ALERT
        """
        if self.log_callback:
            self.log_callback(message, level)

    def update_status(self, message):
        """
        更新状态栏
        :param message: 状态消息
        """
        if self.status_callback:
            self.status_callback(message)
