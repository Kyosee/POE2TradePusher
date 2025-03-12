from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QComboBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QIcon
import cv2
import numpy as np
import os
import json

from .recognition_base_page import RecognitionBasePage
from core.process_modules.item_recognition import ItemRecognitionModule

class ItemRecognitionPage(RecognitionBasePage):
    """物品识别测试页面 - 识别游戏窗口中的物品"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        super().__init__(master, callback_log, callback_status, main_window)
        
        # 创建物品识别模块实例
        self.item_recognition_module = ItemRecognitionModule()
        
        # 监测状态
        self.is_monitoring = False
        
        # 替换搜索框，改为物品下拉选择
        self._replace_search_frame()
        
    def _replace_search_frame(self):
        """替换默认的搜索框为物品选择下拉框"""
        search_frame = self.findChild(QFrame)
        if search_frame:
            # 清除原有布局中的所有部件
            if search_frame.layout():
                while search_frame.layout().count():
                    item = search_frame.layout().takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
            
            # 创建新的布局
            layout = QHBoxLayout(search_frame)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # 添加物品选择下拉框
            item_label = QLabel("物品选择:")
            self.item_combo = QComboBox()
            self.item_combo.setIconSize(QPixmap(24, 24).size())  # 设置图标大小
            self.item_combo.setMinimumWidth(200)  # 设置最小宽度
            self._load_items_to_combo()
            
            layout.addWidget(item_label)
            layout.addWidget(self.item_combo, 1)  # 设置拉伸因子为1，使其占据更多空间
            
            # 添加监测控制按钮
            self.monitor_btn = QPushButton("▶ 开始监测")
            self.monitor_btn.clicked.connect(self._toggle_monitoring)
            self.monitor_btn.setProperty('class', 'primary-button')
            layout.addWidget(self.monitor_btn)
            
            # 单次识别按钮
            self.single_recognize_btn = QPushButton("🔍 识别")
            self.single_recognize_btn.clicked.connect(self._do_recognition)
            self.single_recognize_btn.setProperty('class', 'normal-button')
            layout.addWidget(self.single_recognize_btn)
            
            # 刷新物品列表按钮
            refresh_btn = QPushButton("🔄 刷新")
            refresh_btn.clicked.connect(self._refresh_items)
            refresh_btn.setProperty('class', 'normal-button')
            layout.addWidget(refresh_btn)
    
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
                self.single_recognize_btn.setEnabled(False)
                self.update_status("📊 监测中...")
                
                # 添加日志
                self._add_log(f"开始物品监测: {'所有物品' if item_name is None else item_name}")
            else:
                self._add_log("无法启动监测，模型可能未加载完成", "WARNING")
                self.update_status("⚠️ 监测启动失败")
            
        except Exception as e:
            self._add_log(f"开始监测失败: {str(e)}", "ERROR")
            self.update_status("❌ 监测启动失败")
    
    def _stop_monitoring(self):
        """停止物品监测"""
        try:
            # 停止监测
            success = self.item_recognition_module.stop_monitoring()
            
            if success:
                # 更新UI状态
                self.is_monitoring = False
                self.monitor_btn.setText("▶ 开始监测")
                self.monitor_btn.setProperty('class', 'primary-button')
                self.single_recognize_btn.setEnabled(True)
                self.update_status("✅ 监测已停止")
                
                # 添加日志
                self._add_log("物品监测已停止")
            else:
                self._add_log("停止监测失败，可能监测未在运行", "WARNING")
                self.update_status("⚠️ 监测停止失败")
            
        except Exception as e:
            self._add_log(f"停止监测失败: {str(e)}", "ERROR")
            self.update_status("❌ 监测停止失败")
    
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
            
            # 设置预览图像
            pixmap = QPixmap.fromImage(q_image)
            self.preview_label.setPixmap(pixmap)
            
        except Exception as e:
            self._add_log(f"更新预览图像失败: {str(e)}", "ERROR")
    
    def _do_recognition(self):
        """执行物品识别"""
        try:
            # 获取当前选择的物品
            selected_index = self.item_combo.currentIndex()
            selected_text = self.item_combo.currentText()
            
            # 确定物品名称参数
            item_name = None  # 默认不指定物品名称，识别所有物品
            if selected_index > 0:  # 选择了具体物品
                # 提取物品名称，去除可能的别名部分
                item_name = selected_text.split(" (")[0]
            
            self._add_log(f"开始识别物品: {'所有物品' if item_name is None else item_name}")
            self.update_status("🔍 识别中...")
            
            # 执行识别
            result = self.item_recognition_module.run(
                item_name=item_name,
                generate_preview=True,
                preview_callback=self._update_preview_image
            )
            
            # 检查结果
            if result and result.get('success', False):
                # 提取物品信息
                items = result.get('items', [])
                item_counts = result.get('counts', {})
                total_count = result.get('total', 0)
                
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
                
        except Exception as e:
            self.update_status("❌ 识别过程出错")
            self._add_log(f"识别过程出错: {str(e)}", "ERROR")
