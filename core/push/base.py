from abc import ABC, abstractmethod

class PushBase(ABC):
    """推送基类，定义推送接口"""
    
    def __init__(self, config, log_callback=None):
        """
        初始化推送器
        :param config: 配置对象
        :param log_callback: 日志回调函数
        """
        self.config = config
        self.log_callback = log_callback or (lambda msg, level: None)
        
    @abstractmethod
    def send(self, keyword, content):
        """
        发送推送
        :param keyword: 触发的关键词
        :param content: 推送内容
        :return: (success, message)
        """
        pass
        
    @abstractmethod
    def test(self):
        """
        测试推送配置
        :return: (success, message)
        """
        pass
        
    @abstractmethod
    def validate_config(self):
        """
        验证推送配置
        :return: (success, message)
        """
        pass
