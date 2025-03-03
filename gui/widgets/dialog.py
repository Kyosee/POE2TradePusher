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

class MessageDialog(BaseDialog):
    """消息对话框，用于显示帮助信息等长文本内容"""
    def __init__(self, parent, title, message, width=600, height=400):
        super().__init__(parent, title, width, height)
        
        # 创建布局
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建文本区域
        self.text = QTextEdit()
        self.text.setFont(QFont("微软雅黑", 10))
        self.text.setReadOnly(True)
        self.text.setPlainText(message)
        self.text.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.text)
        
        # 确定按钮
        btn = QPushButton("确定")
        btn.setProperty('class', 'normal-button')
        btn.clicked.connect(self.close)
        btn.setFixedWidth(80)
        
        # 按钮容器
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addWidget(btn)
        btn_layout.setContentsMargins(0, 0, 0, 10)
        layout.addWidget(btn_container, alignment=Qt.AlignCenter)
        
class InputDialog(BaseDialog):
    """输入对话框，用于编辑单个值"""
    def __init__(self, parent, title, prompt, initial_value="", callback=None):
        super().__init__(parent, title)
        
        # 保存回调函数
        self._callback = callback
        
        # 创建布局
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 提示文本
        prompt_label = QLabel(prompt)
        prompt_label.setFont(QFont("微软雅黑", 9))
        layout.addWidget(prompt_label)
        
        # 输入框
        self.entry = QLineEdit()
        self.entry.setFont(QFont("微软雅黑", 9))
        self.entry.setText(initial_value)
        self.entry.setFixedWidth(300)
        layout.addWidget(self.entry)
        
        # 按钮容器
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        
        # 确定按钮
        confirm_btn = QPushButton("✔️ 确定")
        confirm_btn.setProperty('class', 'normal-button')
        confirm_btn.clicked.connect(lambda: self._on_confirm(callback))
        btn_layout.addWidget(confirm_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setProperty('class', 'danger-button')
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)
        
        layout.addWidget(btn_container, alignment=Qt.AlignCenter)
        
        # 设置焦点
        self.entry.setFocus()
        
    def _on_confirm(self, callback):
        """确认按钮点击处理"""
        if callback:
            callback(self.entry.text().strip())
        self.close()
        
    def keyPressEvent(self, event):
        """处理按键事件"""
        if event.key() == Qt.Key_Return:
            self._on_confirm(self._callback)
        else:
            super().keyPressEvent(event)
