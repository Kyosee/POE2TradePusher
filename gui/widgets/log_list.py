from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush

class LogList(QListWidget):
    """统一的日志列表组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置列表属性
        self.setAlternatingRowColors(True)
        self.setWordWrap(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)  # 允许多选
        
        # 日志级别对应的颜色
        self.level_colors = {
            "INFO": QColor(0, 0, 0),       # 黑色
            "SUCCESS": QColor(0, 128, 0),  # 绿色
            "WARNING": QColor(205, 133, 0), # 橙色
            "ERROR": QColor(255, 0, 0),    # 红色
            "SYSTEM": QColor(0, 0, 139),   # 深蓝色
            "DEBUG": QColor(128, 128, 128), # 灰色
        }
        
        # 列表样式
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                font-family: 'Microsoft YaHei', Arial;
                font-size: 13px;
                padding: 2px;
            }
            
            QListWidget::item {
                padding: 3px 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            
            QListWidget::item:selected {
                background-color: #e0e0e0;
                border: none;
            }
            
            QListWidget::item:alternate {
                background-color: #f9f9f9;
            }
        """)
    
    def add_log(self, message, level="INFO", timestamp=None):
        """添加日志项
        
        Args:
            message: 日志消息
            level: 日志级别 (INFO, SUCCESS, WARNING, ERROR, SYSTEM, DEBUG)
            timestamp: 时间戳，如果为None则不显示
        """
        # 构造日志内容
        if timestamp:
            log_text = f"[{timestamp}] [{level}] {message}"
        else:
            log_text = f"[{level}] {message}"
        
        # 创建列表项
        item = QListWidgetItem(log_text)
        
        # 设置颜色
        color = self.level_colors.get(level, QColor(0, 0, 0))
        item.setForeground(QBrush(color))
        
        # 添加到列表顶部
        self.insertItem(0, item)
        
        # 如果日志项太多，删除旧的日志
        if self.count() > 500:
            self.takeItem(self.count() - 1)
    
    def clear_logs(self):
        """清空日志列表"""
        self.clear()
    
    def copy_selected(self):
        """复制选中的日志到剪贴板"""
        from PySide6.QtGui import QGuiApplication
        
        selected_items = self.selectedItems()
        if not selected_items:
            return
            
        # 构造要复制的文本
        text = "\n".join(item.text() for item in selected_items)
        
        # 复制到剪贴板
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        
    def copy_all(self):
        """复制所有日志到剪贴板"""
        from PySide6.QtGui import QGuiApplication
        
        if self.count() == 0:
            return
            
        # 构造要复制的文本
        text = "\n".join(self.item(i).text() for i in range(self.count()))
        
        # 复制到剪贴板
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
