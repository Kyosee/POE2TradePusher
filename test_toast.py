import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QLabel
from gui.widgets.toast import show_toast, Toast
from gui.utils import switch_to_window

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toast测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建测试按钮区域
        button_layout = QHBoxLayout()
        
        info_btn = QPushButton("显示信息Toast")
        info_btn.clicked.connect(self.show_info_toast)
        
        success_btn = QPushButton("显示成功Toast")
        success_btn.clicked.connect(self.show_success_toast)
        
        warning_btn = QPushButton("显示警告Toast")
        warning_btn.clicked.connect(self.show_warning_toast)
        
        error_btn = QPushButton("显示错误Toast")
        error_btn.clicked.connect(self.show_error_toast)
        
        # 添加按钮到布局
        button_layout.addWidget(info_btn)
        button_layout.addWidget(success_btn)
        button_layout.addWidget(warning_btn)
        button_layout.addWidget(error_btn)
        
        layout.addLayout(button_layout)
        
        # 创建模拟切换窗口区域
        switch_layout = QHBoxLayout()
        switch_layout.addWidget(QLabel("窗口名称:"))
        
        self.window_name_entry = QLineEdit("记事本")
        switch_layout.addWidget(self.window_name_entry)
        
        switch_btn = QPushButton("切换窗口")
        switch_btn.clicked.connect(self.switch_window)
        switch_layout.addWidget(switch_btn)
        
        layout.addLayout(switch_layout)
        
        # 添加一些说明
        help_text = QLabel("测试说明:\n1. 输入系统上存在的窗口名称(如'记事本'、'计算器')\n"
                          "2. 点击'切换窗口'按钮\n"
                          "3. 检查Toast是否正确显示在窗口右上角")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        layout.addStretch()
        
    def show_info_toast(self):
        show_toast(self, "信息提示", "这是一条信息提示消息", Toast.INFO)
        
    def show_success_toast(self):
        show_toast(self, "成功提示", "操作已成功完成！\n系统处理完毕", Toast.SUCCESS)
        
    def show_warning_toast(self):
        show_toast(self, "警告提示", "请注意，这是一条警告消息", Toast.WARNING)
        
    def show_error_toast(self):
        show_toast(self, "错误提示", "操作失败，请重试", Toast.ERROR)
        
    def switch_window(self):
        window_name = self.window_name_entry.text().strip()
        # 使用通用的切换窗口函数
        switch_to_window(window_name, self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
