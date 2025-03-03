import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.currency_fetcher import CurrencyFetcher
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Currency Fetcher Test")
        self.setGeometry(100, 100, 400, 200)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建价格显示标签
        self.price_label = QLabel("等待获取...")
        self.price_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.price_label)
        
        # 初始化currency fetcher
        self.fetcher = CurrencyFetcher(interval_minutes=1)  # 测试用1分钟间隔
        self.fetcher.price_updated.connect(self.update_price)
        self.fetcher.start()
        
    def update_price(self, price):
        """更新价格显示"""
        self.price_label.setText(price)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
