import os
import logging
import torch

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ModelDownloader")

class ModelDownloader:
    """
    模型管理器：负责检查和管理YOLOv12模型文件
    """
    
    def __init__(self):
        # 模型文件夹路径
        self.model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
        
        # 确保模型文件夹存在
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 模型文件路径
        self.yolov12_path = os.path.join(self.model_dir, "poe_currency_yolov12.pt")
    
    def check_and_download(self, force=False):
        """
        检查模型文件是否存在
        
        Args:
            force: 参数保留但不再使用
            
        Returns:
            bool: 是否有可用的模型文件
        """
        # 检查YOLO v12模型文件
        v12_exists = os.path.exists(self.yolov12_path) and os.path.getsize(self.yolov12_path) > 1000000
        
        # 如果没有找到模型文件
        if not v12_exists:
            logger.error("未找到YOLOv12模型文件！请确保模型文件已放置在models文件夹中。")
            return False
        
        # 如果已经有模型文件
        logger.info(f"YOLOv12模型文件已存在: {self.yolov12_path}")
        return True

if __name__ == "__main__":
    # 作为独立脚本运行时，检查模型
    downloader = ModelDownloader()
    downloader.check_and_download()
