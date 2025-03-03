import os
import sys
import time
import importlib
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QComboBox, QHBoxLayout
from PySide6.QtCore import Qt, QTimer

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

class UIPreviewWindow(QMainWindow):
    """UI预览窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI实时预览工具")
        self.resize(400, 200)
        
        # 创建中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建控制区域
        self.create_control_panel()
        
        # 创建状态区域
        self.status_label = QLabel("就绪")
        self.main_layout.addWidget(self.status_label)
        
        # 初始化变量
        self.observer = None
        self.preview_process = None
        self.watching = False
        self.current_page = None
        
        # 加载可用页面
        self.load_available_pages()
    
    def create_control_panel(self):
        """创建控制面板"""
        control_layout = QVBoxLayout()
        
        # 页面选择
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("选择页面:"))
        self.page_combo = QComboBox()
        page_layout.addWidget(self.page_combo)
        control_layout.addLayout(page_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 开始监控按钮
        self.start_btn = QPushButton("开始监控")
        self.start_btn.clicked.connect(self.toggle_monitoring)
        button_layout.addWidget(self.start_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新页面列表")
        refresh_btn.clicked.connect(self.load_available_pages)
        button_layout.addWidget(refresh_btn)
        
        control_layout.addLayout(button_layout)
        self.main_layout.addLayout(control_layout)
    
    def load_available_pages(self):
        """加载可用的页面"""
        self.page_combo.clear()
        
        # 查找pages目录下的所有页面
        pages_dir = os.path.join(project_root, "gui", "pages")
        if os.path.exists(pages_dir):
            for file in os.listdir(pages_dir):
                if file.endswith("_page.py") and not file.startswith("__"):
                    page_name = file[:-3]  # 移除.py后缀
                    self.page_combo.addItem(page_name)
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.watching:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """开始监控"""
        if self.page_combo.currentText():
            self.current_page = self.page_combo.currentText()
            self.watching = True
            self.start_btn.setText("停止监控")
            self.status_label.setText(f"正在监控: {self.current_page}")
            
            # 启动文件监控
            self.start_file_monitoring()
            
            # 启动预览窗口
            self.launch_preview_window()
        else:
            self.status_label.setText("错误: 请先选择一个页面")
    
    def stop_monitoring(self):
        """停止监控"""
        self.watching = False
        self.start_btn.setText("开始监控")
        self.status_label.setText("监控已停止")
        
        # 停止文件监控
        if self.observer:
            self.observer.stop()
            self.observer = None
        
        # 关闭预览窗口
        if self.preview_process:
            try:
                self.preview_process.terminate()
                self.preview_process = None
            except Exception as e:
                print(f"关闭预览窗口时出错: {e}")
    
    def start_file_monitoring(self):
        """启动文件监控"""
        # 创建文件系统事件处理器
        event_handler = PageFileHandler(self)
        
        # 创建观察者
        self.observer = Observer()
        
        # 监控pages目录
        pages_dir = os.path.join(project_root, "gui", "pages")
        self.observer.schedule(event_handler, pages_dir, recursive=False)
        
        # 监控widgets目录
        widgets_dir = os.path.join(project_root, "gui", "widgets")
        if os.path.exists(widgets_dir):
            self.observer.schedule(event_handler, widgets_dir, recursive=False)
        
        # 启动观察者
        self.observer.start()
    
    def launch_preview_window(self):
        """启动预览窗口"""
        # 创建预览脚本
        preview_script = self.create_preview_script()
        
        # 启动预览窗口
        try:
            self.preview_process = subprocess.Popen(
                [sys.executable, preview_script],
                cwd=project_root
            )
            self.status_label.setText(f"预览窗口已启动: {self.current_page}")
        except Exception as e:
            self.status_label.setText(f"启动预览窗口失败: {e}")
    
    def create_preview_script(self):
        """创建预览脚本"""
        script_path = os.path.join(project_root, "_temp_preview.py")
        
        # 获取页面模块名
        module_name = self.current_page
        class_name = ''.join(word.capitalize() for word in module_name.split('_'))
        
        # 创建脚本内容
        script_content = f"""
# 临时预览脚本 - 自动生成
import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入页面
from gui.pages.{module_name} import {class_name}
from gui.styles import Styles

class PreviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI预览 - {class_name}")
        self.resize(800, 600)
        
        # 创建中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建标签
        self.title_label = QLabel("预览模式 - {class_name}")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        self.main_layout.addWidget(self.title_label)
        
        # 创建页面实例
        self.page = {class_name}(self, self.log_message, self.update_status)
        self.main_layout.addWidget(self.page)
    
    def log_message(self, message, level="INFO"):
        print(f"[{{level}}] {{message}}")
    
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
"""
        
        # 写入脚本文件
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        return script_path
    
    def file_changed(self, path):
        """文件变更处理"""
        if not self.watching:
            return
            
        # 检查是否是当前监控的页面
        filename = os.path.basename(path)
        if self.current_page + ".py" == filename or filename.endswith(".py"):
            self.status_label.setText(f"检测到文件变更: {filename}，重新启动预览...")
            
            # 关闭当前预览窗口
            if self.preview_process:
                try:
                    self.preview_process.terminate()
                    self.preview_process = None
                except Exception:
                    pass
            
            # 等待一小段时间确保文件写入完成
            QTimer.singleShot(500, self.launch_preview_window)

class PageFileHandler(FileSystemEventHandler):
    """文件变更事件处理器"""
    def __init__(self, window):
        self.window = window
        self.last_modified = {}
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".py"):
            # 防止重复触发
            current_time = time.time()
            if event.src_path in self.last_modified:
                if current_time - self.last_modified[event.src_path] < 1:
                    return
            
            self.last_modified[event.src_path] = current_time
            self.window.file_changed(event.src_path)

def main():
    # 检查依赖
    try:
        import watchdog
    except ImportError:
        print("缺少必要的依赖: watchdog")
        print("请运行: pip install watchdog")
        return
    
    app = QApplication(sys.argv)
    window = UIPreviewWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()