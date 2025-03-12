import os
import threading
import logging
import torch

class ModelLoader:
    """模型加载器基类，提供通用的异步加载功能"""
    
    def __init__(self, logger=None):
        """初始化模型加载器
        
        Args:
            logger: 日志记录器，如果为None则创建新的记录器
        """
        self.model = None
        self.model_loaded = False
        self.loading_thread = None
        self.loading_lock = threading.Lock()
        
        # 设置日志记录器
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(self.__class__.__name__)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def is_loaded(self):
        """检查模型是否已加载"""
        return self.model_loaded
    
    def get_model(self):
        """获取模型实例"""
        return self.model
    
    def load_model_async(self, callback=None):
        """异步加载模型
        
        Args:
            callback: 加载完成后的回调函数
        """
        if self.loading_thread and self.loading_thread.is_alive():
            self.logger.info("模型正在加载中，请等待...")
            return
            
        self.loading_thread = threading.Thread(
            target=self._load_model_thread,
            args=(callback,),
            daemon=True
        )
        self.loading_thread.start()
    
    def _load_model_thread(self, callback=None):
        """模型加载线程函数
        
        Args:
            callback: 加载完成后的回调函数
        """
        with self.loading_lock:
            try:
                self.logger.info(f"开始加载{self.__class__.__name__}模型...")
                self._load_model_impl()
                self.model_loaded = True
                self.logger.info(f"{self.__class__.__name__}模型加载完成")
                
                # 执行回调
                if callback:
                    callback(True, None)
            except Exception as e:
                self.logger.error(f"{self.__class__.__name__}模型加载失败: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                self.model_loaded = False
                
                # 执行回调
                if callback:
                    callback(False, str(e))
    
    def _load_model_impl(self):
        """模型加载实现，子类必须重写此方法"""
        raise NotImplementedError("子类必须实现_load_model_impl方法")


class OCRModelLoader(ModelLoader):
    """OCR模型加载器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(OCRModelLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, model_dir='assets/model', logger=None):
        """初始化OCR模型加载器
        
        Args:
            model_dir: 模型目录
            logger: 日志记录器
        """
        if self._initialized:
            return
            
        super().__init__(logger)
        self.det_model_dir = os.path.join(model_dir, 'ch_PP-OCRv4_det_infer')
        self.rec_model_dir = os.path.join(model_dir, 'ch_PP-OCRv4_rec_infer')
        self._initialized = True
    
    def _load_model_impl(self):
        """加载OCR模型"""
        from paddleocr import PaddleOCR
        self.model = PaddleOCR(
            use_angle_cls=True, 
            det_model_dir=self.det_model_dir,
            rec_model_dir=self.rec_model_dir,
            lang="ch", 
            show_log=False, 
            use_mp=True,
            total_process_num=2,
            use_pp_ocr_v4=True,
            enable_mkldnn=True,
            det_algorithm="DB",
            rec_algorithm="SVTR_LCNet",
        )


class YOLOModelLoader(ModelLoader):
    """YOLO模型加载器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(YOLOModelLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, model_path="models/poe_item_yolov12.pt", logger=None):
        """初始化YOLO模型加载器
        
        Args:
            model_path: 模型路径
            logger: 日志记录器
        """
        if self._initialized:
            return
            
        super().__init__(logger)
        self.model_path = model_path
        self.supported_items = {}
        self.use_cuda = torch.cuda.is_available()
        self.device = torch.device("cuda" if self.use_cuda else "cpu")
        self.detection_threshold = 0.45
        self._initialized = True
    
    def _load_model_impl(self):
        """加载YOLO模型"""
        if not os.path.exists(self.model_path):
            self.logger.warning(f"未找到YOLOv12模型: {self.model_path}")
            raise FileNotFoundError(f"未找到模型文件: {self.model_path}")
            
        # 直接从本地加载模型文件，而不是通过torch hub
        try:
            self.logger.info(f"正在从本地加载YOLOv12模型: {self.model_path}")
            self.model = torch.load(self.model_path, map_location=self.device)
            
            # 检查模型类型并正确处理
            if isinstance(self.model, tuple):
                self.logger.info("加载的模型是tuple类型，尝试提取模型对象")
                # 通常tuple的第一个元素是模型
                self.model = self.model[0]
            
            # 如果加载的是state_dict而不是完整模型，需要额外处理
            if isinstance(self.model, dict) and 'model' in self.model:
                from ultralytics.nn.tasks import attempt_load_one_weight
                self.model = attempt_load_one_weight(self.model_path, device=self.device)
            
            # 确保模型是正确的类型
            if not hasattr(self.model, 'conf'):
                self.logger.warning(f"加载的模型没有conf属性，可能不是预期的YOLO模型类型: {type(self.model)}")
                from ultralytics import YOLO
                # 尝试使用YOLO类加载模型
                try:
                    self.model = YOLO(self.model_path)
                except Exception as e:
                    self.logger.error(f"尝试使用YOLO类加载模型失败: {str(e)}")
                    raise
            
            # 设置模型参数
            self.model.conf = self.detection_threshold  # 置信度阈值
            self.model.iou = 0.45  # NMS IOU阈值
            self.model.classes = None  # 检测所有类别
            self.model.max_det = 100  # 最大检测数量
            self.model.agnostic = True  # 类别无关的NMS
            self.model.multi_label = False  # 每个框只分配一个类别
            self.model.amp = True  # 使用自动混合精度推理
            
            # YOLOv12特有的设置
            self.model.verbose = False  # 禁止冗余输出
            if hasattr(self.model, 'dynamic'):
                self.model.dynamic = True  # 动态ONNX导出
            
            # 记录支持的通货类型
            self.supported_items = self.model.names
            self.logger.info(f"YOLOv12模型已加载: {self.model_path}")
            self.logger.info(f"支持的物品类型: {self.supported_items}")
        except Exception as e:
            self.logger.error(f"加载YOLOv12模型失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
    
    def set_detection_threshold(self, threshold):
        """设置检测阈值
        
        Args:
            threshold: 检测阈值，范围0-1
        """
        self.detection_threshold = threshold
        if self.model:
            self.model.conf = threshold