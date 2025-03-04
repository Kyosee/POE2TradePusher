import os
import cv2
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont
import win32gui
import win32con
import win32api

from core.process_module import ProcessModule
from gui.pages.recognition_base_page import RecognitionBasePage
from gui.utils import switch_to_window


class TabSelectModule(ProcessModule):
    """标签选择流程模块"""
    
    def __init__(self):
        self.recognition_base = None
        self.tab_images_dir = "assets/tab"
        
        # 确保标签图片目录存在
        os.makedirs(self.tab_images_dir, exist_ok=True)

    def name(self) -> str:
        return "标签选择"

    def description(self) -> str:
        return "识别并点击游戏中的标签"

    def _create_tab_image(self, tab_text):
        """根据文本创建标签图片"""
        try:
            # 设置字体和颜色
            font_size = 22
            font_color = (180, 164, 128)  # RGB格式的#B6A480
            
            # 计算图片宽度
            font_path = os.path.join("assets", "fonts", "msyh.ttc")  # 微软雅黑字体，确保此路径正确
            if not os.path.exists(font_path):
                font_path = None  # 使用默认字体
                
            font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
            text_width = font.getbbox(tab_text)[2] - font.getbbox(tab_text)[0]
            
            # 计算图片尺寸（宽度=文本宽度+20px边距，高度=33px）
            width = text_width + 20
            height = 33
            
            # 创建透明背景图片
            image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # 绘制文本，居中对齐
            text_x = (width - text_width) // 2
            text_y = (height - font_size) // 2
            draw.text((text_x, text_y), tab_text, font=font, fill=font_color)
            
            # 保存图片
            tab_image_path = os.path.join(self.tab_images_dir, f"{tab_text}.png")
            image.save(tab_image_path)
            
            return tab_image_path
        except Exception as e:
            print(f"创建标签图片失败: {str(e)}")
            return None

    def _get_tab_image_path(self, tab_text):
        """获取或创建标签图片路径"""
        tab_image_path = os.path.join(self.tab_images_dir, f"{tab_text}.png")
        
        # 检查图片是否已存在
        if not os.path.exists(tab_image_path):
            # 如果不存在，则创建图片
            tab_image_path = self._create_tab_image(tab_text)
            
        return tab_image_path

    def run(self, tab_text, return_preview=False, **kwargs):
        """
        运行模块，识别并点击标签
        
        参数:
            tab_text: 要选择的标签文本
            return_preview: 是否返回标记了匹配位置的预览图
        
        返回:
            如果点击成功，返回True；否则返回False
            如果return_preview=True且匹配成功，则返回(True, preview_image)
        """
        if not self.recognition_base:
            # 创建一个RecognitionBasePage实例来使用其功能
            self.recognition_base = RecognitionBasePage(None, self._log_callback, self._status_callback)
        
        # 获取或创建标签图片
        tab_image_path = self._get_tab_image_path(tab_text)
        if not tab_image_path:
            return False
        
        # 设置模板
        self.recognition_base.set_template(tab_image_path)
        
        if not self.recognition_base.validate_template():
            return False
            
        preview_image = None
        try:
            # 获取游戏窗口
            window_name = self.recognition_base._get_window_name()
            hwnd = self.recognition_base._find_window(window_name)
            if not hwnd:
                print(f"未找到游戏窗口: {window_name}")
                return False

            rect = self.recognition_base._get_window_rect(hwnd)
            original_image = self.recognition_base._grab_screen(rect)
            original_cv = self.recognition_base._convert_to_cv(original_image)

            # 转换为RGB图像进行匹配，保留色彩信息
            img_rgb = cv2.cvtColor(original_cv, cv2.COLOR_BGR2RGB)
            template_rgb = cv2.cvtColor(self.recognition_base.template, cv2.COLOR_BGR2RGB)

            # 匹配模板
            result = cv2.matchTemplate(img_rgb, template_rgb, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # 设置匹配阈值
            threshold = 0.6

            if max_val >= threshold:
                # 获取匹配位置和尺寸
                top_left = max_loc
                h, w = template_rgb.shape[:2]
                bottom_right = (top_left[0] + w, top_left[1] + h)
                
                # 如果需要返回预览图
                if return_preview:
                    # 复制原始图像用于标记
                    preview_img = original_cv.copy()
                    # 绘制矩形框标记匹配位置
                    cv2.rectangle(preview_img, top_left, bottom_right, (0, 255, 0), 2)
                    preview_image = preview_img

                # 执行点击操作
                # 计算相对窗口的点击位置（居中点击）
                relative_x = top_left[0] + w // 2
                relative_y = top_left[1] + h // 2

                # 将窗口置于前台
                switch_to_window(window_name)
                # 等待窗口激活
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
                # 单击即可
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

                # 恢复鼠标位置
                win32api.SetCursorPos(old_pos)
                
                if return_preview:
                    return True, preview_image
                return True
            
            if return_preview:
                return False, None
            return False

        except Exception as e:
            print(f"选择标签失败: {str(e)}")
            if return_preview:
                return False, None
            return False

    def _log_callback(self, message, level="INFO"):
        """日志回调"""
        print(f"[{level}] {message}")

    def _status_callback(self, message):
        """状态回调"""
        print(message)
