from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QPushButton, QLineEdit, QFrame, QMenu,
                                    QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import os
import sys
from ..utils import LoggingMixin, ConfigMixin, show_message, ask_yes_no
from ..widgets.dialog import InputDialog

class CurrencyItem(QFrame):
    """通货单位项组件"""
    def __init__(self, parent=None, currency="", img_path=""):
        super().__init__(parent)
        self.currency = currency
        
        # 设置固定高度
        self.setFixedHeight(34)
        self.setProperty('class', 'currency-frame')
        
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
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
        
        # 布局
        layout.addWidget(self.img_label)
        layout.addWidget(self.text_label, 1)  # 1表示会自动扩展
        
class CurrencyConfigPage(QWidget, LoggingMixin, ConfigMixin):
    def __init__(self, master, callback_log, callback_status, callback_save=None):
        super().__init__(master)
        LoggingMixin.__init__(self, callback_log, callback_status)
        self.init_config()
        self.save_config = callback_save
        self.currency_items = []  # 存储通货单位项的引用
        self.selected_currency_item = None
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        # 创建标题
        title_label = QLabel("通货单位配置")
        title_label.setProperty('class', 'card-title')
        self.main_layout.addWidget(title_label)
        
        # 创建内容框架
        content_frame = QFrame()
        content_frame.setProperty('class', 'card-frame')
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(6)
        
        # 创建通货单位配置区域
        self._create_currency_frame(content_layout)
        self._setup_currency_menu()
        
        self.main_layout.addWidget(content_frame)
        
    def _get_resource_path(self, filename):
        """获取资源文件路径"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, "assets", "orb", filename)
        
    def _create_currency_frame(self, parent_layout):
        """创建通货单位配置区域"""
        # 输入框和按钮
        input_layout = QHBoxLayout()
        
        self.currency_entry = QLineEdit()
        self.currency_entry.returnPressed.connect(self.add_currency)
        
        self.add_currency_btn = QPushButton("➕ 添加")
        self.add_currency_btn.clicked.connect(self.add_currency)
        self.add_currency_btn.setProperty('class', 'normal-button')
        
        self.clear_currency_btn = QPushButton("🔄 清空")
        self.clear_currency_btn.clicked.connect(self.clear_currencies)
        self.clear_currency_btn.setProperty('class', 'danger-button')
        
        input_layout.addWidget(self.currency_entry)
        input_layout.addWidget(self.add_currency_btn)
        input_layout.addWidget(self.clear_currency_btn)
        
        parent_layout.addLayout(input_layout)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #F0F0F0;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CDCDCD;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # 创建容器widget
        self.currency_container = QWidget()
        self.currency_container.setStyleSheet("background: white;")
        self.currency_layout = QVBoxLayout(self.currency_container)
        self.currency_layout.setContentsMargins(0, 0, 0, 0)
        self.currency_layout.setSpacing(0)
        self.currency_layout.addStretch()  # 添加弹性空间
        
        scroll_area.setWidget(self.currency_container)
        parent_layout.addWidget(scroll_area)
        
    def _setup_currency_menu(self):
        """设置通货单位右键菜单"""
        self.currency_menu = QMenu(self)
        
        edit_action = self.currency_menu.addAction("📄 编辑")
        edit_action.triggered.connect(self.edit_currency)
        
        delete_action = self.currency_menu.addAction("❌ 删除")
        delete_action.triggered.connect(self.remove_selected_currency)
        
        self.currency_menu.addSeparator()
        
        copy_action = self.currency_menu.addAction("📋 复制")
        copy_action.triggered.connect(self.copy_currency)
                                     
    def add_currency(self):
        """添加通货单位"""
        currency = self.currency_entry.text().strip()
        if not currency:
            self.log_message("无法添加空通货单位", "WARN")
            return
            
        # 检查是否已存在
        for item in self.currency_items:
            if item.currency == currency:
                self.log_message(f"重复通货单位: {currency}", "WARN")
                return
                
        # 创建新的通货单位项
        img_path = self._get_resource_path(f"{currency.lower()}.png")
        item = CurrencyItem(currency=currency, img_path=img_path)
        
        # 设置点击事件
        item.mousePressEvent = lambda e, item=item: self._on_currency_click(e, item)
        
        # 插入到倒数第二个位置（最后一个是stretch）
        self.currency_layout.insertWidget(len(self.currency_items), item)
        self.currency_items.append(item)
        
        self.currency_entry.clear()
        self.log_message(f"已添加通货单位: {currency}")
        
        # 自动保存配置
        if self.save_config:
            try:
                self.save_config()
                self.update_status(f"✨ 已添加并保存通货单位: {currency}")
            except Exception as e:
                self.log_message(f"保存配置失败: {e}", "ERROR")
                
    def _on_currency_click(self, event, item):
        """处理通货单位项点击事件"""
        # 清除其他项的选中状态
        if self.selected_currency_item:
            self.selected_currency_item.setProperty('selected', False)
            self.selected_currency_item.style().unpolish(self.selected_currency_item)
            self.selected_currency_item.style().polish(self.selected_currency_item)
            
        # 设置当前项的选中状态
        item.setProperty('selected', True)
        item.style().unpolish(item)
        item.style().polish(item)
        self.selected_currency_item = item
        
        # 处理右键点击
        if event.button() == Qt.RightButton:
            self.currency_menu.exec_(event.globalPos())
            
    def edit_currency(self):
        """编辑选中的通货单位"""
        if not self.selected_currency_item:
            return
            
        current_currency = self.selected_currency_item.currency
            
        def save_edit(new_currency):
            if new_currency and new_currency != current_currency:
                # 检查是否已存在
                for item in self.currency_items:
                    if item != self.selected_currency_item and \
                       item.currency == new_currency:
                        show_message("提示", "通货单位已存在", "warning")
                        return
                        
                # 更新通货单位
                index = self.currency_layout.indexOf(self.selected_currency_item)
                self.currency_layout.removeWidget(self.selected_currency_item)
                self.currency_items.remove(self.selected_currency_item)
                self.selected_currency_item.deleteLater()
                
                # 创建新项
                img_path = self._get_resource_path(f"{new_currency.lower()}.png")
                new_item = CurrencyItem(currency=new_currency, img_path=img_path)
                new_item.mousePressEvent = lambda e, item=new_item: self._on_currency_click(e, item)
                
                self.currency_layout.insertWidget(index, new_item)
                self.currency_items.append(new_item)
                self.selected_currency_item = new_item
                
                self.log_message(f"通货单位已更新: {current_currency} → {new_currency}")
                if self.save_config:
                    self.save_config()
                    
        # 使用InputDialog进行编辑
        InputDialog(self, "编辑通货单位", "请输入新的通货单位：", current_currency, save_edit)
            
    def remove_selected_currency(self):
        """删除选中的通货单位"""
        if not self.selected_currency_item:
            return
            
        currency = self.selected_currency_item.currency
        self.currency_layout.removeWidget(self.selected_currency_item)
        self.currency_items.remove(self.selected_currency_item)
        self.selected_currency_item.deleteLater()
        self.selected_currency_item = None
        
        self.log_message(f"已移除通货单位: {currency}")
        if self.save_config:
            self.save_config()
            
    def clear_currencies(self):
        """清空通货单位"""
        if ask_yes_no("确认清空", "确定要清空所有通货单位吗？\n此操作无法撤销"):
            for item in self.currency_items:
                self.currency_layout.removeWidget(item)
                item.deleteLater()
            self.currency_items.clear()
            self.selected_currency_item = None
            
            self.log_message("已清空通货单位列表")
            self.update_status("✨ 已清空通货单位列表")
            if self.save_config:
                self.save_config()
            
    def copy_currency(self):
        """复制选中的通货单位到剪贴板"""
        if not self.selected_currency_item:
            return
            
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.selected_currency_item.currency)
        self.update_status(f"已复制: {self.selected_currency_item.currency}")
            
    def get_config_data(self):
        """获取配置数据"""
        return {
            'currencies': [item.currency for item in self.currency_items]
        }
        
    def set_config_data(self, data):
        """设置配置数据"""
        # 清空现有通货单位
        for item in self.currency_items:
            self.currency_layout.removeWidget(item)
            item.deleteLater()
        self.currency_items.clear()
        self.selected_currency_item = None
        
        # 添加新的通货单位
        for currency in data.get('currencies', []):
            img_path = self._get_resource_path(f"{currency.lower()}.png")
            item = CurrencyItem(currency=currency, img_path=img_path)
            item.mousePressEvent = lambda e, item=item: self._on_currency_click(e, item)
            
            self.currency_layout.insertWidget(len(self.currency_items), item)
            self.currency_items.append(item)
