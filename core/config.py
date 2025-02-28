import json
import os

class Config:
    """配置管理类"""
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = {
            'interval': 1000,
            'push_interval': 0,
            'app_token': '',
            'uid': '',
            'keywords': [],
            'log_path': ''
        }
        
    def load(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                return True, "配置加载完成"
            return False, "未找到配置文件，将使用默认设置"
        except Exception as e:
            return False, f"配置加载失败: {str(e)}"
            
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True, "配置保存成功"
        except Exception as e:
            return False, f"配置保存失败: {str(e)}"
    
    def update(self, new_config):
        """更新配置"""
        self.config.update(new_config)
        
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
