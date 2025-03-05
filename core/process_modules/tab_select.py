import cv2
import numpy as np
import time
import win32gui
import win32api
import win32con
from PIL import Image, ImageDraw
from core.process_module import ProcessModule
from gui.pages.recognition_base_page import RecognitionBasePage
from gui.utils import switch_to_window
from paddleocr import PaddleOCR

class TabSelectModule(ProcessModule):
    """Tab选择流程模块"""
    
    def __init__(self):
        self.recognition_base = None
        self.preview_image = None
        self.show_preview = False

    def name(self) -> str:
        return "Tab选择"

    def description(self) -> str:
        return "识别并点击指定的Tab标签"

    def run(self, tab_text=None, show_preview=False, **kwargs):
        """运行模块，识别并点击指定的Tab标签
        
        Args:
            tab_text: 要识别的Tab文本
            show_preview: 是否返回标注了匹配区域的预览图
            
        Returns:
            bool: 操作是否成功
            Image: 如果show_preview为True，返回标注了匹配区域的预览图，否则返回None
        """
        if not tab_text:
            self._log_callback("未指定Tab文本", "ERROR")
            return False, None
            
        if not self.recognition_base:
            # 创建一个RecognitionBasePage实例来使用其功能
            self.recognition_base = RecognitionBasePage(None, self._log_callback, self._status_callback)
        
        self.show_preview = show_preview
        
        try:
            # 获取游戏窗口
            window_name = self.recognition_base._get_window_name()
            hwnd = self.recognition_base._find_window(window_name)
            if not hwnd:
                print(f"未找到游戏窗口: {window_name}")
                return False, None

            # 切换到游戏窗口
            switch_to_window(window_name)
            # 等待窗口激活
            time.sleep(0.2)

            # 获取窗口区域并截图
            rect = self.recognition_base._get_window_rect(hwnd)
            original_image = self.recognition_base._grab_screen(rect)
            original_cv = self.recognition_base._convert_to_cv(original_image)
            
            # 使用PaddleOCR PP-OCRv4轻量化模型识别文本区域
            ocr = PaddleOCR(
                use_angle_cls=True, 
                lang="ch", 
                show_log=False, 
                use_mp=True,        # 使用多进程加速
                total_process_num=2, # 使用2个进程
                use_pp_ocr_v4=True,  # 启用PP-OCRv4轻量化模型
                det_limit_side_len=960, # 检测模型的输入尺寸
                rec_batch_num=6,    # 识别模型batch大小
                enable_mkldnn=True  # 启用mkldnn加速
            )
            
            # 直接使用原始图像进行识别
            result = ocr.ocr(original_cv, cls=True)
            
            # 查找匹配的文本
            found = False
            click_x, click_y = 0, 0
            
            # 提取识别到的文本列表用于调试
            recognized_texts = []
            if result is not None and len(result) > 0:
                for line in result[0]:
                    if len(line) >= 2 and isinstance(line[1], tuple) and len(line[1]) >= 1:
                        recognized_texts.append(line[1][0])
            
            # 打印识别到的所有文本，用于调试
            print(f"识别到的文本列表: {recognized_texts}")
            print(f"正在查找文本: {tab_text}")
            
            # 遍历识别结果查找匹配文本
            if result is not None and len(result) > 0:
                for line in result[0]:
                    if len(line) >= 2 and isinstance(line[1], tuple) and len(line[1]) >= 2:
                        text = line[1][0].strip()
                        confidence = line[1][1]
                        
                        # 使用更精确的匹配方式
                        # 1. 完全匹配
                        exact_match = text.lower() == tab_text.lower()
                        # 2. 文本包含匹配（仅当搜索文本长度大于3时）
                        contains_match = len(tab_text) > 3 and tab_text.lower() in text.lower()
                        # 3. 计算相似度（针对短文本）
                        similarity_match = False
                        
                        # 对于短文本，计算字符重叠率
                        if len(tab_text) <= 3 and not exact_match:
                            # 计算两个字符串的字符重叠率
                            tab_chars = set(tab_text.lower())
                            text_chars = set(text.lower())
                            overlap = len(tab_chars.intersection(text_chars))
                            similarity = overlap / len(tab_chars) if tab_chars else 0
                            similarity_match = similarity > 0.8 and len(text) <= len(tab_text) + 2
                        
                        if exact_match or contains_match or similarity_match:
                            # 对于非完全匹配，要求更高的置信度
                            min_confidence = 0.8 if exact_match else 0.9
                            
                            if confidence < min_confidence:
                                print(f"匹配文本 '{text}' 置信度过低: {confidence}，需要 {min_confidence}")
                                continue
                                
                            print(f"找到匹配文本: '{text}', 置信度: {confidence}")
                            
                            # 获取文本框的坐标（PaddleOCR返回四个角点坐标）
                            box = line[0]
                            # 计算边界框
                            x_coords = [int(point[0]) for point in box]
                            y_coords = [int(point[1]) for point in box]
                            x = min(x_coords)
                            y = min(y_coords)
                            w = max(x_coords) - x
                            h = max(y_coords) - y
                            
                            # 计算点击位置（文本框中心）
                            click_x = x + w // 2
                            click_y = y + h // 2
                    
                            # 如果需要预览，在原图上标记识别区域
                            if self.show_preview:
                                # 转换回PIL图像用于绘制
                                pil_image = Image.fromarray(cv2.cvtColor(original_cv, cv2.COLOR_BGR2RGB))
                                draw = ImageDraw.Draw(pil_image)
                                # 绘制红色矩形框
                                draw.rectangle([x, y, x+w, y+h], outline="red", width=2)
                                # 标记点击位置
                                draw.ellipse([click_x-5, click_y-5, click_x+5, click_y+5], fill="red")
                                # 保存预览图
                                self.preview_image = pil_image
                            
                            found = True
                            break
            
            if not found:
                print(f"未找到匹配的Tab文本: {tab_text}")
                return False, self.preview_image if self.show_preview else None
            
            # 获取窗口左上角坐标
            window_rect = win32gui.GetWindowRect(hwnd)
            window_x = window_rect[0]
            window_y = window_rect[1]
            
            # 计算屏幕坐标
            screen_x = window_x + click_x
            screen_y = window_y + click_y
            
            # 保存当前鼠标位置
            old_pos = win32api.GetCursorPos()
            
            # 移动鼠标并双击
            win32api.SetCursorPos((screen_x, screen_y))
            # 第一次点击
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            # 短暂延迟
            time.sleep(0.1)
            # 第二次点击
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            # 恢复鼠标位置
            win32api.SetCursorPos(old_pos)
            
            return True, self.preview_image if self.show_preview else None
                
        except Exception as e:
            print(f"Tab选择失败: {str(e)}")
            return False, self.preview_image if self.show_preview else None

    def _log_callback(self, message, level="INFO"):
        """日志回调"""
        print(f"[{level}] {message}")

    def _status_callback(self, message):
        """状态回调"""
        print(message)