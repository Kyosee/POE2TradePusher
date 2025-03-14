from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QPushButton, QLineEdit, QFrame, QGridLayout,
                                    QScrollArea)
from PySide6.QtCore import Qt
from ..styles import Styles
from ..utils import LoggingMixin, ConfigMixin, show_message
from gui.widgets.switch import Switch
from gui.widgets.dialog import MessageDialog
from utils.help_texts import WXPUSHER_HELP, SERVERCHAN_HELP, QMSG_HELP, EMAIL_HELP
from gui.widgets.toast import Toast

class PushManagePage(QWidget, LoggingMixin, ConfigMixin):
    def __init__(self, master, callback_log, callback_status):
        super().__init__(master)
        LoggingMixin.__init__(self, callback_log, callback_status)
        self.init_config()  # 初始化配置对象
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        # 创建内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 6, 12, 6)
        self.content_layout.setSpacing(6)
        
        # 设置滚动区域样式
        self.scroll_area.setStyleSheet(Styles().scroll_area_style)
        
        # 创建推送配置区域
        self._create_wxpusher_frame()  # WxPusher配置
        self._create_serverchan_frame()  # Server酱配置
        self._create_qmsgchan_frame()      # Qmsg酱配置
        self._create_email_frame()     # 邮箱配置
        
        # 设置滚动区域的内容并添加到主布局
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

    def _create_enable_switch(self, text):
        """创建启用/禁用开关"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 创建Switch
        switch = Switch()
        
        # 创建标签
        label = QLabel(text)
        
        layout.addWidget(switch)
        layout.addWidget(label)
        layout.addStretch()
        
        return container, switch
        
    def _create_wxpusher_frame(self):
        """创建WxPusher配置区域"""
        # 创建框架
        wxpusher_frame = QFrame()
        wxpusher_frame.setProperty('class', 'card-frame')
        
        # 创建布局
        layout = QGridLayout(wxpusher_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("WxPusher配置")
        title_label.setProperty('class', 'card-title')
        layout.addWidget(title_label, 0, 0, 1, 3)
        
        # 启用开关
        switch_container, self.wxpusher_enabled = self._create_enable_switch("启用WxPusher推送")
        layout.addWidget(switch_container, 1, 0, 1, 3)
        self.wxpusher_enabled.stateChanged.connect(self._on_config_change)
        
        # AppToken
        layout.addWidget(QLabel("App Token:"), 2, 0)
        self.app_token_entry = QLineEdit()
        self.app_token_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.app_token_entry, 2, 1)
        
        # UID
        layout.addWidget(QLabel("用户UID:"), 3, 0)
        self.uid_entry = QLineEdit()
        self.uid_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.uid_entry, 3, 1)
        
        # 测试按钮
        self.test_wxpusher_btn = QPushButton("🔔 测试")
        self.test_wxpusher_btn.clicked.connect(self.test_wxpusher)
        self.test_wxpusher_btn.setProperty('class', 'normal-button')
        self.test_wxpusher_btn.setFixedWidth(80)
        layout.addWidget(self.test_wxpusher_btn, 2, 2)
        
        # 帮助按钮
        help_btn = QPushButton("❔ 帮助")
        help_btn.clicked.connect(self.show_wxpusher_help)
        help_btn.setProperty('class', 'control-save-button')
        help_btn.setFixedWidth(80)
        layout.addWidget(help_btn, 3, 2)
        
        self.content_layout.addWidget(wxpusher_frame)
        
    def _create_email_frame(self):
        """创建邮箱配置区域"""
        # 创建框架
        email_frame = QFrame()
        email_frame.setProperty('class', 'card-frame')
        
        # 创建布局
        layout = QGridLayout(email_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("邮箱配置")
        title_label.setProperty('class', 'card-title')
        layout.addWidget(title_label, 0, 0, 1, 3)
        
        # 启用开关
        switch_container, self.email_enabled = self._create_enable_switch("启用邮箱推送")
        layout.addWidget(switch_container, 1, 0, 1, 3)
        self.email_enabled.stateChanged.connect(self._on_config_change)
        
        # SMTP服务器
        layout.addWidget(QLabel("SMTP服务器:"), 2, 0)
        self.smtp_server_entry = QLineEdit()
        self.smtp_server_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.smtp_server_entry, 2, 1)
        
        # SMTP端口
        layout.addWidget(QLabel("SMTP端口:"), 3, 0)
        self.smtp_port_entry = QLineEdit()
        self.smtp_port_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.smtp_port_entry, 3, 1)
        
        # 发件人邮箱
        layout.addWidget(QLabel("发件人邮箱:"), 4, 0)
        self.sender_email_entry = QLineEdit()
        self.sender_email_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.sender_email_entry, 4, 1)
        
        # 邮箱密码/授权码
        layout.addWidget(QLabel("密码/授权码:"), 5, 0)
        self.email_password_entry = QLineEdit()
        self.email_password_entry.setEchoMode(QLineEdit.Password)
        self.email_password_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.email_password_entry, 5, 1)
        
        # 收件人邮箱
        layout.addWidget(QLabel("收件人邮箱:"), 6, 0)
        self.receiver_email_entry = QLineEdit()
        self.receiver_email_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.receiver_email_entry, 6, 1)
        
        # 按钮容器
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        
        # 测试按钮
        self.test_email_btn = QPushButton("📧 测试")
        self.test_email_btn.clicked.connect(self.test_email)
        self.test_email_btn.setProperty('class', 'normal-button')
        self.test_email_btn.setFixedWidth(80)
        layout.addWidget(self.test_email_btn, 4, 2)
        
        # 帮助按钮
        help_btn = QPushButton("❔ 帮助")
        help_btn.clicked.connect(self.show_email_help)
        help_btn.setProperty('class', 'control-save-button')
        help_btn.setFixedWidth(80)
        layout.addWidget(help_btn, 5, 2)
        
        self.content_layout.addWidget(email_frame)

    def _create_serverchan_frame(self):
        """创建Server酱配置区域"""
        # 创建框架
        serverchan_frame = QFrame()
        serverchan_frame.setProperty('class', 'card-frame')
        
        # 创建布局
        layout = QGridLayout(serverchan_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("Server酱配置")
        title_label.setProperty('class', 'card-title')
        layout.addWidget(title_label, 0, 0, 1, 3)
        
        # 启用开关
        switch_container, self.serverchan_enabled = self._create_enable_switch("启用Server酱推送")
        layout.addWidget(switch_container, 1, 0, 1, 3)
        self.serverchan_enabled.stateChanged.connect(self._on_config_change)
        
        # SendKey
        layout.addWidget(QLabel("SendKey:"), 2, 0)
        self.serverchan_key_entry = QLineEdit()
        self.serverchan_key_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.serverchan_key_entry, 2, 1)
        
        # 测试按钮
        self.test_serverchan_btn = QPushButton("🔔 测试")
        self.test_serverchan_btn.clicked.connect(self.test_serverchan)
        self.test_serverchan_btn.setProperty('class', 'normal-button')
        self.test_serverchan_btn.setFixedWidth(80)
        layout.addWidget(self.test_serverchan_btn, 2, 2)
        
        # 帮助按钮
        help_btn = QPushButton("❔ 帮助")
        help_btn.clicked.connect(self.show_serverchan_help)
        help_btn.setProperty('class', 'control-save-button')
        help_btn.setFixedWidth(80)
        layout.addWidget(help_btn, 3, 2)
        
        self.content_layout.addWidget(serverchan_frame)

    def _create_qmsgchan_frame(self):
        """创建Qmsg酱配置区域"""
        # 创建框架
        qmsgchan_frame = QFrame()
        qmsgchan_frame.setProperty('class', 'card-frame')
        
        # 创建布局
        layout = QGridLayout(qmsgchan_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("Qmsg酱配置")
        title_label.setProperty('class', 'card-title')
        layout.addWidget(title_label, 0, 0, 1, 3)
        
        # 启用开关
        switch_container, self.qmsgchan_enabled = self._create_enable_switch("启用Qmsg酱推送")
        layout.addWidget(switch_container, 1, 0, 1, 3)
        self.qmsgchan_enabled.stateChanged.connect(self._on_config_change)
        
        # Key
        layout.addWidget(QLabel("Key:"), 2, 0)
        self.qmsgchan_key_entry = QLineEdit()
        self.qmsgchan_key_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.qmsgchan_key_entry, 2, 1)
        
        # QQ
        layout.addWidget(QLabel("接收QQ:"), 3, 0)
        self.qmsgchan_qq_entry = QLineEdit()
        self.qmsgchan_qq_entry.textChanged.connect(self._on_config_change)
        layout.addWidget(self.qmsgchan_qq_entry, 3, 1)
        
        # 测试按钮
        self.test_qmsgchan_btn = QPushButton("🔔 测试")
        self.test_qmsgchan_btn.clicked.connect(self.test_qmsg)
        self.test_qmsgchan_btn.setProperty('class', 'normal-button')
        self.test_qmsgchan_btn.setFixedWidth(80)
        layout.addWidget(self.test_qmsgchan_btn, 2, 2)
        
        # 帮助按钮
        help_btn = QPushButton("❔ 帮助")
        help_btn.clicked.connect(self.show_qmsgchan_help)
        help_btn.setProperty('class', 'control-save-button')
        help_btn.setFixedWidth(80)
        layout.addWidget(help_btn, 3, 2)
        
        self.content_layout.addWidget(qmsgchan_frame)
        
    def test_wxpusher(self):
        """测试WxPusher配置"""
        if not self.wxpusher_enabled.isChecked():
            self.log_message("WxPusher推送未启用", "WARN")
            show_message("提示", "WxPusher推送未启用", "warning", self)
            return
            
        config = self.get_config_data()
        
        if not config.get('wxpusher', {}).get('app_token'):
            self.log_message("请先配置WxPusher的APP Token", "ERROR")
            self.update_status("❌ 缺少APP Token配置")
            show_message("错误", "请先配置WxPusher的APP Token", "error", self)
            return
            
        if not config.get('wxpusher', {}).get('uid'):
            self.log_message("请先配置WxPusher的用户UID", "ERROR")
            self.update_status("❌ 缺少用户UID配置")
            show_message("错误", "请先配置WxPusher的用户UID", "error", self)
            return
            
        self.log_message("正在测试WxPusher配置...", "INFO")
        show_message("测试", "正在发送WxPusher测试消息...", "info", self)
        from core.push.wxpusher import WxPusher
        pusher = WxPusher(config, self.log_message)
        success, message = pusher.test()
        
        if success:
            self.update_status("✅ 测试推送发送成功")
            self.log_message(message, "INFO")
            show_message("成功", "WxPusher测试推送发送成功", "success", self)
        else:
            self.update_status("❌ 测试推送发送失败")
            self.log_message(message, "ERROR")
            show_message("错误", f"WxPusher测试推送失败: {message}", "error", self)
            
    def test_email(self):
        """测试邮箱配置"""
        if not self.email_enabled.isChecked():
            self.log_message("邮箱推送未启用", "WARN")
            show_message("提示", "邮箱推送未启用", "warning", self)
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
                show_message("错误", message, "error", self)
                return
                
        self.log_message("正在测试邮箱配置...", "INFO")
        show_message("测试", "正在发送测试邮件...", "info", self)
        from core.push.email_pusher import EmailPusher
        pusher = EmailPusher(config, self.log_message)
        success, message = pusher.test()
        
        if success:
            self.update_status("✅ 测试邮件发送成功")
            self.log_message(message, "INFO")
            show_message("成功", "测试邮件发送成功", "success", self)
        else:
            self.update_status("❌ 测试邮件发送失败")
            self.log_message(message, "ERROR")
            show_message("错误", f"测试邮件发送失败: {message}", "error", self)

    def test_serverchan(self):
        """测试Server酱配置"""
        if not self.serverchan_enabled.isChecked():
            self.log_message("Server酱推送未启用", "WARN")
            show_message("提示", "Server酱推送未启用", "warning", self)
            return
            
        config = self.get_config_data()
        
        if not config.get('serverchan', {}).get('send_key'):
            self.log_message("请先配置Server酱的SendKey", "ERROR")
            self.update_status("❌ 缺少SendKey配置")
            show_message("错误", "请先配置Server酱的SendKey", "error", self)
            return
            
        self.log_message("正在测试Server酱配置...", "INFO")
        show_message("测试", "正在发送Server酱测试消息...", "info", self)
        from core.push.serverchan import ServerChan
        pusher = ServerChan(config, self.log_message)
        success, message = pusher.test()
        
        if success:
            self.update_status("✅ 测试推送发送成功")
            self.log_message(message, "INFO")
            show_message("成功", "Server酱测试推送发送成功", "success", self)
        else:
            self.update_status("❌ 测试推送发送失败")
            self.log_message(message, "ERROR")
            show_message("错误", f"Server酱测试推送失败: {message}", "error", self)

    def test_qmsg(self):
        """测试Qmsg酱配置"""
        if not self.qmsgchan_enabled.isChecked():
            self.log_message("Qmsg酱推送未启用", "WARN")
            show_message("提示", "Qmsg酱推送未启用", "warning", self)
            return
            
        config = self.get_config_data()
        qmsg_config = config.get('qmsgchan', {})
        
        if not qmsg_config.get('key'):
            self.log_message("请先配置Qmsg酱的Key", "ERROR")
            self.update_status("❌ 缺少Key配置")
            show_message("错误", "请先配置Qmsg酱的Key", "error", self)
            return
            
        if not qmsg_config.get('qq'):
            self.log_message("请先配置接收QQ", "ERROR")
            self.update_status("❌ 缺少QQ配置")
            show_message("错误", "请先配置接收QQ", "error", self)
            return
            
        self.log_message("正在测试Qmsg酱配置...", "INFO")
        show_message("测试", "正在发送Qmsg酱测试消息...", "info", self)
        from core.push.qmsgchan import QmsgChan
        pusher = QmsgChan(config, self.log_message)
        success, message = pusher.test()
        
        if success:
            self.update_status("✅ 测试推送发送成功")
            self.log_message(message, "INFO")
            show_message("成功", "Qmsg酱测试推送发送成功", "success", self)
        else:
            self.update_status("❌ 测试推送发送失败")
            self.log_message(message, "ERROR")
            show_message("错误", f"Qmsg酱测试推送失败: {message}", "error", self)
        
    def get_config_data(self):
        """获取配置数据"""
        return {
            'wxpusher': {
                'enabled': self.wxpusher_enabled.isChecked(),
                'app_token': self.app_token_entry.text(),
                'uid': self.uid_entry.text()
            },
            'email': {
                'enabled': self.email_enabled.isChecked(),
                'smtp_server': self.smtp_server_entry.text(),
                'smtp_port': self.smtp_port_entry.text(),
                'sender_email': self.sender_email_entry.text(),
                'email_password': self.email_password_entry.text(),
                'receiver_email': self.receiver_email_entry.text()
            },
            'serverchan': {
                'enabled': self.serverchan_enabled.isChecked(),
                'send_key': self.serverchan_key_entry.text()
            },
            'qmsgchan': {
                'enabled': self.qmsgchan_enabled.isChecked(),
                'key': self.qmsgchan_key_entry.text(),
                'qq': self.qmsgchan_qq_entry.text()
            }
        }
        
    def show_wxpusher_help(self):
        """显示WxPusher配置帮助"""
        dialog = MessageDialog(self, "WxPusher配置帮助", WXPUSHER_HELP)
        dialog.exec()  # 使用exec()方法显示模态对话框
        show_message("帮助", "已显示WxPusher配置帮助", "info", self)
        
    def show_email_help(self):
        """显示邮箱配置帮助"""
        dialog = MessageDialog(self, "邮箱配置帮助", EMAIL_HELP)
        dialog.exec()  # 使用exec()方法显示模态对话框
        show_message("帮助", "已显示邮箱配置帮助", "info", self)

    def show_serverchan_help(self):
        """显示Server酱配置帮助"""
        dialog = MessageDialog(self, "Server酱配置帮助", SERVERCHAN_HELP)
        dialog.exec()  # 使用exec()方法显示模态对话框
        show_message("帮助", "已显示Server酱配置帮助", "info", self)

    def show_qmsgchan_help(self):
        """显示Qmsg酱配置帮助"""
        dialog = MessageDialog(self, "Qmsg酱配置帮助", QMSG_HELP)
        dialog.exec()  # 使用exec()方法显示模态对话框
        show_message("帮助", "已显示Qmsg酱配置帮助", "info", self)
        
    def _on_config_change(self):
        """配置变更处理"""
        if hasattr(self, 'save_config') and self.save_config:
            self.save_config()
            show_message("保存", "配置已更新", "success", self)

    def set_config_data(self, data):
        """设置配置数据"""
        # WxPusher配置
        wxpusher_data = data.get('wxpusher', {})
        self.wxpusher_enabled.setChecked(wxpusher_data.get('enabled', False))
        self.app_token_entry.setText(wxpusher_data.get('app_token', ''))
        self.uid_entry.setText(wxpusher_data.get('uid', ''))
        
        # 邮箱配置
        email_data = data.get('email', {})
        self.email_enabled.setChecked(email_data.get('enabled', False))
        self.smtp_server_entry.setText(email_data.get('smtp_server', ''))
        self.smtp_port_entry.setText(email_data.get('smtp_port', ''))
        self.sender_email_entry.setText(email_data.get('sender_email', ''))
        self.email_password_entry.setText(email_data.get('email_password', ''))
        self.receiver_email_entry.setText(email_data.get('receiver_email', ''))
        
        # Server酱配置
        serverchan_data = data.get('serverchan', {})
        self.serverchan_enabled.setChecked(serverchan_data.get('enabled', False))
        self.serverchan_key_entry.setText(serverchan_data.get('send_key', ''))
        
        # Qmsg酱配置
        qmsg_data = data.get('qmsgchan', {})
        self.qmsgchan_enabled.setChecked(qmsg_data.get('enabled', False))
        self.qmsgchan_key_entry.setText(qmsg_data.get('key', ''))
        self.qmsgchan_qq_entry.setText(qmsg_data.get('qq', ''))
