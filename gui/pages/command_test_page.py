from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QLineEdit, QFrame, QTableWidget, QTableWidgetItem,
                              QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import time
from core.process_modules.game_command import GameCommandModule
from ..styles import Styles

class CommandTestPage(QWidget):
    def __init__(self, parent, log_callback=None):
        super().__init__(parent)
        self.log_callback = log_callback if log_callback else lambda x, y: None
        self.styles = Styles()
        
        # 设置GameCommandModule的日志回调
        self.game_command = GameCommandModule()
        def log_info(msg): self.log_callback(msg, "INFO")
        def log_error(msg): self.log_callback(msg, "ERROR")
        self.game_command.logger.info = log_info
        self.game_command.logger.error = log_error
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        self.init_ui()

    def init_ui(self):
        # 创建命令输入区域
        input_frame = QFrame()
        input_frame.setProperty('class', 'card-frame')
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("命令测试")
        title_label.setProperty('class', 'card-title')
        self.main_layout.addWidget(title_label)
        
        # 命令输入框和按钮
        command_label = QLabel("命令:")
        self.command_input = QLineEdit()
        self.command_input.returnPressed.connect(self.on_test_clicked)
        
        self.test_button = QPushButton("测试")
        self.test_button.clicked.connect(self.on_test_clicked)
        self.test_button.setProperty('class', 'normal-button')
        self.test_button.setFixedWidth(80)
        
        input_layout.addWidget(command_label)
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.test_button)
        
        self.main_layout.addWidget(input_frame)
        
        # 创建日志显示区域
        log_frame = QFrame()
        log_frame.setProperty('class', 'card-frame')
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        log_title = QLabel("执行日志")
        log_title.setProperty('class', 'card-title')
        self.main_layout.addWidget(log_title)
        
        # 创建日志表格
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["级别", "时间", "消息"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.setAlternatingRowColors(True)
        
        # 设置日志表格样式
        self.log_table.setStyleSheet(self.styles.log_table_style)
        
        # 添加日志表格到布局
        log_layout.addWidget(self.log_table)
        self.main_layout.addWidget(log_frame)
        
    def add_local_log(self, message, level="INFO"):
        """添加日志到本地表格并发送到全局日志"""
        self.log_callback(message, level)
        
        # 更新本地表格显示
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        
        # 级别列
        level_item = QTableWidgetItem(level)
        level_item.setTextAlignment(Qt.AlignCenter)
        level_item.setForeground(QColor(self.styles.log_colors.get(level, "#000000")))
        self.log_table.setItem(row, 0, level_item)
        
        # 时间列
        time_item = QTableWidgetItem(time.strftime("%Y-%m-%d %H:%M:%S"))
        self.log_table.setItem(row, 1, time_item)
        
        # 消息列
        message_item = QTableWidgetItem(message)
        message_item.setForeground(QColor(self.styles.log_colors.get(level, "#000000")))
        self.log_table.setItem(row, 2, message_item)
        
        # 滚动到底部
        self.log_table.scrollToBottom()
    
    def on_test_clicked(self):
        """测试按钮点击事件处理"""
        command = self.command_input.text().strip()
        if command:
            self.add_local_log(f"执行命令: {command}")
            result = self.game_command.run(command_text=command)
            if result:
                self.add_local_log("命令执行成功", "SUCCESS")
            else:
                self.add_local_log("命令执行失败", "ERROR")
