from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QPushButton, QLineEdit, QTextEdit, QFrame)
from PySide6.QtCore import Qt
from core.process_modules.game_command import GameCommandModule

class CommandTestPage(QWidget):
    def __init__(self, parent, log_callback=None):
        super().__init__(parent)
        self.log_callback = log_callback if log_callback else lambda x, y: None
        self.game_command = GameCommandModule()
        self.game_command.logger.info = lambda x: self.log_callback(x, "INFO")
        self.game_command.logger.error = lambda x: self.log_callback(x, "ERROR")
        
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
        
        # 日志文本框
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #E6E7E8;
                border-radius: 2px;
                padding: 8px;
                font-family: 微软雅黑;
                font-size: 9pt;
            }
        """)
        
        log_layout.addWidget(self.log_display)
        self.main_layout.addWidget(log_frame)
        
    def add_log(self, message):
        """添加日志到显示区域"""
        self.log_display.append(message)
        # 滚动到底部
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )
    
    def on_test_clicked(self):
        """测试按钮点击事件处理"""
        command = self.command_input.text().strip()
        if command:
            self.add_log(f"执行命令: {command}")
            result = self.game_command.run(command_text=command)
            if result:
                self.add_log("命令执行成功")
            else:
                self.add_log("命令执行失败")
