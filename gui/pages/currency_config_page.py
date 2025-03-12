from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QLineEdit, QFrame, QMenu,
                              QTableWidget, QTableWidgetItem,
                              QHeaderView, QAbstractItemView, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os
import sys
from ..utils import LoggingMixin, ConfigMixin, show_message, ask_yes_no
from ..widgets.dialog import InputDialog
from ..styles import Styles

# 物品数据类，用于存储物品信息
class CurrencyData:
    def __init__(self, currency="", alias="", img_path="", category="通用"):
        self.currency = currency
        self.alias = alias
        self.img_path = img_path
        self.category = category
        
class CurrencyConfigPage(QWidget, LoggingMixin, ConfigMixin):
    def __init__(self, master, callback_log, callback_status, callback_save=None):
        super().__init__(master)
        LoggingMixin.__init__(self, callback_log, callback_status)
        self.init_config()
        self.save_config = callback_save
        self.styles = Styles()
        self.currency_items = []  # 存储通货单位项的引用
        self.selected_currency_item = None
        
        # 分页相关变量
        self.current_page = 1
        self.items_per_page = 15  # 默认每页显示15条
        self.page_options = [15, 20, 50, 100]  # 每页显示选项
        self.filtered_items = []  # 存储搜索过滤后的物品
        self.search_text = ""  # 搜索文本
        
        # 预定义通货类别
        self.currency_categories = ["可堆疊通貨", "預兆", "地圖碎片", "其他"]
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        # 创建标题
        title_label = QLabel("物品配置")
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
        # 搜索区域
        search_layout = QHBoxLayout()
        
        # 搜索框
        search_label = QLabel("搜索:")
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("输入物品名称或别名搜索")
        self.search_entry.textChanged.connect(self._on_search_changed)
        
        # 类别搜索下拉框
        category_label = QLabel("类别:")
        self.search_category_combo = QComboBox()
        self.search_category_combo.addItem("全部")
        self.search_category_combo.addItems(self.currency_categories)
        self.search_category_combo.currentTextChanged.connect(self._on_category_filter_changed)
        
        # 添加到布局
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_entry, 1)  # 搜索框占据更多空间
        search_layout.addWidget(category_label)
        search_layout.addWidget(self.search_category_combo)
        
        parent_layout.addLayout(search_layout)
        
        # 输入框和按钮
        input_layout = QHBoxLayout()
        
        currency_label = QLabel("物品名称:")
        self.currency_entry = QLineEdit()
        
        alias_label = QLabel("物品别名:")
        self.alias_entry = QLineEdit()
        
        category_label = QLabel("物品类别:")
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.currency_categories)
        
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
        input_layout.addWidget(category_label)
        input_layout.addWidget(self.category_combo)
        input_layout.addWidget(self.add_currency_btn)
        input_layout.addWidget(self.clear_currency_btn)
        
        # 设置回车键触发添加
        self.currency_entry.returnPressed.connect(self.add_currency)
        self.alias_entry.returnPressed.connect(self.add_currency)
        
        parent_layout.addLayout(input_layout)
        
        # 创建表格
        self.currency_table = QTableWidget()
        self.currency_table.setColumnCount(4)  # 图片、通货名称、别名、类别
        self.currency_table.setHorizontalHeaderLabels(["图片", "物品名称", "物品别名", "物品类别"])
        self.currency_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止编辑
        self.currency_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择整行
        self.currency_table.setSelectionMode(QAbstractItemView.SingleSelection)  # 单选
        self.currency_table.setAlternatingRowColors(True)  # 设置交替行颜色
        self.currency_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # 图片列固定宽度
        self.currency_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 通货名称列自适应
        self.currency_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # 别名列自适应
        self.currency_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # 类别列自适应
        self.currency_table.setColumnWidth(0, 40)  # 设置图片列宽度
        
        # 应用统一样式
        self.currency_table.setStyleSheet(self.styles.currency_table_style)
        
        # 设置行高
        self.currency_table.verticalHeader().setDefaultSectionSize(34)
        
        # 连接右键菜单事件
        self.currency_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.currency_table.customContextMenuRequested.connect(self._show_context_menu)
        
        # 连接选择和双击事件
        self.currency_table.itemClicked.connect(self._on_table_item_clicked)
        self.currency_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        parent_layout.addWidget(self.currency_table)
        
        # 创建分页信息和控制区域
        page_status_layout = QHBoxLayout()
        self.total_items_label = QLabel("总计: 0 项")
        page_status_layout.addWidget(self.total_items_label)
        page_status_layout.addStretch()
        
        # 创建分页控制区域
        pagination_frame = QFrame()
        pagination_frame.setFrameShape(QFrame.StyledPanel)
        pagination_frame.setStyleSheet(self.styles.log_pagination_frame_style)
        
        pagination_layout = QHBoxLayout(pagination_frame)
        pagination_layout.setContentsMargins(10, 5, 10, 5)
        
        # 页码信息
        self.page_info_label = QLabel("第1页 / 共1页")
        
        # 每页显示条数选择
        page_size_label = QLabel("每页显示:")
        self.page_size_combo = QComboBox()
        for size in self.page_options:
            self.page_size_combo.addItem(str(size))
        self.page_size_combo.setCurrentText(str(self.items_per_page))
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        
        # 页码导航按钮
        self.first_page_btn = QPushButton("首页")
        self.first_page_btn.clicked.connect(self._goto_first_page)
        
        self.prev_page_btn = QPushButton("上一页")
        self.prev_page_btn.clicked.connect(self._prev_page)
        
        self.next_page_btn = QPushButton("下一页")
        self.next_page_btn.clicked.connect(self._next_page)
        
        self.last_page_btn = QPushButton("末页")
        self.last_page_btn.clicked.connect(self._goto_last_page)
        
        # 设置按钮样式
        for btn in [self.first_page_btn, self.prev_page_btn, self.next_page_btn, self.last_page_btn]:
            btn.setProperty('class', 'normal-button')
            btn.setFixedWidth(60)
        
        # 添加到布局
        pagination_layout.addWidget(page_size_label)
        pagination_layout.addWidget(self.page_size_combo)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.first_page_btn)
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addWidget(self.next_page_btn)
        pagination_layout.addWidget(self.last_page_btn)
        
        parent_layout.addWidget(pagination_frame)
        
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
        row = self.currency_table.currentRow()
        if row >= 0:
            self.currency_menu.exec_(self.currency_table.viewport().mapToGlobal(pos))
    
    def _on_search_changed(self, text):
        """处理搜索文本变化"""
        self.search_text = text.strip().lower()
        self.current_page = 1  # 重置到第一页
        self._filter_items()
        self._update_table()
        
    def _on_category_filter_changed(self, category):
        """处理类别过滤变化"""
        self.current_page = 1  # 重置到第一页
        self._filter_items()
        self._update_table()
        
    def _on_page_size_changed(self, text):
        """处理每页显示数量变化"""
        try:
            self.items_per_page = int(text)
            self.current_page = 1  # 重置到第一页
            self._update_table()
        except ValueError:
            pass
            
    def _prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_table()
            
    def _next_page(self):
        """下一页"""
        total_pages = max(1, (len(self.filtered_items) + self.items_per_page - 1) // self.items_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self._update_table()
            
    def _goto_first_page(self):
        """跳转到第一页"""
        if self.current_page != 1:
            self.current_page = 1
            self._update_table()
    
    def _goto_last_page(self):
        """跳转到最后一页"""
        total_pages = max(1, (len(self.filtered_items) + self.items_per_page - 1) // self.items_per_page)
        if self.current_page != total_pages:
            self.current_page = total_pages
            self._update_table()
            
    def _filter_items(self):
        """根据搜索文本和类别过滤物品"""
        # 先获取所有物品
        self.filtered_items = self.currency_items.copy()
        
        # 按类别过滤
        selected_category = self.search_category_combo.currentText()
        if selected_category != "全部":
            self.filtered_items = [item for item in self.filtered_items if item.category == selected_category]
        
        # 按搜索文本过滤
        if self.search_text:
            temp_items = []
            for item in self.filtered_items:
                if (self.search_text in item.currency.lower() or 
                    self.search_text in item.alias.lower()):
                    temp_items.append(item)
            self.filtered_items = temp_items
                
    def _update_table(self):
        """更新表格显示"""
        # 清空表格
        self.currency_table.setRowCount(0)
        
        # 计算分页信息
        total_items = len(self.filtered_items)
        total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        
        # 确保当前页在有效范围内
        self.current_page = min(max(1, self.current_page), total_pages)
        
        # 更新分页信息显示
        self.page_info_label.setText(f"第{self.current_page}页 / 共{total_pages}页 (总计{total_items}条记录)")
        self.total_items_label.setText(f"总计: {total_items} 项")
        
        # 启用/禁用分页按钮
        self.first_page_btn.setEnabled(self.current_page > 1)
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < total_pages)
        self.last_page_btn.setEnabled(self.current_page < total_pages)
        
        # 计算当前页的起始和结束索引
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)
        
        # 添加当前页的物品到表格
        for i in range(start_idx, end_idx):
            item = self.filtered_items[i]
            row = self.currency_table.rowCount()
            self.currency_table.insertRow(row)
            
            # 创建图片单元格
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignCenter)
            if os.path.exists(item.img_path):
                pixmap = QPixmap(item.img_path)
                scaled_pixmap = pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(scaled_pixmap)
            self.currency_table.setCellWidget(row, 0, img_label)
            
            # 创建物品名称、别名和类别单元格
            self.currency_table.setItem(row, 1, QTableWidgetItem(item.currency))
            self.currency_table.setItem(row, 2, QTableWidgetItem(item.alias))
            self.currency_table.setItem(row, 3, QTableWidgetItem(item.category))
                                     
    def add_currency(self):
        """添加物品"""
        currency = self.currency_entry.text().strip()
        alias = self.alias_entry.text().strip()
        category = self.category_combo.currentText()
        
        if not currency:
            self.log_message("无法添加空物品", "WARN")
            return
            
        # 检查是否已存在
        for item in self.currency_items:
            if item.currency == currency:
                self.log_message("物品已存在", "WARN")
                return
        
        # 获取图片路径
        img_path = self._get_resource_path(f"{currency.lower()}.png")
        
        # 添加到物品列表
        self.currency_items.append(CurrencyData(currency=currency, alias=alias, img_path=img_path, category=category))
        
        # 清空输入框
        self.currency_entry.clear()
        self.alias_entry.clear()
        self.currency_entry.setFocus()
        
        # 更新过滤列表和表格
        self._filter_items()
        self._update_table()
        
        # 记录日志
        self.log_message(f"已添加物品: {currency}, 类别: {category}")
        if self.save_config:
            self.save_config()
                
    def _on_table_item_clicked(self, item):
        """处理表格项点击事件"""
        row = item.row()
        self.selected_row = row
        self.currency_table.selectRow(row)
    
    def _on_item_double_clicked(self, item):
        """处理双击事件，打开编辑对话框"""
        self.edit_currency()
            
    def edit_currency(self):
        """编辑选中的物品"""
        row = self.currency_table.currentRow()
        if row < 0:
            return
            
        # 获取当前页的起始索引
        start_idx = (self.current_page - 1) * self.items_per_page
        # 计算实际的物品索引
        item_idx = start_idx + row
        if item_idx >= len(self.filtered_items):
            return
            
        item = self.filtered_items[item_idx]
        current_currency = item.currency
        current_alias = item.alias
        current_category = item.category
        
        def save_edit(new_currency, new_alias, new_category):
            if not new_currency:
                show_message("提示", "物品名称不能为空", "warning")
                return
                
            if new_currency != current_currency:
                # 检查是否已存在
                for i, existing_item in enumerate(self.currency_items):
                    if existing_item.currency == new_currency and existing_item != item:
                        show_message("提示", "物品已存在", "warning")
                        return
            
            # 更新物品数据
            item.currency = new_currency
            item.alias = new_alias
            item.category = new_category
            
            # 更新图片路径
            img_path = self._get_resource_path(f"{new_currency.lower()}.png")
            item.img_path = img_path
            
            # 更新表格显示
            self._filter_items()
            self._update_table()
            
            self.log_message(f"物品已更新: {current_currency} → {new_currency}, 类别: {new_category}")
            if self.save_config:
                self.save_config()
                
        # 使用InputDialog进行编辑
        dialog = InputDialog(self, "编辑物品", 
                           ["物品名称:", "物品别名:", "物品类别:"], 
                           [current_currency, current_alias, current_category], 
                           lambda values: save_edit(values[0], values[1], values[2]),
                           combo_options={2: self.currency_categories})
        dialog.exec_()
            
    def remove_selected_currency(self):
        """删除选中的物品"""
        row = self.currency_table.currentRow()
        if row < 0:
            return
            
        # 获取当前页的起始索引
        start_idx = (self.current_page - 1) * self.items_per_page
        # 计算实际的物品索引
        item_idx = start_idx + row
        if item_idx >= len(self.filtered_items):
            return
            
        item = self.filtered_items[item_idx]
        currency = item.currency
        
        # 从物品列表中移除
        self.currency_items.remove(item)
        
        # 更新过滤列表和表格
        self._filter_items()
        self._update_table()
        
        self.log_message(f"已移除物品: {currency}")
        if self.save_config:
            self.save_config()
            
    def clear_currencies(self):
        """清空物品"""
        if ask_yes_no("确认清空", "确定要清空所有物品吗？\n此操作无法撤销"):
            self.currency_items.clear()
            self.filtered_items.clear()
            self.currency_table.setRowCount(0)
            self.total_items_label.setText("总计: 0 项")
            
            self.log_message("已清空物品列表")
            self.update_status("✨ 已清空物品列表")
            if self.save_config:
                self.save_config()
            
    def copy_currency(self):
        """复制选中的物品到剪贴板"""
        row = self.currency_table.currentRow()
        if row < 0:
            return
            
        # 获取当前页的起始索引
        start_idx = (self.current_page - 1) * self.items_per_page
        # 计算实际的物品索引
        item_idx = start_idx + row
        if item_idx >= len(self.filtered_items):
            return
            
        currency = self.filtered_items[item_idx].currency
        
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(currency)
        self.update_status(f"已复制: {currency}")
            
    def get_config_data(self):
        """获取配置数据"""
        return {
            'currencies': [item.currency for item in self.currency_items],
            'currency_aliases': {item.currency: item.alias for item in self.currency_items if item.alias},
            'currency_categories': {item.currency: item.category for item in self.currency_items}
        }
        
    def set_config_data(self, data):
        """设置配置数据"""
        # 清空表格和物品列表
        self.currency_table.setRowCount(0)
        self.currency_items.clear()
        
        # 获取别名和类别数据
        aliases = data.get('currency_aliases', {})
        categories = data.get('currency_categories', {})
        
        # 添加新的通货单位
        for currency in data.get('currencies', []):
            alias = aliases.get(currency, "")
            category = categories.get(currency, "通用")  # 默认类别为"通用"
            img_path = self._get_resource_path(f"{currency.lower()}.png")
            
            # 添加到物品列表
            self.currency_items.append(CurrencyData(currency=currency, alias=alias, img_path=img_path, category=category))
        
        # 更新过滤列表和表格
        self._filter_items()
        self._update_table()
