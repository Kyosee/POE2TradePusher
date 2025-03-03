import requests
from .base import PushBase

class ServerChan(PushBase):
    """Server酱推送实现"""
    
    def __init__(self, config, log_callback=None):
        super().__init__(config, log_callback)
        self.api_url = "https://sctapi.ftqq.com/"
        
    def validate_config(self):
        """验证Server酱配置"""
        serverchan_config = self.config.get('serverchan', {})
        send_key = serverchan_config.get('send_key')
        
        if not send_key:
            return False, "请配置Server酱的SendKey"
            
        return True, "Server酱配置验证通过"
        
    def send(self, keyword, content):
        """发送Server酱推送"""
        try:
            # 验证配置
            success, msg = self.validate_config()
            if not success:
                self.log_callback(msg, "ERROR")
                return False, msg
                
            # 构造消息
            title = f"🔔 日志报警 [{keyword}]"
            self.log_callback(f"推送内容: {title}\n{content}", "ALERT")
            
            # 发送请求
            send_key = self.config.get('serverchan', {}).get('send_key')
            response = requests.post(
                f"{self.api_url}{send_key}.send",
                data={
                    "title": title,
                    "desp": content
                },
                timeout=10
            )
            
            # 处理响应
            result = response.json()
            if result.get("code") != 0:
                raise Exception(result.get("message", "未知错误"))
                
            self.log_callback("Server酱推送成功", "INFO")
            return True, "推送成功"
            
        except Exception as e:
            error_msg = f"Server酱推送失败: {str(e)}"
            self.log_callback(error_msg, "ERROR")
            return False, error_msg
            
    def test(self):
        """测试Server酱配置"""
        return self.send("测试", "这是一条测试消息，如果您收到说明Server酱推送配置正确。")