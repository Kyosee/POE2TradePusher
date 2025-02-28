import os
import sys
from tkinter import Tk
from gui.main_window import MainWindow

def main():
    """主程序入口"""
    # 确保资源目录存在
    if not os.path.exists('assets'):
        os.makedirs('assets')
        
    # 创建主窗口
    root = Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
