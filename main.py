import os
import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.styles import Styles

def main():
    """主程序入口"""
    # 确保资源目录存在
    if not os.path.exists('assets'):
        os.makedirs('assets')
        
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 创建并应用样式
    styles = Styles()
    styles.setup(app)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 启动应用程序事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
