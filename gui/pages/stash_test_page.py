from .recognition_base_page import RecognitionBasePage
import cv2
import numpy as np
from PIL import Image, ImageTk
import win32gui
import win32con
import win32api
import time

class StashTestPage(RecognitionBasePage):
    """仓库测试页面 - 识别仓库并执行点击操作"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        super().__init__(master, callback_log, callback_status, main_window)
        self.set_template("assets/rec/stash_cn.png")
        
    def _do_recognition(self):
        """执行仓库识别和点击"""
        # 验证模板
        if not self.validate_template():
            return
            
        # 刷新预览图像
        if not self._refresh_preview():
            return
            
        try:
            # 获取当前预览的图像
            image = ImageTk.getimage(self.preview_label.image)
            
            # 图像预处理
            processed_image = self._preprocess_image(image)
            
            # 获取游戏窗口截图
            window_name = self._get_window_name()
            hwnd = self._find_window(window_name)
            if not hwnd:
                self._add_log(f"未找到游戏窗口: {window_name}", "ERROR")
                return
                
            rect = self._get_window_rect(hwnd)
            original_image = self._grab_screen(rect)
            original_cv = self._convert_to_cv(original_image)
            
            # 转换为灰度图进行匹配
            gray_img = cv2.cvtColor(original_cv, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
            
            # 获取模板原始尺寸
            template_h, template_w = gray_template.shape
            
            # 计算合适的缩放范围
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
                self._add_log("✅ 识别成功！")
                self._add_log(f"匹配度: {max_val_overall:.2%}")
                self._add_log(f"位置: {top_left}")
                self.update_status("✅ 识别成功")
                
                # 执行点击操作
                try:
                    # 计算相对窗口的点击位置
                    relative_x = top_left[0] + best_w//2
                    relative_y = top_left[1] + best_h//2
                    
                    # 将窗口置于前台
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.SetActiveWindow(hwnd)
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
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    time.sleep(0.1)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    
                    # 恢复鼠标位置
                    win32api.SetCursorPos(old_pos)
                    
                    self._add_log(f"✅ 已点击位置: ({screen_x}, {screen_y})")
                except Exception as e:
                    self._add_log(f"点击操作失败: {str(e)}", "ERROR")
            else:
                self._add_log("❌ 识别失败：未找到匹配的区域", "WARNING")
                self._add_log(f"最高匹配度: {max_val_overall:.2%}", "WARNING")
                self.update_status("❌ 识别失败")
                
        except Exception as e:
            self._add_log(f"识别过程出错: {str(e)}", "ERROR")
            self.update_status("❌ 识别失败")
