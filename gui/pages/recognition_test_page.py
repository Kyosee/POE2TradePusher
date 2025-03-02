import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import ImageGrab, ImageTk, Image
import win32gui
import win32con
import win32api
import cv2
import numpy as np
import os
from pathlib import Path

class RecognitionTestPage(ttk.Frame):
    """识别测试页面"""
    def __init__(self, parent, log_callback, status_callback, main_window=None):
        super().__init__(parent)
        self.log_callback = log_callback
        self.status_callback = status_callback
        self.main_window = main_window
        
        # 加载模板图片
        self.template_path = "assets/rec/stash_cn.png"
        self.template = cv2.imread(self.template_path)
        if self.template is None:
            raise ValueError(f"无法加载模板图片: {self.template_path}")
        
        # 界面组件
        self._create_search_frame()
        self._create_preview_frame()
        self._create_log_frame()
        
    def _preprocess_image(self, image):
        """图像预处理以提高识别率"""
        # 转换为OpenCV格式
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return img
        
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
            text="🔍 识别仓库", 
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
        
    def _refresh_preview(self):
        """刷新预览图像"""
        try:
            # 获取游戏窗口名称
            if not self.main_window:
                window_name = "Path of Exile 2"
            else:
                window_name = self.main_window.basic_config_page.game_entry.get().strip()
                if not window_name:
                    window_name = "Path of Exile 2"
            
            # 查找窗口
            hwnd = self._find_window(window_name)
            if not hwnd:
                self._add_log(f"未找到游戏窗口: {window_name}")
                return False
                
            # 获取窗口区域并截图
            rect = win32gui.GetWindowRect(hwnd)
            image = ImageGrab.grab(rect)
            
            # 调整图像大小以适应预览区域
            preview_width = 800
            ratio = preview_width / image.width
            preview_height = int(image.height * ratio)
            image = image.resize((preview_width, preview_height), Image.LANCZOS)
            
            # 更新预览
            photo = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
            
            self.status_callback("✅ 预览已更新")
            return True
            
        except Exception as e:
            self._add_log(f"刷新预览失败: {str(e)}")
            return False
            
    def _do_recognition(self):
        """执行识别"""
        try:
            # 刷新预览图像
            if not self._refresh_preview():
                return
                
            # 获取当前预览的图像
            image = ImageTk.getimage(self.preview_label.image)
            
            try:
                # 图像预处理
                processed_image = self._preprocess_image(image)
                
                # 获取原始游戏窗口截图
                hwnd = self._find_window("Path of Exile 2")
                if not hwnd:
                    self._add_log("未找到游戏窗口")
                    return
                    
                rect = win32gui.GetWindowRect(hwnd)
                original_image = ImageGrab.grab(rect)
                original_cv = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2BGR)
                
                # 转换为灰度图进行匹配
                gray_img = cv2.cvtColor(original_cv, cv2.COLOR_BGR2GRAY)
                gray_template = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
                
                # 获取模板原始尺寸
                template_h, template_w = gray_template.shape
                
                # 计算合适的缩放范围
                # 基于模板大小和原始图像大小设定范围
                img_h, img_w = gray_img.shape
                min_scale = max(0.3, template_w / img_w * 0.5)  # 最小缩放不小于0.3
                max_scale = min(3.0, img_w / template_w * 0.5)  # 最大缩放不超过3.0
                
                # 生成缩放系数序列
                scales = np.linspace(min_scale, max_scale, 20)
                
                # 多尺度模板匹配
                max_val_overall = 0
                max_loc_overall = None
                best_scale = None
                best_w = None
                best_h = None
                
                for scale in scales:
                    # 调整模板大小
                    scaled_w = int(template_w * scale)
                    scaled_h = int(template_h * scale)
                    if scaled_w < 10 or scaled_h < 10:  # 避免模板太小
                        continue
                    resized_template = cv2.resize(gray_template, (scaled_w, scaled_h))
                    
                    # 执行模板匹配
                    result = cv2.matchTemplate(gray_img, resized_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val > max_val_overall:
                        max_val_overall = max_val
                        max_loc_overall = max_loc
                        best_scale = scale
                        best_w = scaled_w
                        best_h = scaled_h
                
                # 设置匹配阈值
                threshold = 0.7  # 略微降低阈值以适应缩放带来的影响
                
                if max_val_overall >= threshold:
                    # 获取匹配位置
                    top_left = max_loc_overall
                    bottom_right = (top_left[0] + best_w, top_left[1] + best_h)
                    
                    # 记录匹配详细信息
                    self._add_log(f"最佳匹配比例: {best_scale:.2f}")
                    self._add_log(f"模板原始大小: {template_w}x{template_h}")
                    self._add_log(f"最佳匹配大小: {best_w}x{best_h}")
                    
                    # 计算缩放比例用于预览显示
                    preview_width = 800
                    scale_factor = preview_width / original_image.width
                    
                    # 在预览图像上绘制矩形
                    preview_top_left = (int(top_left[0] * scale_factor), int(top_left[1] * scale_factor))
                    preview_bottom_right = (int(bottom_right[0] * scale_factor), int(bottom_right[1] * scale_factor))
                    cv2.rectangle(processed_image, preview_top_left, preview_bottom_right, (0, 255, 0), 2)
                    
                    # 转换回PIL格式并更新预览
                    processed_pil = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
                    photo = ImageTk.PhotoImage(processed_pil)
                    self.preview_label.configure(image=photo)
                    self.preview_label.image = photo
                    
                    # 显示匹配信息
                    self._add_log(f"✅ 识别成功！")
                    self._add_log(f"匹配度: {max_val_overall:.2%}")
                    self._add_log(f"位置: {top_left}")
                    self.status_callback("✅ 识别成功")
                    
                    # 执行点击操作
                    try:
                        # 计算相对窗口的点击位置
                        relative_x = top_left[0] + best_w//2
                        relative_y = top_left[1] + best_h//2
                        
                        # 将窗口置于前台
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.SetActiveWindow(hwnd)
                        # 等待窗口激活
                        import time
                        time.sleep(0.2)
                        
                        # 获取窗口左上角坐标
                        window_rect = win32gui.GetWindowRect(hwnd)
                        window_x = window_rect[0]
                        window_y = window_rect[1]
                        
                        # 计算屏幕坐标
                        screen_x = window_x + relative_x
                        screen_y = window_y + relative_y
                        
                        # 保存当前鼠标位置
                        old_pos = win32api.GetCursorPos()
                        
                        # 移动鼠标并点击
                        win32api.SetCursorPos((screen_x, screen_y))
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        time.sleep(0.1)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                        
                        # 恢复鼠标位置
                        win32api.SetCursorPos(old_pos)
                        
                        self._add_log(f"✅ 已点击位置: ({screen_x}, {screen_y})")
                    except Exception as e:
                        self._add_log(f"点击操作失败: {str(e)}")
                else:
                    self._add_log(f"❌ 识别失败：未找到匹配的区域")
                    self._add_log(f"最高匹配度: {max_val:.2%}")
                    self.status_callback("❌ 识别失败")
                    
            except Exception as e:
                self._add_log(f"图像识别失败: {str(e)}")
                
        except Exception as e:
            self._add_log(f"识别过程出错: {str(e)}")
            
    def _find_window(self, window_name):
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
        
    def _add_log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_callback(message)
