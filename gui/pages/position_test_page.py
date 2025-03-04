from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QLineEdit, QFrame, QSpinBox, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
import cv2
import numpy as np
from .recognition_base_page import RecognitionBasePage
from core.process_modules.take_out_item import TakeOutItemModule

class PositionTestPage(RecognitionBasePage):
    """定位测试页面 - 仓库类型识别和格子定位"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        super().__init__(master, callback_log, callback_status, main_window)
        # 创建取出模块实例
        self.take_out_module = TakeOutItemModule()
        
        # 设置默认的模板路径
        from pathlib import Path
        template_path = Path("assets/rec/grid.png")
        if template_path.exists():
            self.set_template(str(template_path))
        
    def _update_preview(self, cv_image):
        """更新预览图像"""
        try:
            # 转换OpenCV图像为QPixmap
            height, width = cv_image.shape[:2]
            
            # 计算缩放比例以适应预览区域（宽度800像素）
            target_width = 800
            ratio = target_width / width
            target_height = int(height * ratio)
            
            # 调整图像大小
            cv_image = cv2.resize(cv_image, (target_width, target_height))
            
            # 转换为RGB格式
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            
            # 创建QImage
            qimg = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
            
            # 转换为QPixmap并显示
            pixmap = QPixmap.fromImage(qimg)
            self.preview_label.setPixmap(pixmap)
            
        except Exception as e:
            self._add_log(f"更新预览图像失败: {str(e)}", "ERROR")
        
    def _create_search_frame(self):
        """创建搜索栏"""
        # 创建搜索框架
        search_frame = QFrame()
        search_frame.setProperty('class', 'card-frame')
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建按钮容器
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)

        # 添加识别按钮
        self.recognize_btn = QPushButton("识别并取出")
        self.recognize_btn.clicked.connect(self._do_recognition)
        self.recognize_btn.setProperty('class', 'normal-button')
        btn_layout.addWidget(self.recognize_btn)
        
        # 添加无预览取出按钮
        self.no_preview_btn = QPushButton("无预览取出")
        self.no_preview_btn.setProperty('class', 'normal-button')
        self.no_preview_btn.clicked.connect(self._take_out_no_preview)
        btn_layout.addWidget(self.no_preview_btn)
        
        # 添加按钮容器到搜索布局
        search_layout.addWidget(btn_container)
        search_layout.addStretch()
        
        # 添加搜索框架到主布局
        self.main_layout.addWidget(search_frame)
        
        # 创建输入区域框架
        input_frame = QFrame()
        input_frame.setProperty('class', 'card-frame')
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("定位设置")
        title_label.setProperty('class', 'card-title')
        self.main_layout.addWidget(title_label)
        
        # 创建坐标输入区域
        coord_layout = QHBoxLayout()
        
        # 横向位置
        pos1_layout = QHBoxLayout()
        pos1_layout.addWidget(QLabel("横向位置:"))
        self.position1_spin = QSpinBox()
        self.position1_spin.setRange(1, 24)
        self.position1_spin.setValue(1)
        pos1_layout.addWidget(self.position1_spin)
        coord_layout.addLayout(pos1_layout)
        
        coord_layout.addSpacing(20)
        
        # 纵向位置
        pos2_layout = QHBoxLayout()
        pos2_layout.addWidget(QLabel("纵向位置:"))
        self.position2_spin = QSpinBox()
        self.position2_spin.setRange(1, 24)
        self.position2_spin.setValue(1)
        pos2_layout.addWidget(self.position2_spin)
        coord_layout.addLayout(pos2_layout)
        
        coord_layout.addStretch()
        
        input_layout.addLayout(coord_layout)
        
        # 插入到主布局中，位于命令按钮下方
        self.main_layout.insertWidget(1, input_frame)
        
    def _do_recognition(self):
        """执行识别并取出装备"""
        try:
            # 获取输入的坐标值
            p1_num = self.position1_spin.value()
            p2_num = self.position2_spin.value()
            
            # 执行取出装备模块（启用预览）
            result = self.take_out_module.process(
                p1_num=p1_num,
                p2_num=p2_num,
                preview_callback=self._update_preview
            )
            
            if result is not False:
                self._add_log(f"✅ 已成功取出装备：横向{p1_num}格，纵向{p2_num}格")
                self.update_status("✅ 识别成功")
            else:
                self._add_log("❌ 取出装备失败", "ERROR")
                self.update_status("❌ 识别失败")
                
        except ValueError as e:
            self._add_log("❌ 请输入有效的位置数值", "ERROR")
            self.update_status("❌ 输入错误")
        except Exception as e:
            self._add_log(f"识别过程出错: {str(e)}", "ERROR")
            self.update_status("❌ 识别失败")

    def _take_out_no_preview(self):
        """执行无预览取出装备"""
        try:
            # 获取输入的坐标值
            p1_num = self.position1_spin.value()
            p2_num = self.position2_spin.value()
            
            # 执行取出装备模块（禁用预览）
            result = self.take_out_module.process(
                p1_num=p1_num,
                p2_num=p2_num,
                preview_callback=None
            )
            
            if result is not False:
                self._add_log(f"✅ 已成功取出装备：横向{p1_num}格，纵向{p2_num}格")
                self.update_status("✅ 操作成功")
            else:
                self._add_log("❌ 取出装备失败", "ERROR")
                self.update_status("❌ 操作失败")
                
        except ValueError as e:
            self._add_log("❌ 请输入有效的位置数值", "ERROR")
            self.update_status("❌ 输入错误")
        except Exception as e:
            self._add_log(f"取出过程出错: {str(e)}", "ERROR")
            self.update_status("❌ 操作失败")
