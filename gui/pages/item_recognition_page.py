from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QComboBox, QFrame, QDialog, QScrollArea,
                              QTableWidget, QTableWidgetItem, QHeaderView, QListWidget)
from PySide6.QtCore import Qt, QEvent, QThread, Signal
from PySide6.QtGui import QPixmap, QImage, QIcon, QCursor, QWheelEvent, QTransform, QFont
import cv2
import numpy as np
import os
import json
import time

from .recognition_base_page import RecognitionBasePage
from core.process_modules.item_recognition import ItemRecognitionModule
from ..widgets.log_list import LogList  # 引入统一的日志列表组件

# 添加用于后台运行识别任务的线程类
class RecognitionThread(QThread):
    """后台识别线程"""
    result_signal = Signal(dict)  # 识别结果信号
    
    def __init__(self, item_recognition, item_name=None):
        super().__init__()
        self.item_recognition = item_recognition
        self.item_name = item_name
        
    def run(self):
        """执行识别任务"""
        try:
            # 在线程中执行识别操作
            result = self.item_recognition.run(
                item_name=self.item_name,
                generate_preview=True
            )
            # 发送结果信号
            self.result_signal.emit(result)
        except Exception as e:
            # 发送错误结果
            self.result_signal.emit({
                'success': False,
                'error': str(e)
            })

class PreviewDialog(QDialog):
    """预览图弹窗类"""
    def __init__(self, parent=None, image=None):
        super().__init__(parent)
        self.setWindowTitle("物品识别预览")
        self.setMinimumSize(900, 700)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        # 创建标签并设置图像
        self.image_label = QLabel()
        if image:
            self.original_pixmap = QPixmap.fromImage(image)
            self.image_label.setPixmap(self.original_pixmap)
        else:
            self.original_pixmap = QPixmap()
        
        # 设置标签对齐方式和缩放模式
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # 添加缩放相关变量
        self.scale_factor = 1.0
        self.zoom_step = 0.1  # 每次缩放步长
        
        # 为滚动区域安装事件过滤器，用于捕获滚轮事件
        self.scroll.viewport().installEventFilter(self)
        
        # 将标签添加到滚动区域
        self.scroll.setWidget(self.image_label)
        
        # 将滚动区域添加到布局
        layout.addWidget(self.scroll)
        
        # 添加状态栏 - 显示缩放比例
        self.status_bar = QLabel("缩放: 100%")
        layout.addWidget(self.status_bar)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 添加缩放按钮
        zoom_in_btn = QPushButton("放大(+)")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn = QPushButton("缩小(-)")
        zoom_out_btn.clicked.connect(self.zoom_out)
        reset_zoom_btn = QPushButton("重置缩放")
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        
        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        
        # 添加提示标签
        tip_label = QLabel("提示: 按住Ctrl键+滚轮可放大/缩小")
        tip_label.setStyleSheet("color: gray;")
        
        # 添加到按钮布局
        button_layout.addWidget(zoom_in_btn)
        button_layout.addWidget(zoom_out_btn)
        button_layout.addWidget(reset_zoom_btn)
        button_layout.addWidget(tip_label)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        # 将按钮布局添加到主布局
        layout.addLayout(button_layout)
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理鼠标滚轮事件"""
        if obj == self.scroll.viewport() and event.type() == QEvent.Wheel:
            wheel_event = QWheelEvent(event)
            # 检查Ctrl键是否按下
            modifiers = wheel_event.modifiers()
            if modifiers & Qt.ControlModifier:
                angle_delta = wheel_event.angleDelta().y()
                if angle_delta > 0:
                    # 向上滚动，放大
                    self.zoom_in()
                else:
                    # 向下滚动，缩小
                    self.zoom_out()
                return True  # 事件已处理
        return super().eventFilter(obj, event)
    
    def zoom_in(self):
        """放大图像"""
        self.scale_image(self.scale_factor + self.zoom_step)
    
    def zoom_out(self):
        """缩小图像"""
        self.scale_image(max(0.1, self.scale_factor - self.zoom_step))
    
    def reset_zoom(self):
        """重置缩放比例"""
        self.scale_image(1.0)
    
    def scale_image(self, factor):
        """按指定比例缩放图像"""
        if not self.original_pixmap.isNull():
            # 更新缩放因子
            self.scale_factor = factor
            
            # 计算新的尺寸
            new_size = self.original_pixmap.size() * self.scale_factor
            
            # 创建缩放后的图像
            scaled_pixmap = self.original_pixmap.scaled(
                new_size.width(),
                new_size.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # 更新图像标签
            self.image_label.setPixmap(scaled_pixmap)
            
            # 调整标签大小
            self.image_label.resize(scaled_pixmap.size())
            
            # 更新状态栏
            zoom_percentage = int(self.scale_factor * 100)
            self.status_bar.setText(f"缩放: {zoom_percentage}%")

class ItemRecognitionPage(RecognitionBasePage):
    """物品识别测试页面 - 识别游戏窗口中的物品"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        # 保存原始的日志回调函数
        self._original_add_log = callback_log
        
        # 调用父类初始化，但不使用其布局
        QWidget.__init__(self, master)
        self.update_status = callback_status
        self.main_window = main_window
        
        # 创建物品识别模块实例
        self.item_recognition_module = ItemRecognitionModule()
        
        # 监测状态
        self.is_monitoring = False
        
        # 保存最后一次图像的QImage对象
        self.last_image = None
        
        # 线程对象
        self.recognition_thread = None
        
        # 创建完全自定义的布局
        self._create_custom_layout()
        
    def _create_custom_layout(self):
        """创建完全自定义的布局，不依赖基类的布局"""
        # 创建新的主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 创建控制区域
        control_frame = QFrame()
        control_frame.setProperty('class', 'card-frame')
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加物品选择下拉框
        item_label = QLabel("物品选择:")
        self.item_combo = QComboBox()
        self.item_combo.setIconSize(QPixmap(24, 24).size())  # 设置图标大小
        self.item_combo.setMinimumWidth(200)  # 设置最小宽度
        self._load_items_to_combo()
        
        control_layout.addWidget(item_label)
        control_layout.addWidget(self.item_combo, 1)  # 设置拉伸因子为1，使其占据更多空间
        
        # 修改监测控制按钮，确保与其他按钮样式一致
        self.monitor_btn = QPushButton("▶ 开始监测")
        self.monitor_btn.clicked.connect(self._toggle_monitoring)
        self.monitor_btn.setProperty('class', 'normal-button')  # 使用normal-button样式与其他按钮一致
        control_layout.addWidget(self.monitor_btn)
        
        # 单次识别按钮
        self.single_recognize_btn = QPushButton("🔍 识别")
        self.single_recognize_btn.clicked.connect(self._start_recognition)
        self.single_recognize_btn.setProperty('class', 'normal-button')
        control_layout.addWidget(self.single_recognize_btn)
        
        # 刷新物品列表按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._refresh_items)
        refresh_btn.setProperty('class', 'normal-button')
        control_layout.addWidget(refresh_btn)
        
        self.main_layout.addWidget(control_frame)
        
        # 创建预览区域 - 调整高度分配
        preview_frame = QFrame()
        preview_frame.setProperty('class', 'card-frame')
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # 预览标题
        preview_title = QLabel("物品识别预览")
        preview_title.setProperty('class', 'card-title')
        preview_layout.addWidget(preview_title)
        
        # 创建新的预览标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(350)  # 稍微减小高度
        self.preview_label.setText("预览区域 - 点击识别按钮开始")
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        self.preview_label.setCursor(QCursor(Qt.PointingHandCursor))  # 设置鼠标指针为手型
        self.preview_label.mousePressEvent = self._on_preview_clicked  # 添加点击事件处理
        
        preview_layout.addWidget(self.preview_label)
        self.main_layout.addWidget(preview_frame, 3)  # 设置拉伸因子为3
        
        # 创建检测结果区域 - 使用表格显示结果
        result_frame = QFrame()
        result_frame.setProperty('class', 'card-frame')
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(10, 10, 10, 10)
        
        # 结果标题
        result_title = QLabel("检测结果")
        result_title.setProperty('class', 'card-title')
        result_layout.addWidget(result_title)
        
        # 创建结果表格
        self.result_table = QTableWidget(0, 3)  # 初始化为0行3列的表格
        self.result_table.setHorizontalHeaderLabels(["物品名称", "数量", "置信度"])
        
        # 设置表格格式
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # 物品名称列伸展
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 数量列自适应内容
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 置信度列自适应内容
        self.result_table.setAlternatingRowColors(True)  # 设置行交替颜色
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)  # 选择整行
        
        # 添加表格到布局
        result_layout.addWidget(self.result_table)
        
        # 添加状态文本
        self.status_text = QLabel("等待检测...")
        self.status_text.setWordWrap(True)
        self.status_text.setStyleSheet("font-size: 14px; color: #666; margin-top: 5px;")
        result_layout.addWidget(self.status_text)
        
        self.main_layout.addWidget(result_frame, 2)  # 设置拉伸因子为2
        
        # 创建日志区域
        log_frame = QFrame()
        log_frame.setProperty('class', 'card-frame')
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(10, 10, 10, 10)
        
        # 日志标题
        log_title = QLabel("操作日志")
        log_title.setProperty('class', 'card-title')
        log_layout.addWidget(log_title)
        
        # 使用统一的LogList组件替代简单的列表
        self.log_list = LogList()
        log_layout.addWidget(self.log_list)
        
        self.main_layout.addWidget(log_frame, 2)  # 设置拉伸因子为2
    
    def _load_items_to_combo(self):
        """从配置加载物品列表到下拉框"""
        self.item_combo.clear()
        
        # 添加"所有物品"选项
        self.item_combo.addItem("所有物品")
        
        try:
            # 读取配置文件获取物品列表
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                currencies = config.get('currencies', [])
                currency_aliases = config.get('currency_aliases', {})
                
                # YOLO模型支持的物品清单（如果可用）
                supported_items = []
                try:
                    if hasattr(self.item_recognition_module.yolo_loader, 'supported_items'):
                        supported_items = self.item_recognition_module.yolo_loader.supported_items
                except Exception as e:
                    self._add_log(f"获取YOLO支持物品列表出错: {str(e)}", "WARNING")
                
                # 添加物品到下拉框
                for currency in currencies:
                    # 只添加YOLO支持的物品
                    if not supported_items or currency in supported_items:
                        alias = currency_aliases.get(currency, "")
                        display_text = currency
                        if alias:
                            display_text = f"{currency} ({alias})"
                        
                        # 尝试加载物品图标
                        icon_path = f"assets/orb/{currency.lower()}.png"
                        if os.path.exists(icon_path):
                            self.item_combo.addItem(QIcon(icon_path), display_text)
                        else:
                            self.item_combo.addItem(display_text)
                
            if self.item_combo.count() <= 1:
                self._add_log("未找到可识别的物品", "WARNING")
                
        except Exception as e:
            self._add_log(f"加载物品列表失败: {str(e)}", "ERROR")
    
    def _refresh_items(self):
        """刷新物品列表"""
        self._load_items_to_combo()
        self._add_log("物品列表已刷新")
        self.update_status("✅ 物品列表已刷新")
    
    def _toggle_monitoring(self):
        """切换监测状态"""
        if not self.is_monitoring:
            # 开始监测
            self._start_monitoring()
        else:
            # 停止监测
            self._stop_monitoring()
    
    def _start_monitoring(self):
        """开始物品监测"""
        try:
            # 获取当前选择的物品
            selected_index = self.item_combo.currentIndex()
            selected_text = self.item_combo.currentText()
            
            # 确定物品名称参数
            item_name = None  # 默认不指定物品名称，识别所有物品
            if selected_index > 0:  # 选择了具体物品
                # 提取物品名称，去除可能的别名部分
                item_name = selected_text.split(" (")[0]
                
            # 更新UI状态 - 提前禁用按钮，以免多次点击
            self.monitor_btn.setEnabled(False)
            self.monitor_btn.setText("正在启动...")
            self.update_status("⏳ 正在启动监测...")
                
            # 开启回调监测
            success = self.item_recognition_module.start_monitoring(
                callback=self._recognition_callback,
                item_name=item_name,
                interval=0.5  # 每0.5秒更新一次
            )
            
            if success:
                # 更新UI状态
                self.is_monitoring = True
                self.monitor_btn.setText("⏹ 停止监测")
                self.monitor_btn.setProperty('class', 'danger-button')
                # 重新应用样式
                self.monitor_btn.style().unpolish(self.monitor_btn)
                self.monitor_btn.style().polish(self.monitor_btn)
                self.monitor_btn.setEnabled(True)
                self.single_recognize_btn.setEnabled(False)
                
                # 更新状态显示
                self.update_status("📊 监测中...")
                
                # 添加日志
                self._add_log(f"开始物品监测: {'所有物品' if item_name is None else item_name}")
            else:
                self._add_log("无法启动监测，模型可能未加载完成", "WARNING")
                self.update_status("⚠️ 监测启动失败")
                self.monitor_btn.setText("▶ 开始监测")
                self.monitor_btn.setEnabled(True)
            
        except Exception as e:
            self._add_log(f"开始监测失败: {str(e)}", "ERROR")
            self.update_status("❌ 监测启动失败")
            self.monitor_btn.setText("▶ 开始监测")
            self.monitor_btn.setEnabled(True)
    
    def _stop_monitoring(self):
        """停止物品监测"""
        try:
            # 禁用按钮防止重复点击
            self.monitor_btn.setEnabled(False)
            self.monitor_btn.setText("正在停止...")
            
            # 停止监测
            success = self.item_recognition_module.stop_monitoring()
            
            if success:
                # 更新UI状态
                self.is_monitoring = False
                self.monitor_btn.setText("▶ 开始监测")
                self.monitor_btn.setProperty('class', 'normal-button')  # 使用normal-button样式与其他按钮一致
                # 重新应用样式
                self.monitor_btn.style().unpolish(self.monitor_btn)
                self.monitor_btn.style().polish(self.monitor_btn)
                self.single_recognize_btn.setEnabled(True)
                self.update_status("✅ 监测已停止")
                
                # 添加日志
                self._add_log("物品监测已停止")
            else:
                self._add_log("停止监测失败，可能监测未在运行", "WARNING")
                self.update_status("⚠️ 监测停止失败")
            
            # 恢复按钮状态
            self.monitor_btn.setEnabled(True)
            
        except Exception as e:
            self._add_log(f"停止监测失败: {str(e)}", "ERROR")
            self.update_status("❌ 监测停止失败")
            self.monitor_btn.setEnabled(True)
    
    def _update_result_table(self, item_counts, total_count, confidence_data=None):
        """更新检测结果表格"""
        # 清空表格
        self.result_table.setRowCount(0)
        
        if not item_counts:
            return
        
        # 设置表格行数
        self.result_table.setRowCount(len(item_counts) + 1)  # +1 是为了添加总计行
        
        # 添加物品行
        row = 0
        for name, count in item_counts.items():
            # 物品名称
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.result_table.setItem(row, 0, name_item)
            
            # 数量
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.result_table.setItem(row, 1, count_item)
            
            # 置信度 - 如果有置信度数据则显示
            if confidence_data and name in confidence_data:
                confidence = confidence_data.get(name, 0)
                conf_text = f"{confidence:.2f}" if isinstance(confidence, float) else "-"
                conf_item = QTableWidgetItem(conf_text)
            else:
                conf_item = QTableWidgetItem("-")
            conf_item.setTextAlignment(Qt.AlignCenter)
            self.result_table.setItem(row, 2, conf_item)
            
            row += 1
        
        # 添加总计行
        total_name_item = QTableWidgetItem("总计")
        total_name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = QFont()
        font.setBold(True)
        total_name_item.setFont(font)
        self.result_table.setItem(row, 0, total_name_item)
        
        total_count_item = QTableWidgetItem(str(total_count))
        total_count_item.setTextAlignment(Qt.AlignCenter)
        total_count_item.setFont(font)
        self.result_table.setItem(row, 1, total_count_item)
        
        # 总计行没有置信度
        empty_item = QTableWidgetItem("-")
        empty_item.setTextAlignment(Qt.AlignCenter)
        self.result_table.setItem(row, 2, empty_item)
    
    def _recognition_callback(self, result):
        """物品识别回调函数"""
        if not result or not result.get('success', False):
            return
            
        # 更新预览图像
        if 'preview' in result:
            self._update_preview_image(result['preview'])
            
        # 更新状态
        item_counts = result.get('counts', {})
        total_count = result.get('total', 0)
        
        # 提取物品置信度信息
        confidence_data = {}
        for item in result.get('items', []):
            name = item.get('name')
            conf = item.get('confidence')
            if name:
                if name not in confidence_data:
                    confidence_data[name] = conf
                elif conf > confidence_data[name]:
                    confidence_data[name] = conf
        
        # 更新表格显示
        self._update_result_table(item_counts, total_count, confidence_data)
        
        status_text = f"✅ 识别到 {total_count} 个物品"
        if item_counts:
            item_details = ", ".join([f"{name}: {count}" for name, count in item_counts.items()])
            status_text += f" ({item_details})"
            
        self.update_status(status_text)
    
    def _update_preview_image(self, cv_image):
        """更新预览图像"""
        try:
            # 转换OpenCV图像为QPixmap
            height, width = cv_image.shape[:2]
            
            # 调整图像大小以适应预览区域
            preview_width = 800
            ratio = preview_width / width
            preview_height = int(height * ratio)
            
            # 调整图像大小
            resized_image = cv2.resize(cv_image, (preview_width, preview_height))
            
            # 转换为RGB格式
            rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            
            # 转换为QImage
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # 保存QImage对象，用于弹窗显示
            self.last_image = q_image
            
            # 设置预览图像
            pixmap = QPixmap.fromImage(q_image)
            self.preview_label.setPixmap(pixmap)
            
            # 添加提示文本，提醒用户可以点击放大
            self.preview_label.setToolTip("点击预览图可查看大图")
            
        except Exception as e:
            self._add_log(f"更新预览图像失败: {str(e)}", "ERROR")
    
    def _start_recognition(self):
        """启动物品识别（非阻塞）"""
        try:
            # 获取当前选择的物品
            selected_index = self.item_combo.currentIndex()
            selected_text = self.item_combo.currentText()
            
            # 确定物品名称参数
            item_name = None  # 默认不指定物品名称，识别所有物品
            if selected_index > 0:  # 选择了具体物品
                # 提取物品名称，去除可能的别名部分
                item_name = selected_text.split(" (")[0]
            
            # 更新界面状态
            self._add_log(f"开始识别物品: {'所有物品' if item_name is None else item_name}")
            self.update_status("🔍 识别中...")
            self.single_recognize_btn.setEnabled(False)
            
            # 创建并启动识别线程
            self.recognition_thread = RecognitionThread(
                self.item_recognition_module, 
                item_name
            )
            # 连接信号
            self.recognition_thread.result_signal.connect(self._handle_recognition_result)
            # 连接完成信号
            self.recognition_thread.finished.connect(self._recognition_thread_finished)
            # 启动线程
            self.recognition_thread.start()
            
        except Exception as e:
            self.update_status("❌ 识别过程出错")
            self._add_log(f"识别过程出错: {str(e)}", "ERROR")
            self.single_recognize_btn.setEnabled(True)
    
    def _handle_recognition_result(self, result):
        """处理识别线程的结果"""
        try:
            # 检查结果
            if result and result.get('success', False):
                # 提取物品信息
                items = result.get('items', [])
                item_counts = result.get('counts', {})
                total_count = result.get('total', 0)
                
                # 如果有预览图像，则更新
                if 'preview' in result:
                    self._update_preview_image(result['preview'])
                
                # 提取置信度数据
                confidence_data = {}
                for item in items:
                    name = item.get('name')
                    conf = item.get('confidence')
                    if name:
                        if name not in confidence_data:
                            confidence_data[name] = conf
                        elif conf > confidence_data[name]:
                            confidence_data[name] = conf
                
                # 更新表格显示
                self._update_result_table(item_counts, total_count, confidence_data)
                
                # 更新状态
                status_text = f"✅ 识别到 {total_count} 个物品"
                if item_counts:
                    item_details = ", ".join([f"{name}: {count}" for name, count in item_counts.items()])
                    status_text += f" ({item_details})"
                    
                self.update_status(status_text)
                
                # 添加识别日志
                if items:
                    for name, count in item_counts.items():
                        self._add_log(f"识别到 {count} 个 {name}")
                else:
                    self._add_log("未识别到任何物品")
            else:
                error = result.get('error', '未知错误') if result else '识别失败'
                self.update_status(f"❌ {error}")
                self._add_log(f"识别失败: {error}", "ERROR")
                # 清空表格
                self.result_table.setRowCount(0)
        except Exception as e:
            self.update_status("❌ 处理识别结果时出错")
            self._add_log(f"处理识别结果时出错: {str(e)}", "ERROR")
    
    def _recognition_thread_finished(self):
        """识别线程完成时调用"""
        # 重新启用识别按钮
        self.single_recognize_btn.setEnabled(True)
        # 清理线程对象
        self.recognition_thread = None
    
    def _do_recognition(self):
        """执行物品识别 - 此方法已被弃用，改用非阻塞的_start_recognition方法"""
        self._start_recognition()
    
    def _on_preview_clicked(self, event):
        """处理预览图点击事件"""
        if self.last_image:
            # 创建并显示预览对话框
            dialog = PreviewDialog(self, self.last_image)
            dialog.exec_()
    
    def update_status(self, text):
        """更新状态显示"""
        if hasattr(self, 'status_text'):
            self.status_text.setText(text)
            
            # 根据内容类型设置不同的样式
            if "识别到" in text and "个物品" in text:
                self.status_text.setStyleSheet("font-size: 14px; color: #009900; font-weight: bold;")
            elif "错误" in text or "失败" in text:
                self.status_text.setStyleSheet("font-size: 14px; color: #cc0000; font-weight: bold;")
            elif "监测中" in text or "识别中" in text:
                self.status_text.setStyleSheet("font-size: 14px; color: #0066cc; font-weight: bold;")
            else:
                self.status_text.setStyleSheet("font-size: 14px; color: #666;")
            
        # 同时调用父类方法，更新状态栏
        # 这里我们使用父类的回调方式而不是实际调用父类方法，避免访问不存在的方法
        if hasattr(self, '_add_status') and callable(self._add_status):
            self._add_status(text)
    
    def _add_log(self, message, level="INFO"):
        """向日志列表添加消息"""
        # 添加时间戳
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        
        # 使用LogList组件的添加日志方法
        self.log_list.add_log(message, level, timestamp)
        
        # 同时使用回调函数发送到主日志
        if callable(self._original_add_log):
            self._original_add_log(message, level)
