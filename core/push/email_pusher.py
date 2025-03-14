import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailPusher:
    def init(self, config, logger=None):
        """初始化邮件推送器
        Args:
        config: 包含邮箱配置信息的字典
        logger: 日志记录函数
        """
        self.config = config.get('email', {})
        self.logger = logger or (lambda msg, level: None)

    def _create_smtp_client(self):
        """创建SMTP客户端连接"""
        try:
            server = smtplib.SMTP_SSL(self.config['smtp_server'], 
                                    int(self.config['smtp_port']))
            server.login(self.config['sender_email'], 
                       self.config['email_password'])
            return server
        except Exception as e:
            self.logger(f"创建SMTP连接失败: {str(e)}", "ERROR")
            return None

    def test(self):
        """测试邮件发送"""
        try:
            server = self._create_smtp_client()
            if not server:
                return False, "SMTP连接失败"

            # 创建测试邮件
            msg = MIMEText("这是一条测试推送，如果您收到说明邮件推送配置正确。", 'plain', 'utf-8')
            msg['Subject'] = 'POE2交易助手 - 邮件推送测试'
            msg['From'] = self.config['sender_email']
            msg['To'] = self.config['receiver_email']

            # 发送测试邮件
            server.send_message(msg)
            server.quit()

            return True, "邮件测试发送成功"

        except Exception as e:
            return False, f"邮件测试发送失败: {str(e)}"

    def send(self, title, content):
        """发送邮件通知
        Args:
            title: 通知标题
            content: 通知内容
        Returns:
            success: 是否发送成功
            message: 结果信息
        """
        if not self.config.get('enabled', True):
            return False, "邮箱推送未启用"

        try:
            server = self._create_smtp_client()
            if not server:
                return False, "SMTP连接失败"

            # 创建邮件
            msg = MIMEMultipart()
            msg['Subject'] = f'POE2交易助手 - {title}'
            msg['From'] = self.config['sender_email']
            msg['To'] = self.config['receiver_email']

            # 添加HTML内容和纯文本内容
            text_content = MIMEText(content, 'plain', 'utf-8')
            html_content = MIMEText(f"<pre>{content}</pre>", 'html', 'utf-8')
            msg.attach(text_content)
            msg.attach(html_content)

            # 发送邮件
            server.send_message(msg)
            server.quit()

            return True, "邮件发送成功"

        except Exception as e:
            error_msg = f"邮件发送失败: {str(e)}"
            self.logger(error_msg, "ERROR")
            return False, error_msg