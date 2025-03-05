from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QPushButton, QFrame, QTextEdit, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import win32gui
import win32con
import win32api
import cv2
import numpy as np
import os
from pathlib import Path
from PIL import ImageGrab, Image
from ..utils import LoggingMixin, find_window

class RecognitionBasePage(QWidget, LoggingMixin):
    """识别功能基类"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        super().__init__(master)
        LoggingMixin.__init__(self, callback_log, callback_status)
        self.main_window = main_window
        
        self.template_path = None
        self.template = None
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        # 创建界面组件
        self._create_search_frame()
        self._create_preview_frame()
        self._create_log_frame()
        
    def _preprocess_image(self, image):
        """图像预处理以提高识别率"""
        # 转换为OpenCV格式
        if isinstance(image, QImage):
            # 将QImage转换为numpy数组
            width = image.width()
            height = image.height()
            ptr = image.constBits()
            ptr.setsize(height * width * 4)  # 32位RGBA
            arr = np.array(ptr).reshape(height, width, 4)  # RGBA
            img = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        else:
            # 假设是PIL图像
            img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return img
        
    def set_template(self, template_path):
        """设置并加载新的模板图片"""
        if not os.path.exists(template_path):
            self.log_message(f"模板文件不存在: {template_path}", "ERROR")
            return False
            
        template = cv2.imread(template_path)
        if template is None:
            self.log_message(f"无法加载模板图片: {template_path}", "ERROR")
            return False
            
        self.template_path = template_path
        self.template = template
        
        # 更新页面标题
        template_name = os.path.basename(template_path).split('.')[0]
        title_map = {
            'stash_cn': '仓库',
            'grid': '仓位'
        }
        title = title_map.get(template_name, template_name)
        self.recognize_btn.setText(f"🔍 识别{title}")
        return True
        
    def validate_template(self):
        """验证模板图片是否有效"""
        if not self.template_path or not os.path.exists(self.template_path):
            self.log_message(f"模板文件不存在", "ERROR")
            return False
        if self.template is None:
            self.log_message("模板图片未加载", "ERROR")
            return False
        return True
        
    def _create_search_frame(self):
        """创建搜索栏"""
        # 创建框架
        search_frame = QFrame()
        search_frame.setProperty('class', 'card-frame')
        layout = QHBoxLayout(search_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("识别设置")
        title_label.setProperty('class', 'card-title')
        self.main_layout.addWidget(title_label)
        
        # 按钮容器
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)
        
        # 识别按钮
        self.recognize_btn = QPushButton("🔍 识别")
        self.recognize_btn.clicked.connect(self._do_recognition)
        self.recognize_btn.setProperty('class', 'normal-button')
        btn_layout.addWidget(self.recognize_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._refresh_preview)
        refresh_btn.setProperty('class', 'normal-button')
        btn_layout.addWidget(refresh_btn)
        
        layout.addWidget(btn_container)
        layout.addStretch()
        
        self.main_layout.addWidget(search_frame)
        
    def _create_preview_frame(self):
        """创建预览区域"""
        # 创建框架
        preview_frame = QFrame()
        preview_frame.setProperty('class', 'card-frame')
        layout = QVBoxLayout(preview_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("截图预览")
        title_label.setProperty('class', 'card-title')
        self.main_layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(400)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建预览标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        scroll_area.setWidget(self.preview_label)
        
        layout.addWidget(scroll_area)
        self.main_layout.addWidget(preview_frame)
        
    def _create_log_frame(self):
        """创建日志区域"""
        # 创建框架
        log_frame = QFrame()
        log_frame.setProperty('class', 'card-frame')
        layout = QVBoxLayout(log_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("识别日志")
        title_label.setProperty('class', 'card-title')
        self.main_layout.addWidget(title_label)
        
        # 日志文本区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #E6E7E8;
                border-radius: 2px;
                padding: 8px;
                font-family: 微软雅黑;
                font-size: 9pt;
            }
        """)
        
        layout.addWidget(self.log_text)
        self.main_layout.addWidget(log_frame)
        
    def _get_window_name(self):
        """获取游戏窗口名称"""
        default_name = "Path of Exile 2"
        try:
            if self.main_window and hasattr(self.main_window, 'basic_config_page'):
                window_name = self.main_window.basic_config_page.game_entry.text().strip()
                return window_name if window_name else default_name
        except Exception:
            pass
        return default_name
        
    def _find_window(self, window_name):
        """查找窗口句柄"""
        return find_window(window_name)
        
    def _get_window_rect(self, hwnd):
        """获取窗口区域"""
        return win32gui.GetWindowRect(hwnd)
        
    def _grab_screen(self, rect):
        """截取屏幕区域"""
        return ImageGrab.grab(rect)
        
    def _convert_to_cv(self, pil_image):
        """将PIL图像转换为OpenCV格式"""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
    def _pil_to_pixmap(self, pil_image, target_width=800):
        """将PIL图像转换为QPixmap"""
        # 计算缩放比例
        ratio = target_width / pil_image.width
        new_height = int(pil_image.height * ratio)
        
        # 调整图像大小
        pil_image = pil_image.resize((target_width, new_height), Image.LANCZOS)
        
        # 转换为QImage
        img_data = pil_image.convert("RGBA").tobytes()
        qimg = QImage(img_data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
        
        return QPixmap.fromImage(qimg)
        
    def _refresh_preview(self):
        """刷新预览图像"""
        try:
            # 获取游戏窗口名称
            window_name = self._get_window_name()
            
            # 查找窗口
            hwnd = self._find_window(window_name)
            if not hwnd:
                self._add_log(f"未找到游戏窗口: {window_name}", "WARNING")
                return False
                
            # 获取窗口区域并截图
            rect = self._get_window_rect(hwnd)
            image = self._grab_screen(rect)
            
            # 转换为QPixmap并更新预览
            pixmap = self._pil_to_pixmap(image)
            self.preview_label.setPixmap(pixmap)
            
            self.update_status("✅ 预览已更新")
            return True
            
        except Exception as e:
            self._add_log(f"刷新预览失败: {str(e)}", "ERROR")
            return False
            
    def _do_recognition(self):
        """执行识别（由子类重写）"""
        raise NotImplementedError("子类必须实现此方法")
            
    def _add_log(self, message, level="INFO"):
        """添加日志"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        self.log_message(message, level)
