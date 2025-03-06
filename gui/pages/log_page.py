from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                                    QPushButton, QFileDialog, QComboBox, QLabel, QFrame, QHeaderView)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from gui.styles import Styles
import time

class LogPage(QWidget):
    def __init__(self, master, callback_log, callback_status):
        super().__init__(master)
        self.log_message = callback_log
        self.status_bar = callback_status
        self.styles = Styles()
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        # 初始化日志缓冲区
        self.log_buffer = []
        self.all_logs = []  # 存储所有日志条目
        
        # 分页设置
        self.current_page = 1
        self.page_size = 50  # 默认每页显示50条
        self.page_sizes = [20, 50, 100, 200, 500]
        
        # 创建日志表格区域
        self._create_log_table()
        
        # 创建分页控制区域
        self._create_pagination_controls()
        
        # 创建按钮区域
        self._create_button_controls()
        
        # 初始化定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._flush_log_buffer)
        self.update_timer.setInterval(100)  # 100ms刷新一次
        self.update_timer.start()
        
    def _create_log_table(self):
        """创建日志表格区域"""
        # 创建日志表格
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["级别", "时间", "消息"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 设置为不可编辑
        self.log_table.setAlternatingRowColors(True)  # 设置交替行颜色
        
        # 设置样式
        self.log_table.setStyleSheet(self.styles.log_table_style)
        
        # 连接事件
        self.log_table.itemClicked.connect(self._on_row_clicked)
        self.log_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # 添加到主布局
        self.main_layout.addWidget(self.log_table, 1)  # 1表示拉伸因子
        
    def _on_row_clicked(self, item):
        """处理行点击事件"""
        row = item.row()
        self.log_table.selectRow(row)
    
    def _on_item_double_clicked(self, item):
        """处理双击事件，显示完整消息内容"""
        if item.column() == 2:  # 只处理消息列
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
            from PySide6.QtCore import Qt
            
            dialog = QDialog(self)
            dialog.setWindowTitle("完整消息内容")
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(item.text())
            text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(dialog.accept)
            
            layout.addWidget(text_edit)
            layout.addWidget(button_box)
            
            dialog.exec()
    
    def _create_pagination_controls(self):
        """创建分页控制区域"""
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
        for size in self.page_sizes:
            self.page_size_combo.addItem(str(size))
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        
        # 页码导航按钮
        self.first_page_btn = QPushButton("首页")
        self.first_page_btn.clicked.connect(self._goto_first_page)
        
        self.prev_page_btn = QPushButton("上一页")
        self.prev_page_btn.clicked.connect(self._goto_prev_page)
        
        self.next_page_btn = QPushButton("下一页")
        self.next_page_btn.clicked.connect(self._goto_next_page)
        
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
        
        self.main_layout.addWidget(pagination_frame)
        
    def _create_button_controls(self):
        """创建按钮控制区域"""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 5, 0, 0)
        
        # 清空按钮
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.setProperty('class', 'danger-button')
        self.clear_log_btn.clicked.connect(self.clear_log)
        
        # 导出按钮
        self.export_log_btn = QPushButton("导出日志")
        self.export_log_btn.setProperty('class', 'normal-button')
        self.export_log_btn.clicked.connect(self.export_log)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setProperty('class', 'normal-button')
        self.refresh_btn.clicked.connect(self._refresh_table)
        
        button_layout.addWidget(self.clear_log_btn)
        button_layout.addWidget(self.export_log_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)
        
        self.main_layout.addWidget(button_frame)
        
    def _on_page_size_changed(self, text):
        """处理每页显示条数变化"""
        try:
            self.page_size = int(text)
            self.current_page = 1  # 重置到第一页
            self._refresh_table()
            self.status_bar(f"每页显示条数已更改为 {self.page_size}")
        except ValueError:
            pass
    
    def _goto_first_page(self):
        """跳转到第一页"""
        if self.current_page != 1:
            self.current_page = 1
            self._refresh_table()
    
    def _goto_prev_page(self):
        """跳转到上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self._refresh_table()
    
    def _goto_next_page(self):
        """跳转到下一页"""
        total_pages = max(1, (len(self.all_logs) + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self._refresh_table()
    
    def _goto_last_page(self):
        """跳转到最后一页"""
        total_pages = max(1, (len(self.all_logs) + self.page_size - 1) // self.page_size)
        if self.current_page != total_pages:
            self.current_page = total_pages
            self._refresh_table()
    
    def _update_pagination_controls(self):
        """更新分页控制器状态"""
        total_pages = max(1, (len(self.all_logs) + self.page_size - 1) // self.page_size)
        self.page_info_label.setText(f"第{self.current_page}页 / 共{total_pages}页 (总计{len(self.all_logs)}条记录)")
        
        # 更新按钮状态
        self.first_page_btn.setEnabled(self.current_page > 1)
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < total_pages)
        self.last_page_btn.setEnabled(self.current_page < total_pages)
    
    def _refresh_table(self):
        """刷新表格显示"""
        # 计算当前页的数据范围（倒序）
        total_logs = len(self.all_logs)
        end_idx = total_logs - (self.current_page - 1) * self.page_size
        start_idx = max(0, end_idx - self.page_size)
        current_page_logs = list(reversed(self.all_logs[start_idx:end_idx]))
        
        # 更新表格
        self.log_table.setRowCount(len(current_page_logs))
        
        for row, log_entry in enumerate(current_page_logs):
            # 级别列
            level_item = QTableWidgetItem(log_entry['level'])
            level_item.setForeground(QColor(log_entry['color']))
            level_item.setTextAlignment(Qt.AlignCenter)
            self.log_table.setItem(row, 0, level_item)
            
            # 时间列
            time_item = QTableWidgetItem(log_entry['timestamp'])
            self.log_table.setItem(row, 1, time_item)
            
            # 消息列
            message_item = QTableWidgetItem(log_entry['message'])
            message_item.setForeground(QColor(log_entry['color']))
            self.log_table.setItem(row, 2, message_item)
        
        # 更新分页控制器
        self._update_pagination_controls()
        
        # 滚动到底部（最新的日志在顶部，所以滚动到顶部）
        if self.current_page == max(1, (len(self.all_logs) + self.page_size - 1) // self.page_size):
            self.log_table.scrollToTop()
    
    def export_log(self):
        """导出日志到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"trade_log_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            "Text files (*.txt);;All files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for log in self.all_logs:
                        f.write(f"[{log['timestamp']}] [{log['level']}] {log['message']}\n")
                self.status_bar(f"日志已导出: {file_path}")
                self.log_message("日志导出成功")
            except Exception as e:
                self.log_message(f"日志导出失败: {str(e)}", "ERROR")
                
    def clear_log(self):
        """清空日志区域"""
        self.log_table.setRowCount(0)
        self.log_buffer.clear()
        self.all_logs.clear()
        self.current_page = 1
        self._update_pagination_controls()
        self.status_bar("日志已清空")
        
    def append_log(self, message, level="INFO"):
        """添加日志条目到缓冲区"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'color': self.styles.log_colors.get(level, "#000000")
        }
        self.log_buffer.append(log_entry)
        
    def _flush_log_buffer(self):
        """将缓冲区的日志刷新到界面"""
        if not self.log_buffer:
            return
        
        # 添加到全局日志列表
        self.all_logs.extend(self.log_buffer)
        self.log_buffer.clear()
        
        # 刷新表格显示
        self._refresh_table()
