import cv2
import numpy as np
from PIL import Image, ImageTk
import win32gui
import win32con
import win32api
import win32ui
import ctypes
from ctypes import (Structure, c_ulong, c_ushort, c_short, c_long, 
                   POINTER, sizeof, CFUNCTYPE, c_void_p, windll, byref)
from ..process_module import ProcessModule

ULONG_PTR = POINTER(c_ulong)

class MOUSEINPUT(Structure):
    _fields_ = [
        ("dx", c_long),
        ("dy", c_long),
        ("mouseData", c_ulong),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", ULONG_PTR)
    ]

class KEYBDINPUT(Structure):
    _fields_ = [
        ("wVk", c_ushort),
        ("wScan", c_ushort),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", ULONG_PTR)
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT)
    ]

class INPUT(Structure):
    _fields_ = [
        ("type", c_ulong),
        ("_input", _INPUT_UNION)
    ]

class TakeOutItemModule(ProcessModule):
    """取出物品模块 - 根据给定位置取出仓库物品"""
    def __init__(self):
        super().__init__()
        # 加载wisdom定位锚点模板
        self.wisdom_template = cv2.imread("assets/rec/wisdom.png")
        
        if self.wisdom_template is None:
            self.logger.warning("⚠️ wisdom模板图片加载失败")

    def name(self) -> str:
        return "取出物品"
        
    def description(self) -> str:
        return "根据给定位置取出仓库物品"
        
    def run(self, **kwargs):
        preview_enabled = kwargs.get('preview_enabled', False)
        p1_num = kwargs.get('p1_num')
        p2_num = kwargs.get('p2_num')
        
        if p1_num is None or p2_num is None:
            self.logger.error("未提供物品位置参数")
            return False
            
        preview_callback = kwargs.get('preview_callback') if preview_enabled else None
        return self.process(p1_num, p2_num, preview_callback)

    def _get_window_name(self):
        """获取游戏窗口名称"""
        return "Path of Exile 2"

    def _find_window(self, window_name):
        """查找指定名称的窗口句柄"""
        return win32gui.FindWindow(None, window_name)

    def _get_window_rect(self, hwnd):
        """获取窗口矩形区域"""
        return win32gui.GetWindowRect(hwnd)

    def _grab_screen(self, rect):
        """截取指定区域的屏幕图像"""
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        
        # 创建设备上下文
        hwnd_dc = win32gui.GetWindowDC(0)
        mfc_dc = win32gui.GetDC(0)
        save_dc = win32gui.CreateCompatibleDC(mfc_dc)
        
        # 创建win32ui位图对象
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(win32ui.CreateDCFromHandle(mfc_dc), width, height)
        
        # 选择到设备上下文
        old_bitmap = win32ui.CreateDCFromHandle(save_dc).SelectObject(bmp)
        
        # 复制屏幕内容到位图
        win32gui.BitBlt(save_dc, 0, 0, width, height, 
                       mfc_dc, rect[0], rect[1], win32con.SRCCOPY)
                       
        # 获取位图数据
        bmp.Paint(win32ui.CreateDCFromHandle(save_dc), (0, 0, width, height))
        bits = bmp.GetBitmapBits(True)
        
        # 转换为PIL图像
        img = Image.frombuffer(
            'RGB',
            (width, height),
            bits,
            'raw',
            'BGRX',
            0,
            1
        )
        
        # 清理win32ui对象
        win32ui.CreateDCFromHandle(save_dc).SelectObject(old_bitmap)
        # 注意：不再调用 bmp.DeleteObject()，因为 PyCBitmap 对象没有这个方法
        # Python 的垃圾回收会处理 bmp 对象
        
        # 清理资源
        win32gui.DeleteDC(save_dc)
        win32gui.ReleaseDC(0, hwnd_dc)
        win32gui.ReleaseDC(0, mfc_dc)
        
        return img

    def _convert_to_cv(self, pil_image):
        """将PIL图像转换为OpenCV格式"""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def process(self, p1_num, p2_num, preview_callback=None):
        """
        执行取出物品操作
        
        Args:
            p1_num: 第一个位置的格子编号
            p2_num: 第二个位置的格子编号
            preview_callback: 用于更新预览图像的回调函数(可选)
        
        Returns:
            bool or numpy.ndarray: 如果识别成功返回处理后的图像，否则返回False
        """
        try:
            # 获取游戏窗口截图
            window_name = self._get_window_name()
            hwnd = self._find_window(window_name)
            if not hwnd:
                self.logger.error(f"未找到游戏窗口: {window_name}")
                return False
                
            rect = self._get_window_rect(hwnd)
            original_image = self._grab_screen(rect)
            original_cv = self._convert_to_cv(original_image)
            
            # 获取图像尺寸和中心线
            img_h, img_w = original_cv.shape[:2]
            window_center_x = img_w // 2
            
            # 只处理左半部分（仓位区域）
            left_region = original_cv[:, :window_center_x]
            gray_left = cv2.cvtColor(left_region, cv2.COLOR_BGR2GRAY)
            
            # 识别wisdom锚点
            wisdom_gray = cv2.cvtColor(self.wisdom_template, cv2.COLOR_BGR2GRAY)
            marker_matches = []
            best_scale_map = {}
            
            wisdom_scales = np.linspace(0.2, 2.5, 35)
            wisdom_threshold = 0.65
            
            for scale in wisdom_scales:
                scaled_wisdom_w = min(int(wisdom_gray.shape[1] * scale), gray_left.shape[1] - 1)
                scaled_wisdom_h = min(int(wisdom_gray.shape[0] * scale), gray_left.shape[0] - 1)
                if scaled_wisdom_w < 10 or scaled_wisdom_h < 10:
                    continue
                    
                resized_wisdom = cv2.resize(wisdom_gray, (scaled_wisdom_w, scaled_wisdom_h))
                result = cv2.matchTemplate(gray_left, resized_wisdom, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= wisdom_threshold)
                
                for loc in zip(*locations[::-1]):
                    pos_key = f"{loc[0]}_{loc[1]}"
                    curr_val = result[loc[1], loc[0]]
                    
                    if pos_key in best_scale_map:
                        if curr_val > best_scale_map[pos_key]['value']:
                            best_scale_map[pos_key] = {
                                'scale': scale,
                                'value': curr_val,
                                'size': (resized_wisdom.shape[1], resized_wisdom.shape[0])
                            }
                    else:
                        best_scale_map[pos_key] = {
                            'scale': scale,
                            'value': curr_val,
                            'size': (resized_wisdom.shape[1], resized_wisdom.shape[0])
                        }
            
            # 转换最佳匹配为marker_matches
            for pos_key, match_info in best_scale_map.items():
                x, y = map(int, pos_key.split('_'))
                marker_matches.append({
                    'pos': (x, y),
                    'scale': match_info['scale'],
                    'size': match_info['size'],
                    'value': match_info['value']
                })
            
            if len(marker_matches) < 2:
                self.logger.warning("未找到足够的wisdom定位锚点")
                return False
            
            # 根据位置筛选左上角和右下角的标记点
            top_left_candidates = [m for m in marker_matches if 
                                 m['pos'][0] < window_center_x * 0.5 and
                                 m['pos'][1] < img_h * 0.5 and
                                 m['value'] > 0.75]
            
            bottom_right_candidates = [m for m in marker_matches if 
                                     m['pos'][0] > window_center_x * 0.2 and
                                     m['pos'][1] > img_h * 0.2 and
                                     m['value'] > 0.75]
            
            if not top_left_candidates or not bottom_right_candidates:
                self.logger.warning("未能定位到正确的wisdom定位锚点位置")
                return False
            
            # 选择最佳的锚点
            top_left_marker = min(top_left_candidates, key=lambda x: x['pos'][0] + x['pos'][1])
            bottom_right_marker = max(bottom_right_candidates, key=lambda x: x['pos'][0] + x['pos'][1])
            
            # 计算网格参数
            grid_start_x = top_left_marker['pos'][0]
            grid_start_y = top_left_marker['pos'][1]
            grid_end_x = bottom_right_marker['pos'][0] + bottom_right_marker['size'][0]
            grid_end_y = bottom_right_marker['pos'][1] + bottom_right_marker['size'][1]
            
            # 判断是大仓还是小仓
            dx = grid_end_x - grid_start_x
            dy = grid_end_y - grid_start_y
            cell_size = (top_left_marker['size'][0] + top_left_marker['size'][1]) / 2
            
            approx_grid_width = dx / cell_size
            approx_grid_height = dy / cell_size
            
            score_24 = abs(approx_grid_width - 24) + abs(approx_grid_height - 24)
            score_12 = abs(approx_grid_width - 12) + abs(approx_grid_height - 12)
            
            is_big_stash = score_24 < score_12
            grid_cols = 24 if is_big_stash else 12
            grid_rows = 24 if is_big_stash else 12
            
            # 计算单元格大小
            cell_width = dx / grid_cols
            cell_height = dy / grid_rows
            
            # 计算目标点击位置
            def get_cell_center(num):
                row = (num - 1) // grid_cols
                col = (num - 1) % grid_cols
                x = grid_start_x + col * cell_width + cell_width / 2
                y = grid_start_y + row * cell_height + cell_height / 2
                return x, y
            
            x1, y1 = get_cell_center(p1_num)
            x2, y2 = get_cell_center(p2_num)
            
            # 转换为屏幕坐标并执行点击
            rect = win32gui.GetWindowRect(hwnd)
            screen_x1 = int(x1) + rect[0]
            screen_y1 = int(y1) + rect[1]
            screen_x2 = int(x2) + rect[0]
            screen_y2 = int(y2) + rect[1]
            
            try:
                # 确保窗口处于活动状态
                if win32gui.GetForegroundWindow() != hwnd:
                    win32gui.SetForegroundWindow(hwnd)
                    win32api.Sleep(100)
                
                # 获取客户区位置
                client_rect = win32gui.GetClientRect(hwnd)
                client_x, client_y = win32gui.ClientToScreen(hwnd, (0, 0))
                
                def click_at(x, y):
                    # 转换为客户区相对坐标
                    rel_x = x - client_x
                    rel_y = y - client_y
                    
                    # 移动鼠标并点击
                    win32api.SetCursorPos((x, y))
                    win32api.Sleep(50)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    win32api.Sleep(50)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                
                # 按下Ctrl键
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                win32api.Sleep(100)
                
                # 点击指定位置
                click_at(screen_x1, screen_y1)
                win32api.Sleep(300)
                
                # 释放Ctrl键
                win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                
            except Exception as e:
                self.logger.error(f"点击操作失败: {str(e)}")
                return False
            
            # 制作预览图
            preview_scale = 800 / original_image.width
            processed_image = original_cv.copy()
            
            # 绘制网格线
            for i in range(grid_rows + 1):
                y = grid_start_y + i * cell_height
                cv2.line(processed_image,
                        (int(grid_start_x), int(y)),
                        (int(grid_end_x), int(y)),
                        (255, 255, 255), 1)
            
            for j in range(grid_cols + 1):
                x = grid_start_x + j * cell_width
                cv2.line(processed_image,
                        (int(x), int(grid_start_y)),
                        (int(x), int(grid_end_y)),
                        (255, 255, 255), 1)
            
            # 标记点击位置
            cv2.circle(processed_image, (int(x1), int(y1)), 5, (0, 255, 0), -1)
            
            # 如果提供了预览回调，则调用它
            if preview_callback:
                preview_image = cv2.resize(processed_image, 
                                         (int(original_image.width * preview_scale),
                                          int(original_image.height * preview_scale)))
                preview_callback(preview_image)
            
            return processed_image
            
        except Exception as e:
            self.logger.error(f"处理过程出错: {str(e)}")
            return False
