from abc import ABC, abstractmethod
import logging

class ProcessModule(ABC):
    """流程模块基类"""
    
    def __init__(self):
        """初始化基类，设置日志记录器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    @abstractmethod
    def name(self) -> str:
        """模块名称"""
        pass

    @abstractmethod
    def description(self) -> str:
        """模块描述"""
        pass
        
    @abstractmethod
    def run(self, **kwargs):
        """
        运行模块
        
        参数：
            preview_enabled (bool): 是否启用预览功能，默认为 False
            **kwargs: 其他模块特定参数
        """
        pass
