from abc import ABC, abstractmethod
import logging
import sys
import os

# 添加项目根目录到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入Toast组件
try:
    from gui.widgets.toast import show_toast, Toast
    HAS_TOAST = True
except ImportError:
    HAS_TOAST = False

class ProcessModule(ABC):
    """流程模块基类"""
    
    def __init__(self):
        """初始化基类，设置日志记录器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # 重写error方法，添加Toast提示
        self._original_error = self.logger.error
        self.logger.error = self._error_with_toast
        
    def _error_with_toast(self, msg, *args, **kwargs):
        """带Toast提示的错误日志方法"""
        # 调用原始的error方法记录日志
        self._original_error(msg, *args, **kwargs)
        
        # 如果Toast组件可用，显示Toast提示
        if HAS_TOAST:
            # 获取主窗口实例（如果存在）
            from PySide6.QtWidgets import QApplication
            parent = None
            if QApplication.instance() and QApplication.activeWindow():
                parent = QApplication.activeWindow()
            
            # 显示Toast提示
            show_toast(parent, "错误", str(msg), Toast.ERROR)

    @abstractmethod
    def name(self) -> str:
        """模块名称"""
        pass

    @abstractmethod
    def description(self) -> str:
        """模块描述"""
        pass
        
    @abstractmethod
    def run(self, **kwargs):
        """
        运行模块
        
        参数：
            preview_enabled (bool): 是否启用预览功能，默认为 False
            **kwargs: 其他模块特定参数
        """
        pass
