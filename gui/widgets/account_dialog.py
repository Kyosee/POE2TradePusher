from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                              QPushButton, QFrame, QMessageBox)
from PySide6.QtCore import Qt

class AccountDialog(QDialog):
    """账号编辑对话框，用于添加和编辑账号信息"""
    
    def __init__(self, parent, account=None, title="添加账号"):
        """初始化账号编辑对话框
        
        Args:
            parent: 父窗口
            account: 账号信息字典，用于编辑模式，None表示添加模式
            title: 对话框标题
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)
        self.setModal(True)
        
        # 保存账号信息
        self.account = account or {}
        self.result_account = None
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        
        # 创建表单
        self._create_form()
        
        # 创建按钮区域
        self._create_buttons()
        
        # 如果是编辑模式，填充表单
        if account:
            self._fill_form(account)
    
    def _create_form(self):
        """创建表单区域"""
        form_frame = QFrame()
        form_frame.setProperty('class', 'card-frame')
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(10)
        
        # 邮箱
        email_layout = QHBoxLayout()
        email_label = QLabel("邮箱:")
        email_label.setFixedWidth(80)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("请输入邮箱")
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        form_layout.addLayout(email_layout)
        
        # 密码
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFixedWidth(80)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        # Steam账号
        steam_account_layout = QHBoxLayout()
        steam_account_label = QLabel("Steam账号:")
        steam_account_label.setFixedWidth(80)
        self.steam_account_input = QLineEdit()
        self.steam_account_input.setPlaceholderText("请输入Steam账号（可选）")
        steam_account_layout.addWidget(steam_account_label)
        steam_account_layout.addWidget(self.steam_account_input)
        form_layout.addLayout(steam_account_layout)
        
        # Steam密码
        steam_password_layout = QHBoxLayout()
        steam_password_label = QLabel("Steam密码:")
        steam_password_label.setFixedWidth(80)
        self.steam_password_input = QLineEdit()
        self.steam_password_input.setPlaceholderText("请输入Steam密码（可选）")
        steam_password_layout.addWidget(steam_password_label)
        steam_password_layout.addWidget(self.steam_password_input)
        form_layout.addLayout(steam_password_layout)
        
        # 邮箱密码
        email_password_layout = QHBoxLayout()
        email_password_label = QLabel("邮箱密码:")
        email_password_label.setFixedWidth(80)
        self.email_password_input = QLineEdit()
        self.email_password_input.setPlaceholderText("请输入邮箱密码（可选）")
        email_password_layout.addWidget(email_password_label)
        email_password_layout.addWidget(self.email_password_input)
        form_layout.addLayout(email_password_layout)
        
        # 备注
        note_layout = QHBoxLayout()
        note_label = QLabel("备注:")
        note_label.setFixedWidth(80)
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("请输入备注信息（可选）")
        note_layout.addWidget(note_label)
        note_layout.addWidget(self.note_input)
        form_layout.addLayout(note_layout)
        
        self.main_layout.addWidget(form_frame)
    
    def _create_buttons(self):
        """创建按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 确定按钮
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setProperty('class', 'normal-button')
        self.ok_btn.clicked.connect(self._on_ok_clicked)
        button_layout.addWidget(self.ok_btn)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setProperty('class', 'danger-button')
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.main_layout.addLayout(button_layout)
    
    def _fill_form(self, account):
        """填充表单数据
        
        Args:
            account: 账号信息字典
        """
        self.email_input.setText(account.get('email', ''))
        self.password_input.setText(account.get('password', ''))
        self.steam_account_input.setText(account.get('steam_account', ''))
        self.steam_password_input.setText(account.get('steam_password', ''))
        self.email_password_input.setText(account.get('email_password', ''))
        self.note_input.setText(account.get('note', ''))
    
    def _on_ok_clicked(self):
        """确定按钮点击事件"""
        # 获取表单数据
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # 验证必填字段
        if not email or not password:
            QMessageBox.warning(self, "输入错误", "邮箱和密码不能为空")
            return
        
        # 构建账号信息
        self.result_account = {
            'email': email,
            'password': password,
            'steam_account': self.steam_account_input.text().strip(),
            'steam_password': self.steam_password_input.text(),
            'email_password': self.email_password_input.text(),
            'note': self.note_input.text().strip()
        }
        
        # 如果是编辑模式，保留原有的其他字段
        if self.account:
            for key, value in self.account.items():
                if key not in self.result_account:
                    self.result_account[key] = value
        
        self.accept()
    
    def get_account(self):
        """获取账号信息
        
        Returns:
            dict: 账号信息字典，如果取消则返回None
        """
        return self.result_account