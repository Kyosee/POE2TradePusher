from tkinter import *
from tkinter import ttk
from gui.widgets.switch import Switch
from gui.widgets.dialog import MessageDialog
from ..utils import LoggingMixin, ConfigMixin, show_message

class PushManagePage(ttk.Frame, LoggingMixin, ConfigMixin):
    def __init__(self, master, callback_log, callback_status):
        ttk.Frame.__init__(self, master, style='Content.TFrame')
        LoggingMixin.__init__(self, callback_log, callback_status)
        
        # 创建推送配置区域
        self._create_wxpusher_frame()  # WxPusher配置
        self._create_email_frame()     # 邮箱配置

    def _create_enable_switch(self, parent, text, row=0, column=0, padx=(12,6), pady=3):
        """创建启用/禁用开关"""
        # 创建容器来放置Switch和标签
        container = ttk.Frame(parent, style='Content.TFrame')
        container.grid(row=row, column=column, padx=padx, pady=pady, sticky="w")
        
        # 创建Switch
        switch = Switch(container, width=50, height=26, pad_x=3, pad_y=3)
        switch.pack(side=LEFT, padx=(0, 8))
        
        # 创建标签
        label = ttk.Label(container, text=text, style='TLabel')
        label.pack(side=LEFT)
        
        return switch.checked
        
    def _create_wxpusher_frame(self):
        """创建WxPusher配置区域"""
        self.wxpusher_frame = ttk.LabelFrame(self, text="WxPusher配置")
        
        # 启用开关
        self.wxpusher_enabled = self._create_enable_switch(self.wxpusher_frame, "启用WxPusher推送")
        
        # AppToken
        ttk.Label(self.wxpusher_frame, text="App Token:", style='Frame.TLabel').grid(
            row=1, column=0, padx=(12,0), sticky="e")
        self.app_token_entry = ttk.Entry(self.wxpusher_frame, width=50, font=('Consolas', 10))
        self.app_token_entry.grid(row=1, column=1, padx=(0,6), sticky="ew")
        
        # UID
        ttk.Label(self.wxpusher_frame, text="用户UID:", style='Frame.TLabel').grid(
            row=2, column=0, padx=(12,0), sticky="e")
        self.uid_entry = ttk.Entry(self.wxpusher_frame, width=50, font=('Consolas', 10))
        self.uid_entry.grid(row=2, column=1, padx=(0,6), sticky="ew")
        
        # 按钮容器
        btn_frame = ttk.Frame(self.wxpusher_frame)
        btn_frame.grid(row=1, column=2, rowspan=2, padx=6, sticky="ns")
        
        # 测试按钮
        self.test_wxpusher_btn = ttk.Button(btn_frame, text="🔔 测试", 
                                          command=self.test_wxpusher, width=8)
        self.test_wxpusher_btn.pack(pady=(0,2))
        
        # 帮助按钮
        help_btn = ttk.Button(btn_frame, text="❔ 帮助",
                             command=self.show_wxpusher_help, width=8,
                             style='Control.Save.TButton')
        help_btn.pack()
        
        # 布局
        self.wxpusher_frame.pack(fill=X, padx=12, pady=(6,3))
        self.wxpusher_frame.columnconfigure(1, weight=1)
        
    def _create_email_frame(self):
        """创建邮箱配置区域"""
        self.email_frame = ttk.LabelFrame(self, text="邮箱配置")
        
        # 启用开关
        self.email_enabled = self._create_enable_switch(self.email_frame, "启用邮箱推送")
        
        # SMTP服务器
        ttk.Label(self.email_frame, text="SMTP服务器:", style='Frame.TLabel').grid(
            row=1, column=0, padx=(12,0), sticky="e")
        self.smtp_server_entry = ttk.Entry(self.email_frame, width=50, font=('Consolas', 10))
        self.smtp_server_entry.grid(row=1, column=1, padx=(0,6), sticky="ew")
        
        # SMTP端口
        ttk.Label(self.email_frame, text="SMTP端口:", style='Frame.TLabel').grid(
            row=2, column=0, padx=(12,0), sticky="e")
        self.smtp_port_entry = ttk.Entry(self.email_frame, width=50, font=('Consolas', 10))
        self.smtp_port_entry.grid(row=2, column=1, padx=(0,6), sticky="ew")
        
        # 发件人邮箱
        ttk.Label(self.email_frame, text="发件人邮箱:", style='Frame.TLabel').grid(
            row=3, column=0, padx=(12,0), sticky="e")
        self.sender_email_entry = ttk.Entry(self.email_frame, width=50, font=('Consolas', 10))
        self.sender_email_entry.grid(row=3, column=1, padx=(0,6), sticky="ew")
        
        # 邮箱密码/授权码
        ttk.Label(self.email_frame, text="密码/授权码:", style='Frame.TLabel').grid(
            row=4, column=0, padx=(12,0), sticky="e")
        self.email_password_entry = ttk.Entry(self.email_frame, width=50, font=('Consolas', 10), show='*')
        self.email_password_entry.grid(row=4, column=1, padx=(0,6), sticky="ew")
        
        # 收件人邮箱
        ttk.Label(self.email_frame, text="收件人邮箱:", style='Frame.TLabel').grid(
            row=5, column=0, padx=(12,0), sticky="e")
        self.receiver_email_entry = ttk.Entry(self.email_frame, width=50, font=('Consolas', 10))
        self.receiver_email_entry.grid(row=5, column=1, padx=(0,6), sticky="ew")
        
        # 按钮容器
        btn_frame = ttk.Frame(self.email_frame)
        btn_frame.grid(row=1, column=2, rowspan=2, padx=6, sticky="ns")
        
        # 测试按钮
        self.test_email_btn = ttk.Button(btn_frame, text="📧 测试", 
                                       command=self.test_email, width=8)
        self.test_email_btn.pack(pady=(0,2))
        
        # 帮助按钮
        help_btn = ttk.Button(btn_frame, text="❔ 帮助",
                             command=self.show_email_help, width=8,
                             style='Control.Save.TButton')
        help_btn.pack()
        
        # 布局
        self.email_frame.pack(fill=X, padx=12, pady=(3,6))
        self.email_frame.columnconfigure(1, weight=1)
        
    def test_wxpusher(self):
        """测试WxPusher配置"""
        if not self.wxpusher_enabled.get():
            self.log_message("WxPusher推送未启用", "WARN")
            return
            
        config = self.get_config_data()
        
        if not config.get('wxpusher', {}).get('app_token'):
            self.log_message("请先配置WxPusher的APP Token", "ERROR")
            self.update_status("❌ 缺少APP Token配置")
            return
            
        if not config.get('wxpusher', {}).get('uid'):
            self.log_message("请先配置WxPusher的用户UID", "ERROR")
            self.update_status("❌ 缺少用户UID配置")
            return
            
        self.log_message("正在测试WxPusher配置...", "INFO")
        from push.wxpusher import WxPusher
        pusher = WxPusher(config, self.log_message)
        success, message = pusher.test()
        
        if success:
            self.update_status("✅ 测试推送发送成功")
            self.log_message(message, "INFO")
        else:
            self.update_status("❌ 测试推送发送失败")
            self.log_message(message, "ERROR")
            
    def test_email(self):
        """测试邮箱配置"""
        if not self.email_enabled.get():
            self.log_message("邮箱推送未启用", "WARN")
            return
            
        config = self.get_config_data()
        email_config = config.get('email', {})
        
        # 验证必填字段
        required = {
            'smtp_server': '请配置SMTP服务器',
            'smtp_port': '请配置SMTP端口',
            'sender_email': '请配置发件人邮箱',
            'email_password': '请配置邮箱密码/授权码',
            'receiver_email': '请配置收件人邮箱'
        }
        
        for field, message in required.items():
            if not email_config.get(field):
                self.log_message(message, "ERROR")
                self.update_status(f"❌ {message}")
                return
                
        self.log_message("正在测试邮箱配置...", "INFO")
        from push.email_pusher import EmailPusher
        pusher = EmailPusher(config, self.log_message)
        success, message = pusher.test()
        
        if success:
            self.update_status("✅ 测试邮件发送成功")
            self.log_message(message, "INFO")
        else:
            self.update_status("❌ 测试邮件发送失败")
            self.log_message(message, "ERROR")
        
    def get_config_data(self):
        """获取配置数据"""
        return {
            'wxpusher': {
                'enabled': self.wxpusher_enabled.get(),
                'app_token': self.app_token_entry.get(),
                'uid': self.uid_entry.get()
            },
            'email': {
                'enabled': self.email_enabled.get(),
                'smtp_server': self.smtp_server_entry.get(),
                'smtp_port': self.smtp_port_entry.get(),
                'sender_email': self.sender_email_entry.get(),
                'email_password': self.email_password_entry.get(),
                'receiver_email': self.receiver_email_entry.get()
            }
        }
        
    def show_wxpusher_help(self):
        """显示WxPusher配置帮助"""
        help_text = (
            "WxPusher配置说明：\n\n"
            "1. 访问 http://wxpusher.zjiecode.com 注册登录\n\n"
            "2. 创建应用：\n"
            "   - 进入应用管理页面\n"
            "   - 点击「新建应用」\n"
            "   - 填写应用名称等信息\n"
            "   - 创建后可获取 App Token\n\n"
            "3. 获取用户UID：\n"
            "   - 使用微信扫码关注公众号\n"
            "   - 进入用户管理页面\n"
            "   - 可以看到你的用户UID\n\n"
            "4. 填写配置：\n"
            "   - 将获取到的 App Token 和 UID 填入对应输入框\n"
            "   - 点击测试按钮验证配置是否正确"
        )
        MessageDialog(self, "WxPusher配置帮助", help_text)
        
    def show_email_help(self):
        """显示邮箱配置帮助"""
        help_text = (
            "邮箱配置说明（以QQ邮箱为例）：\n\n"
            "1. SMTP服务器和端口：\n"
            "   - SMTP服务器：smtp.qq.com\n"
            "   - SMTP端口：465（SSL）\n\n"
            "2. 获取授权码：\n"
            "   - 登录QQ邮箱网页版\n"
            "   - 打开「设置」-「账户」\n"
            "   - 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」\n"
            "   - 开启「POP3/SMTP服务」\n"
            "   - 按提示操作获取授权码\n\n"
            "3. 填写配置：\n"
            "   - 发件人邮箱：你的QQ邮箱\n"
            "   - 密码/授权码：上一步获取的授权码\n"
            "   - 收件人邮箱：接收通知的邮箱地址\n\n"
            "4. 点击测试按钮验证配置是否正确"
        )
        MessageDialog(self, "邮箱配置帮助", help_text)
        
    def set_config_data(self, data):
        """设置配置数据"""
        # WxPusher配置
        wxpusher_data = data.get('wxpusher', {})
        self.wxpusher_enabled.set(wxpusher_data.get('enabled', True))
        self.app_token_entry.delete(0, END)
        self.app_token_entry.insert(0, wxpusher_data.get('app_token', ''))
        self.uid_entry.delete(0, END)
        self.uid_entry.insert(0, wxpusher_data.get('uid', ''))
        
        # 邮箱配置
        email_data = data.get('email', {})
        self.email_enabled.set(email_data.get('enabled', True))
        self.smtp_server_entry.delete(0, END)
        self.smtp_server_entry.insert(0, email_data.get('smtp_server', ''))
        self.smtp_port_entry.delete(0, END)
        self.smtp_port_entry.insert(0, email_data.get('smtp_port', ''))
        self.sender_email_entry.delete(0, END)
        self.sender_email_entry.insert(0, email_data.get('sender_email', ''))
        self.email_password_entry.delete(0, END)
        self.email_password_entry.insert(0, email_data.get('email_password', ''))
        self.receiver_email_entry.delete(0, END)
        self.receiver_email_entry.insert(0, email_data.get('receiver_email', ''))
