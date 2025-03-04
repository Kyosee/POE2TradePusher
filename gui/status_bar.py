from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout

class StatusBarWidget(QWidget):
    """状态栏组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 0, 5, 0)
        
        # 创建状态文本标签
        self.status_label = QLabel("就绪")
        self.status_label.setProperty('class', 'status-label')
        self.layout.addWidget(self.status_label)
        
        # 添加弹性空间
        self.layout.addStretch()
        
        # 创建通货价格标签
        self.price_label = QLabel("神圣石-等待获取...")
        self.price_label.setProperty('class', 'status-label')
        self.layout.addWidget(self.price_label)
        
    def set_status(self, text):
        """设置状态文本"""
        self.status_label.setText(text)
        
    def set_price(self, price):
        """设置价格文本"""
        self.price_label.setText(price)
