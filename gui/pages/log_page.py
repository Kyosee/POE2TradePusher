from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                    QTextEdit, QPushButton, QFileDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor
import time

class LogPage(QWidget):
    def __init__(self, master, callback_log, callback_status):
        super().__init__(master)
        self.log_message = callback_log
        self.status_bar = callback_status
        
        # 创建主布局
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        
        # 初始化日志缓冲区和定时器
        self.log_buffer = []
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._flush_log_buffer)
        self.update_timer.setInterval(100)  # 100ms刷新一次
        self.update_timer.start()
        
        self._create_log_area()
        
    def _create_log_area(self):
        """创建日志区域"""
        # 创建日志文本区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(self.font())
        self.log_area.document().setMaximumBlockCount(5000)  # 限制最大行数
        
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
        self.log_buffer.clear()
        self.status_bar("日志已清空")
        
    def append_log(self, message, level="INFO"):
        """添加日志条目到缓冲区"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'color': self._get_level_color(level)
        }
        self.log_buffer.append(log_entry)
        
    def _flush_log_buffer(self):
        """将缓冲区的日志刷新到界面"""
        if not self.log_buffer:
            return
            
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 批量处理日志条目
        for entry in self.log_buffer:
            # 设置文本颜色
            format = QTextCharFormat()
            format.setForeground(QColor(entry['color']))
            
            # 构造并插入日志文本
            log_text = f"[{entry['timestamp']}] [{entry['level']}] {entry['message']}\n"
            cursor.insertText(log_text, format)
        
        # 清空缓冲区
        self.log_buffer.clear()
        
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
        return {}
        
    def set_config_data(self, data):
        """设置页面数据"""
        pass
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.update_timer.stop()
        super().closeEvent(event)
