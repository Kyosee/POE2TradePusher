import re
import requests
import threading
import logging
from utils.model_loader import ModelLoader

class PriceLoader(ModelLoader):
    """价格加载器，用于异步获取神圣石价格"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(PriceLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, interval_minutes=5, logger=None):
        """初始化价格加载器
        
        Args:
            interval_minutes: 价格更新间隔（分钟）
            logger: 日志记录器
        """
        if self._initialized:
            return
            
        super().__init__(logger)
        self.url = "https://www.dd373.com/s-3hcpqw-0-0-0-0-0-8rknmp-0-0-0-0-0-1-0-5-0.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.interval_minutes = interval_minutes
        self.price = "未获取"
        self.price_callbacks = []
        self.update_timer = None
        self._initialized = True
    
    def _load_model_impl(self):
        """实现价格获取逻辑"""
        self.fetch_price()
        
        # 设置定时更新
        if self.interval_minutes > 0:
            self._setup_timer()
    
    def _setup_timer(self):
        """设置定时器进行价格更新"""
        if self.update_timer:
            return
            
        self.update_timer = threading.Timer(self.interval_minutes * 60, self._timer_callback)
        self.update_timer.daemon = True
        self.update_timer.start()
    
    def _timer_callback(self):
        """定时器回调函数"""
        self.fetch_price()
        # 重新设置定时器
        self._setup_timer()
    
    def fetch_price(self):
        """获取神圣石价格"""
        try:
            # 禁用SSL验证
            response = requests.get(self.url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'utf-8'
            
            # 使用正则表达式查找价格信息
            match = re.search(r'<p class="font12 color666 m-t5">([^<]+)</p>', response.text)
            if match:
                self.price = match.group(1).strip()
                price_text = f"神圣石-{self.price}"
                self.logger.info(f"价格更新: {price_text}")
                
                # 触发回调
                self._notify_callbacks(price_text)
            else:
                self.price = "获取失败"
                self.logger.warning("价格获取失败: 未找到匹配内容")
                self._notify_callbacks("神圣石-获取失败")
        except Exception as e:
            self.price = f"错误: {str(e)}"
            self.logger.error(f"价格获取错误: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            self._notify_callbacks(f"神圣石-错误: {str(e)}")
    
    def get_price(self):
        """获取当前价格"""
        return self.price
    
    def add_callback(self, callback):
        """添加价格更新回调函数
        
        Args:
            callback: 回调函数，接收价格文本作为参数
        """
        if callback not in self.price_callbacks:
            self.price_callbacks.append(callback)
    
    def remove_callback(self, callback):
        """移除价格更新回调函数"""
        if callback in self.price_callbacks:
            self.price_callbacks.remove(callback)
    
    def _notify_callbacks(self, price_text):
        """通知所有回调函数"""
        for callback in self.price_callbacks:
            try:
                callback(price_text)
            except Exception as e:
                self.logger.error(f"执行价格回调时出错: {str(e)}")
    
    def set_interval(self, minutes):
        """设置更新间隔
        
        Args:
            minutes: 更新间隔（分钟）
        """
        self.interval_minutes = minutes
        # 如果定时器已存在，重新设置
        if self.update_timer:
            self.update_timer.cancel()
            self.update_timer = None
            self._setup_timer()