
# 临时预览脚本 - 自动生成
import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入页面
from gui.pages.push_manage_page import PushManagePage
from gui.styles import Styles

class PreviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI预览 - PushManagePage")
        self.resize(800, 600)
        
        # 创建中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建标签
        self.title_label = QLabel("预览模式 - PushManagePage")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        self.main_layout.addWidget(self.title_label)
        
        # 创建页面实例
        self.page = PushManagePage(self, self.log_message, self.update_status)
        self.main_layout.addWidget(self.page)
    
    def log_message(self, message, level="INFO"):
        print(f"[{level}] {message}")
    
    def update_status(self, message):
        self.statusBar().showMessage(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 应用样式
    styles = Styles()
    styles.setup(app)
    
    window = PreviewWindow()
    window.show()
    
    sys.exit(app.exec())
