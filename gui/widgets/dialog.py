from PySide6.QtWidgets import (QDialog, QFrame, QPushButton, QLabel, QTextEdit, 
                                    QLineEdit, QVBoxLayout, QHBoxLayout, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class BaseDialog(QDialog):
    """基础对话框类，用于创建统一风格的对话框"""
    def __init__(self, parent, title, width=300, height=180):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setModal(True)
        
        # 如果父窗口是置顶的，对话框也应该置顶
        if parent and parent.window().windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 创建主框架
        self.main_frame = QFrame()
        self.main_frame.setProperty('class', 'dialog-frame')
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.addWidget(self.main_frame)
        
        # 居中显示
        self.center_window()
        
    def center_window(self):
        """将窗口居中显示"""
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def keyPressEvent(self, event):
        """处理按键事件"""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

class MessageDialog(QDialog):
    """显示消息的对话框"""
    def __init__(self, parent, title, message, width=400, height=300):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(width, height)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 添加消息显示区域
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setText(message)
        layout.addWidget(self.text_area)
        
        # 添加确定按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)

class InputDialog(QDialog):
    """输入对话框"""
    def __init__(self, parent, title, prompt, default_text="", callback=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.callback = callback
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 添加提示文本
        layout.addWidget(QLabel(prompt))
        
        # 添加输入框
        self.input_field = QLineEdit()
        self.input_field.setText(default_text)
        self.input_field.selectAll()
        layout.addWidget(self.input_field)
        
        # 添加按钮区域
        button_layout = QHBoxLayout()
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        # 确定按钮
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept_input)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # 设置默认按钮和回车键触发
        ok_button.setDefault(True)
        self.input_field.returnPressed.connect(self.accept_input)
    
    def accept_input(self):
        """接受输入内容并回调"""
        if self.callback:
            self.callback(self.input_field.text())
        self.accept()
