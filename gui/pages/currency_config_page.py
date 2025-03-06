from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QPushButton, QLineEdit, QFrame, QMenu,
                                    QScrollArea, QGridLayout, QTableWidget, QTableWidgetItem,
                                    QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import os
import sys
from ..utils import LoggingMixin, ConfigMixin, show_message, ask_yes_no
from ..widgets.dialog import InputDialog

# 通货单位数据类，用于存储通货信息
class CurrencyData:
    def __init__(self, currency="", alias="", img_path=""):
        self.currency = currency
        self.alias = alias
        self.img_path = img_path
        
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
        
        currency_label = QLabel("通货名称:")
        self.currency_entry = QLineEdit()
        
        alias_label = QLabel("通货别名:")
        self.alias_entry = QLineEdit()
        
        self.add_currency_btn = QPushButton("➕ 添加")
        self.add_currency_btn.clicked.connect(self.add_currency)
        self.add_currency_btn.setProperty('class', 'normal-button')
        
        self.clear_currency_btn = QPushButton("🔄 清空")
        self.clear_currency_btn.clicked.connect(self.clear_currencies)
        self.clear_currency_btn.setProperty('class', 'danger-button')
        
        input_layout.addWidget(currency_label)
        input_layout.addWidget(self.currency_entry)
        input_layout.addWidget(alias_label)
        input_layout.addWidget(self.alias_entry)
        input_layout.addWidget(self.add_currency_btn)
        input_layout.addWidget(self.clear_currency_btn)
        
        # 设置回车键触发添加
        self.currency_entry.returnPressed.connect(self.add_currency)
        self.alias_entry.returnPressed.connect(self.add_currency)
        
        parent_layout.addLayout(input_layout)
        
        # 创建表格
        self.currency_table = QTableWidget()
        self.currency_table.setColumnCount(3)  # 图片、通货名称、别名
        self.currency_table.setHorizontalHeaderLabels(["图片", "通货名称", "通货别名"])
        self.currency_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止编辑
        self.currency_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择整行
        self.currency_table.setSelectionMode(QAbstractItemView.SingleSelection)  # 单选
        self.currency_table.setShowGrid(False)  # 不显示网格线
        self.currency_table.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.currency_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # 图片列固定宽度
        self.currency_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 通货名称列自适应
        self.currency_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # 别名列自适应
        self.currency_table.setColumnWidth(0, 40)  # 设置图片列宽度
        self.currency_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background: white;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e0f0ff;
                color: black;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 4px;
                border: none;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        # 设置行高
        self.currency_table.verticalHeader().setDefaultSectionSize(34)
        
        # 连接右键菜单事件
        self.currency_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.currency_table.customContextMenuRequested.connect(self._show_context_menu)
        
        # 连接选择事件
        self.currency_table.itemClicked.connect(self._on_table_item_clicked)
        
        parent_layout.addWidget(self.currency_table)
        
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
        
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        # 获取当前选中的行
        row = self.currency_table.currentRow()
        if row >= 0:
            self.currency_menu.exec_(self.currency_table.viewport().mapToGlobal(pos))
                                     
    def add_currency(self):
        """添加通货单位"""
        currency = self.currency_entry.text().strip()
        alias = self.alias_entry.text().strip()
        
        if not currency:
            self.log_message("无法添加空通货单位", "WARN")
            return
            
        # 检查是否已存在
        for i in range(self.currency_table.rowCount()):
            if self.currency_table.item(i, 1).text() == currency:
                self.log_message("通货单位已存在", "WARN")
                return
        
        # 获取图片路径
        img_path = self._get_resource_path(f"{currency.lower()}.png")
        
        # 添加到表格
        row = self.currency_table.rowCount()
        self.currency_table.insertRow(row)
        
        # 创建图片单元格
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            scaled_pixmap = pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(scaled_pixmap)
        self.currency_table.setCellWidget(row, 0, img_label)
        
        # 创建通货名称和别名单元格
        self.currency_table.setItem(row, 1, QTableWidgetItem(currency))
        self.currency_table.setItem(row, 2, QTableWidgetItem(alias))
        
        # 添加到通货项列表
        self.currency_items.append(CurrencyData(currency=currency, alias=alias, img_path=img_path))
        
        # 清空输入框
        self.currency_entry.clear()
        self.alias_entry.clear()
        self.currency_entry.setFocus()
        
        # 记录日志
        self.log_message(f"已添加通货单位: {currency}")
        if self.save_config:
            self.save_config()
                
    def _on_table_item_clicked(self, item):
        """处理表格项点击事件"""
        # 获取当前选中的行
        row = item.row()
        self.selected_row = row
            
    def edit_currency(self):
        """编辑选中的通货单位"""
        row = self.currency_table.currentRow()
        if row < 0:
            return
            
        current_currency = self.currency_table.item(row, 1).text()
        current_alias = self.currency_table.item(row, 2).text()
        
        def save_edit(new_currency, new_alias):
            if not new_currency:
                show_message("提示", "通货名称不能为空", "warning")
                return
                
            if new_currency != current_currency:
                # 检查是否已存在
                for i in range(self.currency_table.rowCount()):
                    if i != row and self.currency_table.item(i, 1).text() == new_currency:
                        show_message("提示", "通货单位已存在", "warning")
                        return
            
            # 更新表格中的数据
            self.currency_table.item(row, 1).setText(new_currency)
            self.currency_table.item(row, 2).setText(new_alias)
            
            # 更新通货项列表
            self.currency_items[row].currency = new_currency
            self.currency_items[row].alias = new_alias
            
            # 更新图片
            img_path = self._get_resource_path(f"{new_currency.lower()}.png")
            self.currency_items[row].img_path = img_path
            
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                scaled_pixmap = pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(scaled_pixmap)
            self.currency_table.setCellWidget(row, 0, img_label)
            
            self.log_message(f"通货单位已更新: {current_currency} → {new_currency}")
            if self.save_config:
                self.save_config()
                
        # 使用InputDialog进行编辑
        dialog = InputDialog(self, "编辑通货单位", 
                           ["通货名称:", "通货别名:"], 
                           [current_currency, current_alias], 
                           lambda values: save_edit(values[0], values[1]))
        dialog.exec_()
            
    def remove_selected_currency(self):
        """删除选中的通货单位"""
        row = self.currency_table.currentRow()
        if row < 0:
            return
            
        currency = self.currency_table.item(row, 1).text()
        
        # 从表格和数据列表中移除
        self.currency_table.removeRow(row)
        self.currency_items.pop(row)
        
        self.log_message(f"已移除通货单位: {currency}")
        if self.save_config:
            self.save_config()
            
    def clear_currencies(self):
        """清空通货单位"""
        if ask_yes_no("确认清空", "确定要清空所有通货单位吗？\n此操作无法撤销"):
            self.currency_table.setRowCount(0)
            self.currency_items.clear()
            
            self.log_message("已清空通货单位列表")
            self.update_status("✨ 已清空通货单位列表")
            if self.save_config:
                self.save_config()
            
    def copy_currency(self):
        """复制选中的通货单位到剪贴板"""
        row = self.currency_table.currentRow()
        if row < 0:
            return
            
        currency = self.currency_table.item(row, 1).text()
        
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(currency)
        self.update_status(f"已复制: {currency}")
            
    def get_config_data(self):
        """获取配置数据"""
        return {
            'currencies': [item.currency for item in self.currency_items],
            'currency_aliases': {item.currency: item.alias for item in self.currency_items if item.alias}
        }
        
    def set_config_data(self, data):
        """设置配置数据"""
        # 清空表格
        self.currency_table.setRowCount(0)
        self.currency_items.clear()
        
        # 获取别名数据
        aliases = data.get('currency_aliases', {})
        
        # 添加新的通货单位
        for currency in data.get('currencies', []):
            alias = aliases.get(currency, "")
            img_path = self._get_resource_path(f"{currency.lower()}.png")
            
            # 添加到表格
            row = self.currency_table.rowCount()
            self.currency_table.insertRow(row)
            
            # 创建图片单元格
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                scaled_pixmap = pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(scaled_pixmap)
            self.currency_table.setCellWidget(row, 0, img_label)
            
            # 创建通货名称和别名单元格
            self.currency_table.setItem(row, 1, QTableWidgetItem(currency))
            self.currency_table.setItem(row, 2, QTableWidgetItem(alias))
            
            # 添加到通货项列表
            self.currency_items.append(CurrencyData(currency=currency, alias=alias, img_path=img_path))
