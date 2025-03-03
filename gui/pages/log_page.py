from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                    QTextEdit, QPushButton, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor
import time

class LogPage(QWidget):
    def __init__(self, master, callback_log, callback_status):
        super().__init__(master)
        self.log_message = callback_log
        self.status_bar = callback_status
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        
        self._create_log_area()
        
    def _create_log_area(self):
        """创建日志区域"""
        # 创建日志文本区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(self.font())
        
        # 设置样式
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #E6E7E8;
                border-radius: 2px;
                padding: 8px;
            }
            QTextEdit:focus {
                border: 1px solid #07C160;
            }
        """)
        
        # 创建按钮区域
        button_layout = QVBoxLayout()
        button_layout.setSpacing(5)
        
        # 清空按钮
        self.clear_log_btn = QPushButton("清空")
        self.clear_log_btn.setProperty('class', 'danger-button')
        self.clear_log_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_log_btn)
        
        # 导出按钮
        self.export_log_btn = QPushButton("导出")
        self.export_log_btn.setProperty('class', 'normal-button')
        self.export_log_btn.clicked.connect(self.export_log)
        button_layout.addWidget(self.export_log_btn)
        
        button_layout.addStretch()
        
        # 添加到主布局
        self.main_layout.addWidget(self.log_area)
        self.main_layout.addLayout(button_layout)
        
    def export_log(self):
        """导出日志到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"trade_log_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            "Text files (*.txt);;All files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_area.toPlainText())
                self.status_bar(f"日志已导出: {file_path}")
                self.log_message("日志导出成功")
            except Exception as e:
                self.log_message(f"日志导出失败: {str(e)}", "ERROR")
                
    def clear_log(self):
        """清空日志区域"""
        self.log_area.clear()
        self.status_bar("日志已清空")
        
    def append_log(self, message, level="INFO"):
        """添加日志条目"""
        # 创建格式
        format = QTextCharFormat()
        format.setForeground(QColor(self._get_level_color(level)))
        
        # 创建条目背景格式
        entry_format = QTextCharFormat()
        entry_format.setBackground(QColor('#FBFBFB'))
        
        # 获取光标
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 插入日志条目
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # 应用格式并插入文本
        cursor.insertText(log_entry, format)
        
        # 插入分隔行
        cursor.insertText("\n")
        
        # 滚动到底部
        self.log_area.setTextCursor(cursor)
        self.log_area.ensureCursorVisible()
        
    def _get_level_color(self, level):
        """获取日志级别对应的颜色"""
        colors = {
            "INFO": "#4A4A4A",           # 深灰色-普通消息
            "WARN": "#FF9800",           # 橙色-警告消息
            "ERROR": "#F44336",          # 红色-错误消息
            "ALERT": "#E91E63",          # 亮粉红-警报消息
            "SUCCESS": "#4CAF50",        # 绿色-成功消息
            "DEBUG": "#2196F3",          # 蓝色-调试消息
            "TRADE": "#9C27B0",          # 紫色-交易消息
            "PRICE": "#673AB7",          # 深紫色-价格相关
            "SYSTEM": "#607D8B",         # 蓝灰色-系统消息
            "FILE": "#795548"            # 棕色-文件操作
        }
        return colors.get(level, "#333333")
        
    def get_config_data(self):
        """获取页面数据"""
        # 日志页面不需要保存数据
        return {}
        
    def set_config_data(self, data):
        """设置页面数据"""
        # 日志页面不需要恢复数据
        pass
