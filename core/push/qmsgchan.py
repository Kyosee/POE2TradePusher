import requests
from .base import PushBase

class QmsgChan(PushBase):
    """Qmsg酱推送实现"""
    
    def __init__(self, config, log_callback=None):
        super().__init__(config, log_callback)
        self.api_url = "https://qmsg.zendee.cn/send/"
        
    def validate_config(self):
        """验证Qmsg酱配置"""
        qmsg_config = self.config.get('qmsgchan', {})
        key = qmsg_config.get('key')
        qq = qmsg_config.get('qq')
        
        if not key:
            return False, "请配置Qmsg酱的Key"
        if not qq:
            return False, "请配置接收消息的QQ号码"
            
        return True, "Qmsg酱配置验证通过"
        
    def send(self, keyword, content):
        """发送Qmsg酱推送"""
        try:
            # 验证配置
            success, msg = self.validate_config()
            if not success:
                self.log_callback(msg, "ERROR")
                return False, msg
                
            # 构造消息
            message = f"🔔 日志报警 [{keyword}]\n{content}"
            self.log_callback(f"Qmsg酱推送内容: {message}", "ALERT")
            
            # 发送请求
            key = self.config.get('qmsgchan', {}).get('key')
            qq = self.config.get('qmsgchan', {}).get('qq')
            response = requests.post(
                f"{self.api_url}{key}",
                data={
                    "msg": message,
                    "qq": qq
                },
                timeout=10
            )
            
            # 处理响应
            result = response.json()
            if result.get("success") != True:
                raise Exception(result.get("reason", "未知错误"))
                
            self.log_callback("Qmsg酱推送成功", "INFO")
            return True, "推送成功"
            
        except Exception as e:
            error_msg = f"Qmsg酱推送失败: {str(e)}"
            self.log_callback(error_msg, "ERROR")
            return False, error_msg
            
    def test(self):
        """测试Qmsg酱配置"""
        return self.send("测试", "这是一条测试消息，如果您收到说明Qmsg酱推送配置正确。")