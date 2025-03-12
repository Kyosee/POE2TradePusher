import cv2
import numpy as np
import time
import win32gui
import win32api
import win32con
from PIL import Image, ImageDraw, ImageEnhance
import os
import torch
from core.process_module import ProcessModule
from gui.pages.recognition_base_page import RecognitionBasePage
from gui.utils import switch_to_window
import logging
from utils.model_loader import YOLOModelLoader

class TradeMonitorModule(ProcessModule):
    """交易监测流程模块"""
    
    def __init__(self):
        super().__init__()
        self.recognition_base = None
        self.preview_image = None
        self.show_preview = False
        self.monitoring = False
        self.trade_title_template = cv2.imread("assets/rec/trade_title.png")
        
        # 添加高级参数，可以通过配置调整
        self.detection_threshold = 0.45  # 检测置信度阈值
        self.enable_advanced_detection = True
        self.debug_mode = False
        
        # 使用YOLO模型加载器
        self._yolo_loader = YOLOModelLoader()
        self.supported_currencies = {}
        
        if self.trade_title_template is None:
            self.logger.warning("⚠️ 交易窗口模板图片加载失败")
            
        # 异步加载YOLO模型
        self._yolo_loader.load_model_async()

    def name(self) -> str:
        return "交易监测"

    def description(self) -> str:
        return "监测交易窗口中对方放入的通货物品数量"
    
    def _get_yolo_model(self):
        """获取YOLO模型实例"""
        if self._yolo_loader.is_loaded():
            # 更新支持的通货类型
            self.supported_currencies = self._yolo_loader.supported_currencies
            return self._yolo_loader.get_model()
        else:
            # 如果模型尚未加载，尝试同步加载
            try:
                self.logger.info("YOLO模型尚未加载，正在尝试加载...")
                self._yolo_loader._load_model_impl()
                # 更新支持的通货类型
                self.supported_currencies = self._yolo_loader.supported_currencies
                return self._yolo_loader.get_model()
            except Exception as e:
                self.logger.error(f"YOLO模型加载失败: {str(e)}")
                return None
    
    def start_monitoring(self):
        """开始监测"""
        self.monitoring = True
        return True
    
    def stop_monitoring(self):
        """停止监测"""
        self.monitoring = False
        return True
    
    def is_monitoring(self):
        """返回当前监测状态"""
        return self.monitoring

    def run(self, **kwargs):
        """运行模块，监测交易窗口中对方放入的通货物品数量
        
        Args:
            username: 用户名
            currency_type: 通货类型（YOLO模型支持的类别名称）
            show_preview: 是否返回标注了匹配区域的预览图
            detection_threshold: 可选，检测阈值
            enable_advanced_detection: 可选，是否启用高级检测
            debug_mode: 可选，调试模式
            
        Returns:
            tuple: (是否成功, 识别到的物品数量, 预览图像)
        """
        username = kwargs.get('username')
        currency_type = kwargs.get('currency_type')
        self.show_preview = kwargs.get('show_preview', False)
        self.detection_threshold = kwargs.get('detection_threshold', self.detection_threshold)
        self.enable_advanced_detection = kwargs.get('enable_advanced_detection', self.enable_advanced_detection)
        self.debug_mode = kwargs.get('debug_mode', self.debug_mode)
        
        if not username:
            self.logger.error("未指定用户名")
            return False, 0, None
            
        # 确保模型已加载
        model = self._get_yolo_model()
        if model is None:
            self.logger.error("YOLO模型未加载，无法进行通货识别")
            return False, 0, None
        
        # 设置当前的检测阈值
        if model.conf != self.detection_threshold:
            model.conf = self.detection_threshold
                
        # 如果指定了通货类型，确认它在支持列表中    
        if currency_type and currency_type not in self.supported_currencies.values():
            self.logger.warning(f"指定的通货类型 '{currency_type}' 不在支持列表中")
            self.logger.info(f"支持的通货类型: {self.supported_currencies}")
            # 不直接返回错误，继续检测所有类型通货
            
        if not self.recognition_base:
            # 创建一个RecognitionBasePage实例来使用其功能
            self.recognition_base = RecognitionBasePage(None, self._log_callback, self._status_callback)
        
        try:
            # 获取游戏窗口
            window_name = self.recognition_base._get_window_name()
            hwnd = self.recognition_base._find_window(window_name)
            if not hwnd:
                self.logger.error(f"未找到游戏窗口: {window_name}")
                return False, 0, None

            # 切换到游戏窗口
            switch_to_window(window_name)
            # 等待窗口激活
            time.sleep(0.2)

            # 获取窗口区域并截图
            rect = self.recognition_base._get_window_rect(hwnd)
            original_image = self.recognition_base._grab_screen(rect)
            original_cv = self.recognition_base._convert_to_cv(original_image)
            
            # 获取图像尺寸
            img_h, img_w = original_cv.shape[:2]
            
            # 识别交易窗口
            trade_window_rect = self._detect_trade_window(original_cv)
            if trade_window_rect is None:
                self.logger.warning("未检测到交易窗口")
                return False, 0, None
                
            # 获取游戏窗口尺寸
            window_height, window_width = original_cv.shape[:2]
            
            # 计算交易区域位置（基于游戏窗口尺寸的固定比例）
            x = int(window_width * 0.05)  # 交易区域起始于窗口宽度的5%处
            y = int(window_height * 0.1)  # 交易区域起始于窗口高度的10%处
            w = int(window_width * 0.5)   # 交易区域宽度为窗口宽度的50%
            h = int(window_height * 0.7)  # 交易区域高度为窗口高度的70%
            
            # 划分交易区域
            trade_area_height = h // 2
            
            # 对方交易区域（上半部分）
            other_trade_area = original_cv[y:y+trade_area_height, x:x+w]
            
            # 我方交易区域（下半部分）
            my_trade_area = original_cv[y+trade_area_height:y+h, x:x+w]
            
            # 使用YOLO模型识别对方放入的通货物品
            item_count, detected_items, marked_image = self._detect_currency_with_yolo(
                other_trade_area,
                original_cv,
                (x, y, w, trade_area_height),
                currency_type
            )
            
            # 如果需要预览，在原图上标记识别区域和结果
            if self.show_preview:
                # 转换回PIL图像用于绘制
                pil_image = Image.fromarray(cv2.cvtColor(marked_image, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_image)
                    
                # 标记交易窗口
                draw.rectangle([x, y, x+w, y+h], outline="blue", width=3)
                    
                # 标记对方交易区域
                draw.rectangle([x, y, x+w, y+trade_area_height], outline="green", width=3)
                    
                # 标记我方交易区域
                draw.rectangle([x, y+trade_area_height, x+w, y+h], outline="yellow", width=3)
                    
                # 添加文本标注
                font_size = 20
                # 添加半透明背景以增强文本可读性
                text_bg_color = (0, 0, 0, 128)  # 半透明黑色
                
                # 如果有检测到物品，将信息标注在第一个物品的上方
                if detected_items:
                    # 获取第一个物品的位置
                    first_item = detected_items[0]
                    box_x1, box_y1, box_x2, box_y2 = first_item['box']
                    
                    # 对方信息 - 放在物品上方
                    text = f"对方: {username}"
                    draw.rectangle([box_x1, box_y1-60, box_x1+200, box_y1-30], fill=text_bg_color)
                    draw.text((box_x1+10, box_y1-55), text, fill="white")
                    
                    # 通货类型信息 - 放在物品上方
                    if currency_type:
                        text = f"通货: {currency_type}"
                        draw.rectangle([box_x1, box_y1-30, box_x1+200, box_y1], fill=text_bg_color)
                        draw.text((box_x1+10, box_y1-25), text, fill="white")
                    
                    # 数量信息 - 放在物品下方，使用更大字体和醒目颜色
                    text = f"数量: {item_count}"
                    draw.rectangle([box_x1, box_y2+5, box_x1+200, box_y2+35], fill=text_bg_color)
                    draw.text((box_x1+10, box_y2+10), text, fill="#FFFF00")  # 黄色文本
                else:
                    # 如果没有检测到物品，则使用原来的固定位置
                    # 对方信息
                    text = f"对方: {username}"
                    draw.rectangle([x, y-30, x+200, y], fill=text_bg_color)
                    draw.text((x+10, y-25), text, fill="white")
                    
                    # 通货类型信息
                    if currency_type:
                        text = f"通货: {currency_type}"
                        draw.rectangle([x, y+h+5, x+200, y+h+35], fill=text_bg_color)
                        draw.text((x+10, y+h+10), text, fill="white")
                    
                    # 数量信息 - 使用更大字体和醒目颜色
                    text = f"数量: {item_count}"
                    draw.rectangle([x, y+h+40, x+200, y+h+70], fill=text_bg_color)
                    draw.text((x+10, y+h+45), text, fill="#FFFF00")  # 黄色文本
                
                # 添加检测时间戳 - 始终放在右上角
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                draw.rectangle([x+w-250, y-30, x+w, y], fill=text_bg_color)
                draw.text((x+w-240, y-25), f"时间: {timestamp}", fill="white")
                    
                # 保存预览图
                self.preview_image = pil_image
            
            return True, item_count, self.preview_image if self.show_preview else None
                
        except Exception as e:
            self.logger.error(f"交易监测失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False, 0, None
    
    def _detect_trade_window(self, image):
        """检测交易窗口位置
        
        Args:
            image: 原始图像
            
        Returns:
            tuple: (x, y, w, h) 交易窗口的位置和大小，如果未检测到则返回None
        """
        try:
            # 转换并预处理图像
            gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(self.trade_title_template, cv2.COLOR_BGR2GRAY)
            
            # 使用自适应直方图均衡化增强对比度
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray_img = clahe.apply(gray_img)
            gray_template = clahe.apply(gray_template)
            
            # 使用高斯模糊减少噪声
            gray_img = cv2.GaussianBlur(gray_img, (3, 3), 0)
            gray_template = cv2.GaussianBlur(gray_template, (3, 3), 0)
            
            # 获取模板原始尺寸
            template_h, template_w = gray_template.shape
            
            # 计算合适的缩放范围
            img_h, img_w = gray_img.shape
            min_scale = max(0.2, template_w / img_w * 0.3)  # 扩大缩放范围
            max_scale = min(4.0, img_w / template_w * 0.7)  # 扩大缩放范围
            
            # 生成更密集的缩放系数序列
            scales = np.linspace(min_scale, max_scale, 30)  # 增加缩放步数
            
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
            threshold = 0.6  # 降低匹配阈值
            
            if max_val_overall >= threshold:
                # 获取匹配位置
                top_left = max_loc_overall
                
                # 估计交易窗口大小（根据标题栏位置推断）
                # 交易窗口宽度约为标题栏宽度的1.2倍
                window_width = int(best_w * 1.2)
                # 交易窗口高度约为标题栏高度的10倍
                window_height = int(best_h * 10)
                
                # 返回交易窗口位置和大小
                return (top_left[0], top_left[1] + best_h, window_width, window_height)
            
            return None
            
        except Exception as e:
            self.logger.error(f"检测交易窗口失败: {str(e)}")
            return None
    
    def _detect_currency_with_yolo(self, trade_area, original_image, area_rect, target_currency=None):
        """使用YOLOv11模型检测交易区域中的通货物品
        
        Args:
            trade_area: 交易区域图像
            original_image: 原始图像（用于标记）
            area_rect: 交易区域在原始图像中的位置 (x, y, w, h)
            target_currency: 目标通货类型，None表示检测所有类型
            
        Returns:
            tuple: (物品总数量, 检测到的物品详情列表, 标记后的图像)
        """
        try:
            # 创建调试图像
            debug_images = {}
            if self.debug_mode:
                debug_images['trade_area'] = trade_area
            
            # 增强图像预处理，使YOLO更容易识别
            enhanced_trade_area = self._enhance_image(trade_area)
            
            if self.debug_mode:
                debug_images['enhanced_area'] = enhanced_trade_area
            
            # 获取偏移量
            x_offset, y_offset, _, _ = area_rect
            
            # 创建标记图像副本
            marked_image = original_image.copy()
            
            # 获取YOLO模型
            model = self._get_yolo_model()
            if model is None:
                return 0, [], original_image
                
            # 使用YOLOv11模型进行检测
            results = model(enhanced_trade_area)
            
            # 获取检测结果 - YOLOv11可能有不同的结果格式
            try:
                # 适用于YOLOv8+的结果格式
                if hasattr(results, 'pandas') and callable(getattr(results, 'pandas')):
                    detections = results.pandas().xyxy[0]  # 以pandas DataFrame格式获取结果
                # 适用于YOLOv5的结果格式
                elif hasattr(results, 'xyxy') and isinstance(results.xyxy, list):
                    detections = results.pandas().xyxy[0]
                # YOLOv11特有格式
                elif hasattr(results, 'boxes'):
                    # 直接从YOLOv11的结果对象中提取数据
                    boxes = results.boxes.cpu().numpy()
                    detections = []
                    for i in range(len(boxes)):
                        box = boxes[i]
                        x1, y1, x2, y2 = box.xyxy[0]
                        conf = box.conf[0]
                        cls_id = int(box.cls[0])
                        class_name = model.names[cls_id]  # 使用model而不是self.model
                        
                        detections.append({
                            'xmin': x1, 'ymin': y1, 'xmax': x2, 'ymax': y2,
                            'confidence': conf, 'name': class_name
                        })
                else:
                    # 通用处理方式
                    detections = []
                    if hasattr(results, 'pred') and isinstance(results.pred, list) and len(results.pred) > 0:
                        pred = results.pred[0]
                        for *xyxy, conf, cls_id in pred.cpu().numpy():
                            x1, y1, x2, y2 = xyxy
                            class_name = model.names[int(cls_id)]  # 使用model而不是self.model
                            detections.append({
                                'xmin': x1, 'ymin': y1, 'xmax': x2, 'ymax': y2,
                                'confidence': conf, 'name': class_name
                            })
            except Exception as e:
                self.logger.error(f"处理YOLOv11结果时出错: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                return 0, [], original_image
            
            # 过滤结果只保留目标通货类型（如果指定）
            if target_currency and isinstance(detections, list):
                filtered_detections = []
                for det in detections:
                    if det['name'] == target_currency:
                        filtered_detections.append(det)
                detections = filtered_detections
            elif target_currency:  # 如果是DataFrame
                try:
                    detections = detections[detections['name'] == target_currency]
                except:
                    pass
            
            # 创建检测到的物品列表
            detected_items = []
            
            # 在标记图像上绘制检测框
            if isinstance(detections, list):
                # 处理列表形式的检测结果
                for det in detections:
                    x1, y1, x2, y2 = int(det['xmin']), int(det['ymin']), int(det['xmax']), int(det['ymax'])
                    conf = det['confidence']
                    class_name = det['name']
                    
                    # 计算在原图上的位置
                    abs_x1 = x1 + x_offset
                    abs_y1 = y1 + y_offset
                    abs_x2 = x2 + x_offset
                    abs_y2 = y2 + y_offset
                    
                    # 添加到检测列表
                    detected_items.append({
                        'type': class_name,
                        'confidence': conf,
                        'box': (abs_x1, abs_y1, abs_x2, abs_y2)
                    })
                    
                    # 设置不同类型的颜色 - 使用更丰富的颜色方案
                    class_names = list(self.supported_currencies.values()) if hasattr(self.supported_currencies, 'values') else list(self.supported_currencies)
                    try:
                        class_id = class_names.index(class_name) if class_name in class_names else 0
                    except:
                        class_id = 0
                    # 使用更多颜色以区分不同类型
                    colors = [
                        (0, 255, 0),    # 绿色
                        (255, 0, 0),    # 蓝色
                        (0, 0, 255),    # 红色
                        (255, 255, 0),  # 青色
                        (0, 255, 255),  # 黄色
                        (255, 0, 255),  # 紫色
                        (255, 128, 0),  # 橙色
                        (128, 0, 255),  # 紫蓝色
                        (0, 128, 255),  # 橙红色
                        (128, 255, 0)   # 黄绿色
                    ]
                    color_id = class_id % len(colors)
                    color = colors[color_id]
                    
                    # 绘制更明显的矩形框，增加线宽
                    cv2.rectangle(marked_image, 
                                (abs_x1, abs_y1), 
                                (abs_x2, abs_y2), 
                                color, 4)  # 增加线宽到4
                    
                    # 绘制半透明填充区域以突出显示物品
                    overlay = marked_image.copy()
                    cv2.rectangle(overlay, (abs_x1, abs_y1), (abs_x2, abs_y2), color, -1)  # 填充矩形
                    cv2.addWeighted(overlay, 0.3, marked_image, 0.7, 0, marked_image)  # 增加透明度以更明显
                    
                    # 添加更醒目的标签背景
                    label = f"{class_name}: {conf:.2f}"
                    # 使用更大的字体
                    font_scale = 0.8
                    thickness = 2
                    (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                    
                    # 标签背景使用黑色以增加对比度
                    cv2.rectangle(marked_image, 
                                (abs_x1, abs_y1-label_h-10), 
                                (abs_x1+label_w+10, abs_y1), 
                                (0, 0, 0), -1)  # 黑色背景
                    
                    # 添加白色文本以增加对比度
                    cv2.putText(marked_image, label, (abs_x1+5, abs_y1-7), 
                              cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
            else:
                # 处理DataFrame形式的检测结果
                for _, det in detections.iterrows():
                    x1, y1, x2, y2 = int(det['xmin']), int(det['ymin']), int(det['xmax']), int(det['ymax'])
                    conf = det['confidence']
                    class_name = det['name']
                    
                    # 计算在原图上的位置
                    abs_x1 = x1 + x_offset
                    abs_y1 = y1 + y_offset
                    abs_x2 = x2 + x_offset
                    abs_y2 = y2 + y_offset
                    
                    # 添加到检测列表
                    detected_items.append({
                        'type': class_name,
                        'confidence': conf,
                        'box': (abs_x1, abs_y1, abs_x2, abs_y2)
                    })
                    
                    # 确定颜色 (使用更丰富的颜色方案)
                    class_names = list(self.supported_currencies.values()) if hasattr(self.supported_currencies, 'values') else list(self.supported_currencies)
                    try:
                        class_id = class_names.index(class_name) if class_name in class_names else 0
                    except:
                        class_id = 0
                    # 使用更多颜色以区分不同类型
                    colors = [
                        (0, 255, 0),    # 绿色
                        (255, 0, 0),    # 蓝色
                        (0, 0, 255),    # 红色
                        (255, 255, 0),  # 青色
                        (0, 255, 255),  # 黄色
                        (255, 0, 255),  # 紫色
                        (255, 128, 0),  # 橙色
                        (128, 0, 255),  # 紫蓝色
                        (0, 128, 255),  # 橙红色
                        (128, 255, 0)   # 黄绿色
                    ]
                    color_id = class_id % len(colors)
                    color = colors[color_id]
                    
                    # 绘制更明显的矩形框，增加线宽
                    cv2.rectangle(marked_image, 
                                (abs_x1, abs_y1), 
                                (abs_x2, abs_y2), 
                                color, 4)  # 增加线宽到4
                    
                    # 绘制半透明填充区域以突出显示物品
                    overlay = marked_image.copy()
                    cv2.rectangle(overlay, (abs_x1, abs_y1), (abs_x2, abs_y2), color, -1)  # 填充矩形
                    cv2.addWeighted(overlay, 0.3, marked_image, 0.7, 0, marked_image)  # 增加透明度以更明显
                    
                    # 添加更醒目的标签背景
                    label = f"{class_name}: {conf:.2f}"
                    # 使用更大的字体
                    font_scale = 0.8
                    thickness = 2
                    (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                    
                    # 标签背景使用黑色以增加对比度
                    cv2.rectangle(marked_image, 
                                (abs_x1, abs_y1-label_h-10), 
                                (abs_x1+label_w+10, abs_y1), 
                                (0, 0, 0), -1)  # 黑色背景
                    
                    # 添加白色文本以增加对比度
                    cv2.putText(marked_image, label, (abs_x1+5, abs_y1-7), 
                              cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
            
            if self.debug_mode:
                # 如果是调试模式，保存所有调试图像
                debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_images")
                os.makedirs(debug_dir, exist_ok=True)
                
                timestamp = int(time.time())
                for name, img in debug_images.items():
                    try:
                        cv2.imwrite(os.path.join(debug_dir, f"{name}_{timestamp}.png"), img)
                    except Exception as e:
                        self.logger.debug(f"保存调试图像失败 {name}: {str(e)}")
                
                # 保存YOLO结果图像
                try:
                    results_img = results.plot()[0] if hasattr(results, 'plot') else None
                    if results_img is not None:
                        cv2.imwrite(os.path.join(debug_dir, f"yolo_results_{timestamp}.png"), results_img)
                except Exception as e:
                    self.logger.debug(f"保存YOLO结果图像失败: {str(e)}")
            
            # 计算检测到的物品数量
            item_count = len(detected_items)
            
            return item_count, detected_items, marked_image
            
        except Exception as e:
            self.logger.error(f"YOLOv11检测通货失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return 0, [], original_image
    
    def _enhance_image(self, image):
        """增强图像质量
        
        Args:
            image: 原始图像
            
        Returns:
            numpy.ndarray: 增强后的图像
        """
        try:
            # 转换为PIL图像进行增强
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # 提高对比度
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(1.5)
            
            # 提高清晰度
            enhancer = ImageEnhance.Sharpness(pil_image)
            pil_image = enhancer.enhance(1.5)
            
            # 转回OpenCV格式
            enhanced = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # 应用去噪
            enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
            
            return enhanced
        except Exception as e:
            self.logger.debug(f"图像增强失败: {str(e)}")
            return image
    
    def _log_callback(self, message, level="INFO"):
        """日志回调"""
        print(f"[{level}] {message}")

    def _status_callback(self, message):
        """状态回调"""
        print(message)
        
    def continuous_monitoring(self, username, currency_type, callback=None):
        """持续监测交易窗口
        
        Args:
            username: 用户名
            currency_type: 通货类型
            callback: 回调函数，接收物品数量变化的通知
            
        Returns:
            None
        """
        if not self.monitoring:
            self.logger.warning("监测未启动")
            return
            
        last_count = 0
        
        try:
            while self.monitoring:
                success, count, _ = self.run(
                    username=username,
                    currency_type=currency_type,
                    show_preview=False
                )
                
                # 如果检测成功且物品数量发生变化
                if success and count != last_count:
                    last_count = count
                    if callback:
                        callback(count)
                    self.logger.info(f"检测到物品数量变化: {count}")
                
                # 短暂休眠，避免过度占用CPU
                time.sleep(0.5)
                
        except Exception as e:
            self.logger.error(f"持续监测过程出错: {str(e)}")
            self.monitoring = False