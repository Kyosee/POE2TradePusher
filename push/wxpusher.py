import requests
from .base import PushBase

class WxPusher(PushBase):
    """WxPusher推送实现"""
    
    def __init__(self, config, log_callback=None):
        super().__init__(config, log_callback)
        self.api_url = "http://wxpusher.zjiecode.com/api/send/message"
        
    def validate_config(self):
        """验证WxPusher配置"""
        wxpusher_config = self.config.get('wxpusher', {})
        app_token = wxpusher_config.get('app_token')
        uid = wxpusher_config.get('uid')
        
        if not app_token:
            return False, "请配置WxPusher的APP Token"
        if not uid:
            return False, "请配置WxPusher的用户UID"
            
        return True, "WxPusher配置验证通过"
        
    def send(self, keyword, content):
        """发送WxPusher推送"""
        try:
            # 验证配置
            success, msg = self.validate_config()
            if not success:
                self.log_callback(msg, "ERROR")
                return False, msg
                
            # 构造消息
            message = f"🔔 日志报警 [{keyword}]\n{content}"
            self.log_callback(f"推送内容: {message}", "ALERT")
            
            # 发送请求
            response = requests.post(
                self.api_url,
                json={
                    "appToken": self.config.get('wxpusher', {}).get('app_token'),
                    "content": message,
                    "contentType": 1,
                    "uids": [self.config.get('wxpusher', {}).get('uid')]
                },
                timeout=10
            )
            
            # 处理响应
            result = response.json()
            if result["code"] != 1000:
                raise Exception(result["msg"])
                
            self.log_callback("推送成功", "INFO")
            return True, "推送成功"
            
        except Exception as e:
            error_msg = f"推送失败: {str(e)}"
            self.log_callback(error_msg, "ERROR")
            return False, error_msg
            
    def test(self):
        """测试WxPusher配置"""
        return self.send("测试", "这是一条测试消息")
