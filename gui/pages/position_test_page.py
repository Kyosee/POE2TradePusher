from .recognition_base_page import RecognitionBasePage
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
from core.process_modules.take_out_item import TakeOutItemModule

class PositionTestPage(RecognitionBasePage):
    """定位测试页面 - 仓库类型识别和格子定位"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        super().__init__(master, callback_log, callback_status, main_window)
        # 创建取出模块实例
        self.take_out_module = TakeOutItemModule()
        
    def _update_preview(self, cv_image):
        """更新预览图像"""
        try:
            # 转换为PIL格式并更新预览
            pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
            photo = ImageTk.PhotoImage(pil_image)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            self._add_log(f"更新预览图像失败: {str(e)}", "ERROR")
        
    def _create_search_frame(self):
        """创建搜索栏"""
        super()._create_search_frame()
        
        # 修改识别按钮文本
        self.recognize_btn.configure(text="识别并取出")
        
        # 在搜索框架中创建输入区域
        search_frame = self.recognize_btn.master.master.master  # 获取LabelFrame
        self.input_frame = ttk.Frame(search_frame)
        self.input_frame.pack(fill=tk.X, padx=6, pady=6)
        
        # 横向和纵向位置输入框
        coord_frame = ttk.Frame(self.input_frame)
        coord_frame.pack(fill=tk.X, pady=6)
        
        # 横向位置
        pos1_frame = ttk.Frame(coord_frame)
        pos1_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(pos1_frame, text="横向位置:").pack(side=tk.LEFT)
        self.position1_var = tk.StringVar(value="1")
        ttk.Entry(pos1_frame, textvariable=self.position1_var, width=10).pack(side=tk.LEFT)
        
        # 纵向位置
        pos2_frame = ttk.Frame(coord_frame)
        pos2_frame.pack(side=tk.LEFT)
        ttk.Label(pos2_frame, text="纵向位置:").pack(side=tk.LEFT)
        self.position2_var = tk.StringVar(value="1")
        ttk.Entry(pos2_frame, textvariable=self.position2_var, width=10).pack(side=tk.LEFT)
        
    def _do_recognition(self):
        """执行识别并取出装备"""
        try:
            # 获取输入的坐标值
            p1_num = int(self.position1_var.get())
            p2_num = int(self.position2_var.get())
            
            # 执行取出装备模块（启用预览）
            result = self.take_out_module.process(
                p1_num=p1_num,
                p2_num=p2_num,
                preview_callback=self._update_preview
            )
            
            if result is not False:
                self._add_log(f"✅ 已成功取出装备：横向{p1_num}格，纵向{p2_num}格")
                self.update_status("✅ 识别成功")
            else:
                self._add_log("❌ 取出装备失败", "ERROR")
                self.update_status("❌ 识别失败")
                
        except ValueError as e:
            self._add_log("❌ 请输入有效的位置数值", "ERROR")
            self.update_status("❌ 输入错误")
        except Exception as e:
            self._add_log(f"识别过程出错: {str(e)}", "ERROR")
            self.update_status("❌ 识别失败")
