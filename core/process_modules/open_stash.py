import cv2
import numpy as np
from PIL import Image
import win32gui
import win32con
import win32api
import time

from core.process_module import ProcessModule
from gui.pages.recognition_base_page import RecognitionBasePage
from gui.utils import switch_to_window


class OpenStashModule(ProcessModule):
    """打开仓库流程模块"""
    
    def __init__(self):
        self.recognition_base = None

    def name(self) -> str:
        return "打开仓库"

    def description(self) -> str:
        return "识别并点击仓库按钮"

    def run(self, **kwargs):
        """运行模块，识别并点击仓库"""
        if not self.recognition_base:
            # 创建一个RecognitionBasePage实例来使用其功能
            self.recognition_base = RecognitionBasePage(None, self._log_callback, self._status_callback)
            self.recognition_base.set_template("assets/rec/stash_cn.png")

        if not self.recognition_base.validate_template():
            return False

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

            # 转换为灰度图进行匹配
            gray_img = cv2.cvtColor(original_cv, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(self.recognition_base.template, cv2.COLOR_BGR2GRAY)

            # 获取模板原始尺寸
            template_h, template_w = gray_template.shape

            # 计算合适的缩放范围
            img_h, img_w = gray_img.shape
            min_scale = max(0.3, template_w / img_w * 0.5)
            max_scale = min(3.0, img_w / template_w * 0.5)

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
                if scaled_w < 10 or scaled_h < 10:
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
            threshold = 0.7

            if max_val_overall >= threshold:
                # 获取匹配位置
                top_left = max_loc_overall

                # 执行点击操作
                # 计算相对窗口的点击位置
                relative_x = top_left[0] + best_w//2
                relative_y = top_left[1] + best_h//2

                # 将窗口置于前台 - 使用通用切换窗口函数
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

                return True
                
            return False

        except Exception as e:
            print(f"打开仓库失败: {str(e)}")
            return False

    def _log_callback(self, message, level="INFO"):
        """日志回调"""
        print(f"[{level}] {message}")

    def _status_callback(self, message):
        """状态回调"""
        print(message)
