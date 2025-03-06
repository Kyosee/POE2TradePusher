import re
import requests
from PySide6.QtCore import QObject, QTimer, Signal

class CurrencyFetcher(QObject):
    """通货价格获取器"""
    price_updated = Signal(str)  # 价格更新信号

    def __init__(self, interval_minutes=5):
        super().__init__()
        self.url = "https://www.dd373.com/s-3hcpqw-0-0-0-0-0-8rknmp-0-0-0-0-0-1-0-5-0.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_price)
        self.set_interval(interval_minutes)
        
    def set_interval(self, minutes):
        """设置获取间隔"""
        self.timer.setInterval(minutes * 60 * 1000)  # 转换为毫秒
        
    def start(self):
        """启动定时获取"""
        self.fetch_price()  # 立即获取一次
        self.timer.start()
        
    def stop(self):
        """停止定时获取"""
        self.timer.stop()
        
    def fetch_price(self):
        """获取价格"""
        try:
            # 禁用SSL验证 - 注意：这种方式不够安全，但在这个特定场景下是可接受的
            # TODO: 考虑在未来添加proper的证书验证
            response = requests.get(self.url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'utf-8'
            
            # 使用正则表达式查找第一个class为m-t5的p标签内容
            match = re.search(r'<p class="font12 color666 m-t5">([^<]+)</p>', response.text)
            if match:
                price = match.group(1).strip()
                self.price_updated.emit(f"神圣石-{price}")
            else:
                self.price_updated.emit("神圣石-获取失败")
        except Exception as e:
            self.price_updated.emit(f"神圣石-错误: {str(e)}")
