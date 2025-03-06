from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QPushButton, QFrame, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from gui.styles import Styles
import os
import sys

class CurrencyStatsItem(QFrame):
    """通货统计项组件"""
    def __init__(self, parent=None, currency="", count=0, img_path=""):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setProperty('class', 'currency-frame')
        
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 1, 6, 1)
        layout.setSpacing(2)
        
        # 创建图片标签
        self.img_label = QLabel()
        self.img_label.setFixedSize(30, 30)
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            scaled_pixmap = pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(scaled_pixmap)
        
        # 创建文本标签
        self.text_label = QLabel(currency)
        self.text_label.setStyleSheet("font-family: 微软雅黑; font-size: 10pt;")
        
        # 创建计数标签
        self.count_label = QLabel(f"{count:.1f}")
        self.count_label.setStyleSheet("font-family: 微软雅黑; font-size: 10pt; font-weight: bold;")
        
        # 布局
        layout.addWidget(self.img_label)
        layout.addWidget(self.text_label, 1)  # 1表示会自动扩展
        layout.addWidget(self.count_label)

class StatsPage(QWidget):
    def __init__(self, master, callback_log, callback_status, callback_save=None):
        super().__init__(master)
        self.log_message = callback_log
        self.status_bar = callback_status
        self.save_config = callback_save
        
        self.currency_stats = {}  # 存储通货统计数据
        self.trade_message_count = 0  # 交易消息计数
        self.configured_currencies = []  # 已配置的通货单位
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        # 创建统计区域
        self._create_stats_frame()
        
        # 统计重置按钮
        self.clear_btn = QPushButton("统计重置")
        self.clear_btn.setProperty('class', 'danger-button')
        self.clear_btn.clicked.connect(self.clear_stats)
        self.clear_btn.setFixedWidth(100)
        
        # 创建按钮容器并右对齐
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)
        
        self.main_layout.addWidget(btn_container)
        
        # 初始化显示
        self.refresh_stats_display()
        
    def _create_stats_frame(self):
        """创建统计区域"""
        # 交易消息数统计
        message_frame = QFrame()
        message_frame.setProperty('class', 'card-frame')
        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("交易消息数")
        title_label.setProperty('class', 'card-title')
        
        self.message_count_label = QLabel("0")
        self.message_count_label.setStyleSheet("font-family: 微软雅黑; font-size: 12pt; font-weight: bold;")
        self.message_count_label.setAlignment(Qt.AlignCenter)
        
        message_layout.addWidget(title_label)
        message_layout.addWidget(self.message_count_label)
        
        self.main_layout.addWidget(message_frame)
        
        # 交易消息通货统计
        currency_frame = QFrame()
        currency_frame.setProperty('class', 'card-frame')
        currency_layout = QVBoxLayout(currency_frame)
        currency_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("交易消息通货统计")
        title_label.setProperty('class', 'card-title')
        currency_layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(Styles().scroll_area_style)
        
        # 创建容器widget
        self.currency_container = QWidget()
        self.currency_container.setStyleSheet("background: white;")
        self.currency_layout = QVBoxLayout(self.currency_container)
        self.currency_layout.setContentsMargins(0, 0, 0, 0)
        self.currency_layout.setSpacing(1)
        self.currency_layout.addStretch()
        
        scroll_area.setWidget(self.currency_container)
        currency_layout.addWidget(scroll_area)
        
        self.main_layout.addWidget(currency_frame)
        
    def _get_resource_path(self, filename):
        """获取资源文件路径"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, "assets", "orb", filename)
            
    def update_currency_stats(self, currency, amount):
        """更新通货统计"""
        if currency in self.currency_stats:
            self.currency_stats[currency] += float(amount)
        else:
            self.currency_stats[currency] = float(amount)
        self.refresh_stats_display()
        
    def increment_message_count(self):
        """增加交易消息计数"""
        self.trade_message_count += 1
        self.message_count_label.setText(str(self.trade_message_count))
        
    def clear_stats(self):
        """清除所有统计数据"""
        self.currency_stats.clear()
        self.trade_message_count = 0
        self.message_count_label.setText("0")
        
        # 刷新显示（会显示所有已配置的通货单位，计数为0）
        self.refresh_stats_display()
        
        self.log_message("已清除统计数据")
        if callable(self.status_bar):
            self.status_bar("✨ 已清除统计数据")
        
        # 保存配置
        if self.save_config:
            self.save_config()

    def refresh_stats_display(self):
        """刷新统计显示"""
        # 清除现有显示（除了stretch）
        while self.currency_layout.count() > 1:
            item = self.currency_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        # 获取最新的配置通货单位和统计数据
        if hasattr(self.parent(), 'get_currency_config'):
            self.configured_currencies = self.parent().get_currency_config()
        
        # 获取所有需要显示的通货
        currencies = set(self.currency_stats.keys())
        currencies.update(self.configured_currencies)
        
        # 重新创建显示项
        for currency in sorted(currencies):
            img_path = self._get_resource_path(f"{currency.lower()}.png")
            count = self.currency_stats.get(currency, 0)
            item = CurrencyStatsItem(currency=currency, count=count, img_path=img_path)
            self.currency_layout.insertWidget(self.currency_layout.count() - 1, item)
            
    def get_config_data(self):
        """获取页面数据"""
        return {
            'currency_stats': self.currency_stats,
            'trade_message_count': self.trade_message_count
        }
        
    def set_config_data(self, data):
        """设置页面数据"""
        self.currency_stats = data.get('currency_stats', {})
        self.trade_message_count = data.get('trade_message_count', 0)
        
        # 重新获取已配置的通货单位
        if hasattr(self.parent(), 'get_currency_config'):
            self.configured_currencies = self.parent().get_currency_config()
            
        # 更新显示
        self.message_count_label.setText(str(self.trade_message_count))
        self.refresh_stats_display()
