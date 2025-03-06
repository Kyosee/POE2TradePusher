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
    """多字段输入对话框"""
    def __init__(self, parent, title, prompts, default_texts=None, callback=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.callback = callback
        self.input_fields = []
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 如果传入单个字符串，转换为列表
        if isinstance(prompts, str):
            prompts = [prompts]
        if isinstance(default_texts, str):
            default_texts = [default_texts]
        
        # 确保default_texts是列表且长度与prompts相同
        if default_texts is None:
            default_texts = [""] * len(prompts)
        elif len(default_texts) != len(prompts):
            default_texts.extend([""] * (len(prompts) - len(default_texts)))
        
        # 添加输入字段
        for prompt, default_text in zip(prompts, default_texts):
            # 添加提示文本
            layout.addWidget(QLabel(prompt))
            
            # 添加输入框
            input_field = QLineEdit()
            input_field.setText(default_text)
            if len(self.input_fields) == 0:  # 只选择第一个输入框的内容
                input_field.selectAll()
            layout.addWidget(input_field)
            self.input_fields.append(input_field)
        
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
        for input_field in self.input_fields:
            input_field.returnPressed.connect(self.accept_input)
    
    def accept_input(self):
        """接受输入内容并回调"""
        if self.callback:
            values = [field.text() for field in self.input_fields]
            # 如果只有一个输入字段，返回单个值而不是列表
            self.callback(values[0] if len(values) == 1 else values)
        self.accept()
