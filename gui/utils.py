from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt
import win32gui
import win32con
from .widgets.toast import show_toast, Toast

def show_message(title, message, type_="info", parent=None):
    """显示消息提示"""
    # 使用新的Toast组件替代QMessageBox
    if not parent and QApplication.activeWindow():
        parent = QApplication.activeWindow()
    
    # 映射消息类型到Toast类型
    toast_type_map = {
        "info": Toast.INFO,
        "warning": Toast.WARNING,
        "error": Toast.ERROR,
        "success": Toast.SUCCESS
    }
    toast_type = toast_type_map.get(type_, Toast.INFO)
    
    # 显示Toast提示
    show_toast(parent, title, message, toast_type)

def ask_yes_no(title, question):
    """显示是否确认对话框"""
    msg_box = QMessageBox()
    msg_box.setWindowTitle(title)
    msg_box.setText(question)
    msg_box.setIcon(QMessageBox.Question)
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.No)
    
    return msg_box.exec() == QMessageBox.Yes

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

def switch_to_window(window_name, current_widget=None):
    """
    切换到指定名称的窗口
    
    Args:
        window_name: 窗口名称
        current_widget: 当前小部件，用于显示Toast
        
    Returns:
        bool: 切换是否成功
    """
    if not window_name:
        if current_widget:
            show_toast(current_widget, "错误", "窗口名称不能为空", Toast.ERROR)
        return False
        
    try:
        import win32gui
        import win32con

        # 查找窗口
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd == 0:
            if current_widget:
                show_toast(current_widget, "错误", f"找不到窗口: {window_name}", Toast.ERROR)
            return False

        # 如果窗口最小化，则恢复它
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
        # 将窗口置于前台
        win32gui.SetForegroundWindow(hwnd)
        
        # 显示成功Toast
        if current_widget:
            show_toast(current_widget, "成功", f"已切换到窗口: {window_name}", Toast.SUCCESS)
            
        return True
    except Exception as e:
        if current_widget:
            show_toast(current_widget, "错误", f"切换窗口失败: {str(e)}", Toast.ERROR)
        return False

class ConfigMixin:
    """配置操作混入类"""
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
