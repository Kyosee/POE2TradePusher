import cv2
import numpy as np
import threading
import time
from PIL import Image
import win32gui
import win32con
import win32ui
from typing import Dict, List, Tuple, Optional, Union, Callable
import os
import json

from ..process_module import ProcessModule
from utils.model_loader import YOLOModelLoader
from gui.utils import switch_to_window

class ItemRecognitionModule(ProcessModule):
    """物品识别模块 - 使用YOLOv12识别游戏窗口内的物品"""
    
    def __init__(self):
        """初始化物品识别模块"""
        super().__init__()
        self.yolo_loader = YOLOModelLoader()
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_lock = threading.Lock()
        self.last_result = None
        self.callback = None
        
    def name(self) -> str:
        return "物品识别"
        
    def description(self) -> str:
        return "使用YOLOv12识别游戏窗口内的物品"
    
    def _get_window_name(self):
        """获取游戏窗口名称"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('game_window', 'Path of Exile 2')
        except Exception as e:
            self.logger.error(f"读取配置文件失败: {str(e)}")
            return 'Path of Exile 2'

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
        
        # 清理资源
        win32gui.DeleteDC(save_dc)
        win32gui.ReleaseDC(0, hwnd_dc)
        win32gui.ReleaseDC(0, mfc_dc)
        
        return img

    def _convert_to_cv(self, pil_image):
        """将PIL图像转换为OpenCV格式"""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def _divide_image(self, image):
        """将图像划分为四等分，返回左上和左下区域"""
        height, width = image.shape[:2]
        half_height = height // 2
        half_width = width // 2
        
        # 左上区域
        top_left = image[0:half_height, 0:half_width]
        # 左下区域
        bottom_left = image[half_height:height, 0:half_width]
        
        return top_left, bottom_left
    
    def _draw_detection_boxes(self, image, detections, item_name=None):
        """在图像上绘制检测框"""
        result_image = image.copy()
        
        if not detections or len(detections) == 0:
            return result_image
            
        # 获取检测结果
        boxes = detections.boxes.cpu().numpy()
        
        for box in boxes:
            # 如果指定了物品名称，则只显示匹配的物品
            if item_name is not None:
                cls_id = int(box.cls[0])
                cls_name = self.yolo_loader.supported_items[cls_id]
                if cls_name != item_name:
                    continue
            
            # 获取边界框坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = box.conf[0]
            cls_name = self.yolo_loader.supported_items[cls_id]
            
            # 绘制边界框
            color = (0, 255, 0)  # 绿色
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            label = f"{cls_name}: {conf:.2f}"
            cv2.putText(result_image, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return result_image
    
    def _filter_detections(self, detections, item_name=None):
        """过滤检测结果，只返回指定物品名称的结果"""
        if not detections or len(detections) == 0:
            return []
            
        result = []
        boxes = detections.boxes.cpu().numpy()
        
        for box in boxes:
            cls_id = int(box.cls[0])
            cls_name = self.yolo_loader.supported_items[cls_id]
            
            # 如果指定了物品名称，则只返回匹配的物品
            if item_name is not None and cls_name != item_name:
                continue
                
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            
            # 计算中心点坐标
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            result.append({
                'name': cls_name,
                'confidence': conf,
                'box': (x1, y1, x2, y2),
                'center': (center_x, center_y)
            })
        
        return result
    
    def recognize_items(self, item_name=None, generate_preview=False):
        """识别游戏窗口中的物品
        
        Args:
            item_name: 物品名称，如果指定则只返回该物品的识别结果
            generate_preview: 是否生成预览图像
            
        Returns:
            dict: 包含识别结果的字典
        """
        # 确保YOLO模型已加载
        if not self.yolo_loader.is_loaded():
            self.logger.info("YOLO模型尚未加载，正在加载...")
            self.yolo_loader.load_model_async()
            while not self.yolo_loader.is_loaded():
                time.sleep(0.1)
        
        # 获取游戏窗口截图
        window_name = self._get_window_name()
        hwnd = self._find_window(window_name)
        if not hwnd:
            self.logger.error(f"未找到游戏窗口: {window_name}")
            return {'success': False, 'error': f"未找到游戏窗口: {window_name}"}
            
        rect = self._get_window_rect(hwnd)
        original_image = self._grab_screen(rect)
        original_cv = self._convert_to_cv(original_image)
        
        # 划分图像区域，只处理左上和左下
        top_left, bottom_left = self._divide_image(original_cv)
        
        # 使用YOLO模型进行物品识别
        model = self.yolo_loader.get_model()
        
        # 对左上和左下区域进行识别
        top_left_results = model(top_left)
        bottom_left_results = model(bottom_left)
        
        # 处理识别结果
        top_left_items = self._filter_detections(top_left_results[0], item_name)
        bottom_left_items = self._filter_detections(bottom_left_results[0], item_name)
        
        # 调整底部区域的坐标（加上top_left的高度）
        for item in bottom_left_items:
            item['center'] = (item['center'][0], item['center'][1] + top_left.shape[0])
            x1, y1, x2, y2 = item['box']
            item['box'] = (x1, y1 + top_left.shape[0], x2, y2 + top_left.shape[0])
        
        # 合并结果
        all_items = top_left_items + bottom_left_items
        
        # 统计每种物品的数量
        item_counts = {}
        for item in all_items:
            name = item['name']
            if name in item_counts:
                item_counts[name] += 1
            else:
                item_counts[name] = 1
        
        result = {
            'success': True,
            'items': all_items,
            'counts': item_counts,
            'total': len(all_items)
        }
        
        # 如果需要生成预览图像
        if generate_preview:
            # 在原始图像上绘制检测区域
            preview = original_cv.copy()
            height, width = preview.shape[:2]
            half_height = height // 2
            half_width = width // 2
            
            # 绘制检测区域边界
            cv2.rectangle(preview, (0, 0), (half_width, half_height), (255, 0, 0), 2)  # 左上区域
            cv2.rectangle(preview, (0, half_height), (half_width, height), (255, 0, 0), 2)  # 左下区域
            
            # 在左上区域绘制检测框
            top_left_preview = self._draw_detection_boxes(top_left, top_left_results[0], item_name)
            preview[0:half_height, 0:half_width] = top_left_preview
            
            # 在左下区域绘制检测框
            bottom_left_preview = self._draw_detection_boxes(bottom_left, bottom_left_results[0], item_name)
            preview[half_height:height, 0:half_width] = bottom_left_preview
            
            result['preview'] = preview
        
        return result
    
    def start_monitoring(self, callback=None, item_name=None, interval=0.5):
        """开始持续监测游戏窗口中的物品
        
        Args:
            callback: 回调函数，接收识别结果
            item_name: 物品名称，如果指定则只监测该物品
            interval: 监测间隔，单位为秒
        """
        if self.monitoring:
            self.logger.info("物品识别监测已经在运行中")
            return False
        
        self.callback = callback
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_thread,
            args=(item_name, interval),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("物品识别监测已启动")
        return True
    
    def stop_monitoring(self):
        """停止物品监测"""
        if not self.monitoring:
            self.logger.info("物品识别监测未在运行")
            return False
        
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        self.logger.info("物品识别监测已停止")
        return True
    
    def _monitor_thread(self, item_name=None, interval=0.5):
        """监测线程函数
        
        Args:
            item_name: 物品名称，如果指定则只监测该物品
            interval: 监测间隔，单位为秒
        """
        while self.monitoring:
            try:
                with self.monitor_lock:
                    # 执行物品识别
                    result = self.recognize_items(item_name, generate_preview=True)
                    self.last_result = result
                    
                    # 如果有回调函数，则调用回调函数
                    if self.callback:
                        self.callback(result)
            except Exception as e:
                self.logger.error(f"物品识别监测异常: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
            
            # 等待指定的间隔时间
            time.sleep(interval)
    
    def run(self, **kwargs):
        """运行物品识别模块
        
        Args:
            item_name: 物品名称，如果指定则只返回该物品的识别结果
            generate_preview: 是否生成预览图像，默认为False
            preview_callback: 预览图像回调函数，用于显示预览图像
            
        Returns:
            dict: 包含识别结果的字典
        """
        item_name = kwargs.get('item_name')
        generate_preview = kwargs.get('generate_preview', False)
        preview_callback = kwargs.get('preview_callback')
        
        # 执行物品识别
        result = self.recognize_items(item_name, generate_preview)
        
        # 如果有预览回调函数且生成了预览图像，则调用回调函数
        if preview_callback and generate_preview and result.get('success') and 'preview' in result:
            preview_callback(result['preview'])
        
        return result