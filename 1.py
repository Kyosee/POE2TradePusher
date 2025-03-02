from .recognition_base_page import RecognitionBasePage
import cv2
import numpy as np
from PIL import Image, ImageTk
import win32gui
import win32con
import win32api
import ctypes
from ctypes import (Structure, c_ulong, c_ushort, c_short, c_long, 
                   POINTER, sizeof, CFUNCTYPE, c_void_p, windll, byref)

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


class PositionTestPage(RecognitionBasePage):
    """定位测试页面 - 仓库类型识别和格子定位"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        super().__init__(master, callback_log, callback_status, main_window)
        # 加载wisdom定位锚点模板
        self.wisdom_template = cv2.imread("assets/rec/wisdom.png")
        
        if self.wisdom_template is None:
            self._add_log("⚠️ wisdom模板图片加载失败", "WARNING")

    def _do_recognition(self):
        """执行定位测试：基于wisdom锚点识别仓库类型和格子位置"""
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
            
            # 获取图像尺寸和中心线
            img_h, img_w = original_cv.shape[:2]
            window_center_x = img_w // 2
            self._add_log(f"游戏窗口尺寸: {img_w}x{img_h}")
            
            # 只处理左半部分（仓位区域）
            left_region = original_cv[:, :window_center_x]
            gray_left = cv2.cvtColor(left_region, cv2.COLOR_BGR2GRAY)
            
            # ---------- 识别wisdom锚点 ----------
            wisdom_gray = cv2.cvtColor(self.wisdom_template, cv2.COLOR_BGR2GRAY)
            marker_matches = []
            best_scale_map = {}
            
            # 进一步扩大缩放范围和降低阈值以提高识别灵活性
            wisdom_scales = np.linspace(0.2, 2.5, 35)  # 更大的范围，更多采样点
            wisdom_threshold = 0.65  # 进一步降低阈值提高容错性
            
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
            self._add_log("\n----- wisdom定位结果 -----")
            self._add_log("开始查找wisdom定位锚点...")
            for pos_key, match_info in best_scale_map.items():
                x, y = map(int, pos_key.split('_'))
                marker_matches.append({
                    'pos': (x, y),
                    'scale': match_info['scale'],
                    'size': match_info['size'],
                    'value': match_info['value']
                })
            
            if len(marker_matches) < 2:
                self._add_log("❌ 未找到足够的wisdom定位锚点（需要2个，实际找到：{}）".format(len(marker_matches)), "WARNING")
                self._add_log("请确保在仓位左上角和右下角各放置了一个wisdom装备", "WARNING")
                self.update_status("❌ 识别失败：缺少定位锚点")
                return
            
            self._add_log(f"✓ 找到 {len(marker_matches)} 个可能的wisdom定位锚点")
            
            # 根据位置筛选左上角和右下角的标记点（扩大搜索范围）
            top_left_candidates = [m for m in marker_matches if 
                                 m['pos'][0] < window_center_x * 0.5 and  # 扩大到左半部分
                                 m['pos'][1] < img_h * 0.5 and           # 扩大到上半部分
                                 m['value'] > 0.75]                      # 降低阈值
                                 
            bottom_right_candidates = [m for m in marker_matches if 
                                     m['pos'][0] > window_center_x * 0.2 and  # 从左侧1/5开始
                                     m['pos'][1] > img_h * 0.2 and           # 从顶部1/5开始
                                     m['value'] > 0.75]                      # 降低阈值
            
            # 验证候选点尺寸的一致性
            if top_left_candidates and bottom_right_candidates:
                # 移除尺寸差异过大的候选点（提高容错度）
                avg_size = sum(c['size'][0] * c['size'][1] for c in top_left_candidates + bottom_right_candidates) / len(top_left_candidates + bottom_right_candidates)
                size_threshold = 0.7  # 允许70%的尺寸差异
                
                top_left_candidates = [c for c in top_left_candidates if 
                                     abs(c['size'][0] * c['size'][1] - avg_size) / avg_size < size_threshold]
                bottom_right_candidates = [c for c in bottom_right_candidates if 
                                        abs(c['size'][0] * c['size'][1] - avg_size) / avg_size < size_threshold]
            
            if not top_left_candidates or not bottom_right_candidates:
                self._add_log("❌ 未能定位到正确的wisdom定位锚点位置", "WARNING")
                if not top_left_candidates:
                    self._add_log("  - 缺少左上角定位锚点（请在仓位左上角放置wisdom装备）", "WARNING")
                if not bottom_right_candidates:
                    self._add_log("  - 缺少右下角定位锚点（请在仓位右下角放置wisdom装备）", "WARNING")
                self.update_status("❌ 识别失败：定位锚点位置错误")
                return
            
            # 选择最佳的锚点
            top_left_marker = min(top_left_candidates, key=lambda x: x['pos'][0] + x['pos'][1])
            bottom_right_marker = max(bottom_right_candidates, key=lambda x: x['pos'][0] + x['pos'][1])
            
            # ---------- 计算仓库类型和尺寸 ----------
            # 计算两个锚点之间的距离
            dx = bottom_right_marker['pos'][0] - top_left_marker['pos'][0]
            dy = bottom_right_marker['pos'][1] - top_left_marker['pos'][1]
            
            # 使用wisdom物品（1x1格子）的大小作为基准
            marker_width_tl = top_left_marker['size'][0]
            marker_height_tl = top_left_marker['size'][1]
            marker_width_br = bottom_right_marker['size'][0]
            marker_height_br = bottom_right_marker['size'][1]
            
            # 使用两个锚点的平均大小作为标准格子大小
            cell_size = (marker_width_tl + marker_height_tl + 
                        marker_width_br + marker_height_br) / 4
            
            # 根据格子大小计算实际的格子数
            approx_grid_width = dx / cell_size
            approx_grid_height = dy / cell_size
            
            # 计算大仓和小仓的可能性得分
            score_24 = abs(approx_grid_width - 24) + abs(approx_grid_height - 24)
            score_12 = abs(approx_grid_width - 12) + abs(approx_grid_height - 12)
            
            # 判断仓库类型（更精确的判断）
            is_big_stash = score_24 < score_12
            grid_cols = 24 if is_big_stash else 12
            grid_rows = 24 if is_big_stash else 12
            stash_type = "大型仓位 (24x24)" if is_big_stash else "小型仓位 (12x12)"
            
            # 使用标准格子大小
            cell_width = cell_size
            cell_height = cell_size
            
            # 计算网格覆盖率
            total_width = grid_cols * cell_size
            total_height = grid_rows * cell_size
            width_coverage = dx / total_width
            height_coverage = dy / total_height
            
            # 记录详细的计算信息以便调试
            self._add_log(f"预估的横向格子数: {approx_grid_width:.1f}")
            self._add_log(f"预估的纵向格子数: {approx_grid_height:.1f}")
            self._add_log(f"识别可信度: 24格={score_24:.2f}, 12格={score_12:.2f}")
            self._add_log(f"网格覆盖率: 宽度 {width_coverage:.2%}, 高度 {height_coverage:.2%}")

            self._add_log("\n----- 仓库类型识别结果 -----")
            self._add_log(f"类型: {stash_type}")
            self._add_log(f"格子数量: {grid_cols * grid_rows} 个 ({grid_cols}x{grid_rows})")
            self._add_log(f"锚点平均尺寸: {cell_size:.1f} 像素")
            self._add_log(f"锚点间距: 横向 {dx:.1f} 像素, 纵向 {dy:.1f} 像素")
            
            # ---------- 绘制识别结果 ----------
            # 计算预览缩放比例
            preview_width = 800
            scale_factor = preview_width / original_image.width
            
            # 计算得到的实际格子大小
            self._add_log(f"计算得到的格子尺寸: {cell_size:.1f}x{cell_size:.1f} 像素")
            
            # 在预览图像上绘制结果
            # 绘制窗口中心线（黄色）
            cv2.line(processed_image, 
                    (int(window_center_x * scale_factor), 0), 
                    (int(window_center_x * scale_factor), int(img_h * scale_factor)), 
                    (0, 255, 255), 1)
                    
            # 绘制标记点
            # 左上角标记点（绿色）
            tl_pos = top_left_marker['pos']
            tl_size = top_left_marker['size']
            cv2.rectangle(processed_image,
                        (int(tl_pos[0] * scale_factor), int(tl_pos[1] * scale_factor)),
                        (int((tl_pos[0] + tl_size[0]) * scale_factor), int((tl_pos[1] + tl_size[1]) * scale_factor)),
                        (0, 255, 0), 2)
            cv2.putText(processed_image, "TL",
                       (int(tl_pos[0] * scale_factor), int(tl_pos[1] * scale_factor - 5)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # 右下角标记点（蓝色）
            br_pos = bottom_right_marker['pos']
            br_size = bottom_right_marker['size']
            cv2.rectangle(processed_image,
                        (int(br_pos[0] * scale_factor), int(br_pos[1] * scale_factor)),
                        (int((br_pos[0] + br_size[0]) * scale_factor), int((br_pos[1] + br_size[1]) * scale_factor)),
                        (255, 0, 0), 2)
            cv2.putText(processed_image, "BR",
                       (int(br_pos[0] * scale_factor), int(br_pos[1] * scale_factor - 5)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                       
            # 使用锚点位置直接定位网格
            grid_start_x = tl_pos[0]  # 左上角X
            grid_start_y = tl_pos[1]  # 左上角Y
            grid_end_x = br_pos[0] + br_size[0]  # 右下角X（包括物品大小）
            grid_end_y = br_pos[1] + br_size[1]  # 右下角Y（包括物品大小）

            # 根据实际距离重新计算格子大小
            cell_width = (grid_end_x - grid_start_x) / grid_cols
            cell_height = (grid_end_y - grid_start_y) / grid_rows

            # 使用较小的值作为统一格子大小
            cell_size = min(cell_width, cell_height)
            
            # 计算实际的网格总大小
            total_width = grid_cols * cell_size
            total_height = grid_rows * cell_size
            
            # 从左上角开始绘制水平线
            for i in range(grid_rows + 1):
                y = grid_start_y + i * cell_size
                start_x = int(grid_start_x * scale_factor)
                end_x = int((grid_start_x + total_width) * scale_factor)
                line_y = int(y * scale_factor)
                cv2.line(processed_image, 
                        (start_x, line_y),
                        (end_x, line_y),
                        (255, 255, 255), 1)
            
            # 从左上角开始绘制垂直线
            for j in range(grid_cols + 1):
                x = grid_start_x + j * cell_size
                start_y = int(grid_start_y * scale_factor)
                end_y = int((grid_start_y + total_height) * scale_factor)
                line_x = int(x * scale_factor)
                cv2.line(processed_image,
                        (line_x, start_y),
                        (line_x, end_y),
                        (255, 255, 255), 1)
                        
            # 计算覆盖率（考虑锚点物品大小）
            actual_width = grid_end_x - grid_start_x
            actual_height = grid_end_y - grid_start_y
            grid_coverage_x = total_width / actual_width
            grid_coverage_y = total_height / actual_height
            
            # 计算实际网格中心点
            grid_center_x = grid_start_x + actual_width / 2
            grid_center_y = grid_start_y + actual_height / 2
            
            # 绘制实际网格中心点（红色十字）
            cross_size = 10
            center_x_scaled = int(grid_center_x * scale_factor)
            center_y_scaled = int(grid_center_y * scale_factor)
            
            cv2.line(processed_image,
                    (center_x_scaled - cross_size, center_y_scaled),
                    (center_x_scaled + cross_size, center_y_scaled),
                    (0, 0, 255), 2)
            cv2.line(processed_image,
                    (center_x_scaled, center_y_scaled - cross_size),
                    (center_x_scaled, center_y_scaled + cross_size),
                    (0, 0, 255), 2)
            
            # 在中心点旁添加标签
            cv2.putText(processed_image, "C",
                       (center_x_scaled + cross_size + 5, center_y_scaled + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # 在日志中添加详细信息
            self._add_log(f"网格范围: 左上({grid_start_x:.1f}, {grid_start_y:.1f})")
            self._add_log(f"          右下({grid_end_x:.1f}, {grid_end_y:.1f})")
            self._add_log(f"网格大小: {actual_width:.1f}x{actual_height:.1f} 像素")
            self._add_log(f"格子大小: {cell_size:.1f}x{cell_size:.1f} 像素")
            self._add_log(f"网格覆盖比例: X={grid_coverage_x:.2%}, Y={grid_coverage_y:.2%}")
            self._add_log(f"网格中心点: ({grid_center_x:.1f}, {grid_center_y:.1f})")
            
            # 更新预览图像
            processed_pil = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
            photo = ImageTk.PhotoImage(processed_pil)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
            
            # 显示最终识别结果
            self._add_log("\n----- 定位结果 -----")
            self._add_log("✅ 识别成功！")
            self._add_log(f"仓库类型: {stash_type}")
            self._add_log(f"单元格大小: {cell_width:.1f}x{cell_height:.1f} 像素")
            self._add_log(f"总区域大小: {dx:.1f}x{dy:.1f} 像素")
            self.update_status("✅ 定位识别成功")

            # 执行指定位置的Ctrl+左键点击
            self._add_log("\n----- 执行自动点击 -----")
            
            # 计算左3上5的位置
            x1 = grid_start_x + (1 * cell_size) + (cell_size / 2)  # 左3，从0开始计数所以是2
            y1 = grid_start_y + (0 * cell_size) + (cell_size / 2)  # 上5，从0开始计数所以是4
            

            # 获取窗口句柄
            hwnd = win32gui.FindWindow(None, self._get_window_name())
            if hwnd:
                # 转换为屏幕坐标
                rect = win32gui.GetWindowRect(hwnd)
                screen_x1 = int(x1) + rect[0]
                screen_y1 = int(y1) + rect[1]
                
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

                    # 执行第一个点击 (左3上5)
                    click_at(screen_x1, screen_y1)
                    win32api.Sleep(1000)

                    # 释放Ctrl键
                    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                    
                    self._add_log("✅ 自动点击完成")
                    self._add_log(f"已点击位置：左3上5 ({screen_x1}, {screen_y1})")
                    self._add_log(f"已点击位置：左5上10 ({screen_x2}, {screen_y2})")
                except Exception as e:
                    self._add_log(f"自动点击失败: {str(e)}", "ERROR")
            else:
                self._add_log("❌ 未找到游戏窗口，无法执行点击", "ERROR")

        except Exception as e:
            self._add_log(f"识别过程出错: {str(e)}", "ERROR")
            self.update_status("❌ 识别失败")
