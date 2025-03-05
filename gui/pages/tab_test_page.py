from PySide6.QtWidgets import QLineEdit, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from .recognition_base_page import RecognitionBasePage
from core.process_modules.tab_select import TabSelectModule

class TabTestPage(RecognitionBasePage):
    """Tab测试页面 - 识别Tab标签并执行点击操作"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        super().__init__(master, callback_log, callback_status, main_window)
        self.tab_select_module = TabSelectModule()
        
        # 修改搜索框为Tab文本输入
        self._create_tab_input_frame()
        
    def _create_tab_input_frame(self):
        """创建Tab文本输入框"""
        # 创建一个新的框架替代原来的搜索框架
        # 先找到原来的搜索框架并从布局中移除
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QFrame) and item.widget().property('class') == 'card-frame':
                # 找到第一个card-frame，这应该是搜索框架
                search_frame = item.widget()
                self.main_layout.removeWidget(search_frame)
                search_frame.deleteLater()
                break
        
        # 创建新的框架
        search_frame = QFrame()
        search_frame.setProperty('class', 'card-frame')
        layout = QHBoxLayout(search_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加标签和输入框
        label = QLabel("Tab文本:")
        label.setProperty('class', 'form-label')
        layout.addWidget(label)
        
        self.tab_text_input = QLineEdit()
        self.tab_text_input.setPlaceholderText("输入要识别的Tab标签文本")
        self.tab_text_input.setProperty('class', 'form-input')
        layout.addWidget(self.tab_text_input)
        
        # 按钮容器
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)
        
        # 识别按钮
        self.recognize_btn.setText("🔍 识别Tab")
        btn_layout.addWidget(self.recognize_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._refresh_preview)
        refresh_btn.setProperty('class', 'normal-button')
        btn_layout.addWidget(refresh_btn)
        
        layout.addWidget(btn_container)
        layout.addStretch()
        
        # 将新框架添加到布局中，放在原来搜索框架的位置
        self.main_layout.insertWidget(0, search_frame)
        
        # 添加标题
        title_label = QLabel("识别设置")
        title_label.setProperty('class', 'card-title')
        self.main_layout.insertWidget(0, title_label)
        
    def _do_recognition(self):
        """执行Tab识别和点击"""
        try:
            # 获取输入的Tab文本
            tab_text = self.tab_text_input.text().strip()
            if not tab_text:
                self._add_log("❌ 请输入要识别的Tab文本", "ERROR")
                self.update_status("❌ 请输入Tab文本")
                return
                
            # 执行Tab选择模块
            result, preview_image = self.tab_select_module.run(tab_text=tab_text, show_preview=True)
            
            # 更新预览图
            if preview_image:
                # 将PIL图像转换为QPixmap
                preview_image = preview_image.convert("RGB")
                img_data = preview_image.tobytes("raw", "RGB")
                qimage = QImage(img_data, preview_image.width, preview_image.height, 
                              3 * preview_image.width, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)
                
                # 设置预览图
                self.preview_label.setPixmap(pixmap)
                self.preview_label.setAlignment(Qt.AlignCenter)
            
            if result:
                self._add_log(f"✅ Tab '{tab_text}' 识别并点击成功")
                self.update_status("✅ 识别成功")
            else:
                self._add_log(f"❌ Tab '{tab_text}' 识别或点击失败", "ERROR")
                self.update_status("❌ 识别失败")
                
        except Exception as e:
            self._add_log(f"识别过程出错: {str(e)}", "ERROR")
            self.update_status("❌ 识别失败")