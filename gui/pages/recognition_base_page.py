import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab, ImageTk, Image
import win32gui
import win32con
import win32api
import cv2
import numpy as np
import os
from pathlib import Path
from ..utils import LoggingMixin, find_window

class RecognitionBasePage(ttk.Frame, LoggingMixin):
    """识别功能基类"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        ttk.Frame.__init__(self, master, style='Content.TFrame')
        LoggingMixin.__init__(self, callback_log, callback_status)
        self.main_window = main_window
        
        self.template_path = None
        self.template = None
        
        # 界面组件
        self._create_search_frame()
        self._create_preview_frame()
        self._create_log_frame()
        
    def _preprocess_image(self, image):
        """图像预处理以提高识别率"""
        # 转换为OpenCV格式
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
        self.recognize_btn.configure(text=f"🔍 识别{title}")
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
        search_frame = ttk.LabelFrame(self, text="识别设置")
        search_frame.pack(fill=tk.X, padx=12, pady=6)
        
        input_frame = ttk.Frame(search_frame)
        input_frame.pack(fill=tk.X, padx=6, pady=6)
        
        # 按钮框架
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side=tk.LEFT)
        
        self.recognize_btn = ttk.Button(
            btn_frame, 
            text="🔍 识别", 
            command=self._do_recognition,
            style='Control.TButton'
        )
        self.recognize_btn.pack(side=tk.LEFT, padx=3)
        
        refresh_btn = ttk.Button(
            btn_frame, 
            text="🔄 刷新", 
            command=self._refresh_preview,
            style='Control.TButton'
        )
        refresh_btn.pack(side=tk.LEFT, padx=3)
        
    def _create_preview_frame(self):
        """创建预览区域"""
        preview_frame = ttk.LabelFrame(self, text="截图预览")
        preview_frame.pack(fill=tk.BOTH, padx=12, pady=6)
        
        # 创建固定高度的预览容器
        preview_container = ttk.Frame(preview_frame, height=400)
        preview_container.pack(fill=tk.BOTH, padx=6, pady=6)
        preview_container.pack_propagate(False)  # 防止子组件改变容器大小
        
        self.preview_label = ttk.Label(preview_container)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
    def _create_log_frame(self):
        """创建日志区域"""
        log_frame = ttk.LabelFrame(self, text="识别日志")
        log_frame.pack(fill=tk.BOTH, padx=12, pady=6)
        
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD,
                               font=('微软雅黑', 9))
        self.log_text.pack(fill=tk.BOTH, padx=6, pady=6)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
    def _get_window_name(self):
        """获取游戏窗口名称"""
        default_name = "Path of Exile 2"
        try:
            if self.main_window and hasattr(self.main_window, 'basic_config_page'):
                window_name = self.main_window.basic_config_page.game_entry.get().strip()
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
            
            # 调整图像大小以适应预览区域
            preview_width = 800
            ratio = preview_width / image.width
            preview_height = int(image.height * ratio)
            image = image.resize((preview_width, preview_height), Image.LANCZOS)
            
            # 更新预览
            photo = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
            
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
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_message(message, level)
