from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QMessageBox, QFrame, QSpinBox, QComboBox, QApplication
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QClipboard, QGuiApplication, QColor
from .recognition_base_page import RecognitionBasePage
from gui.styles import Styles
from gui.widgets.account_dialog import AccountDialog
from gui.utils import ask_yes_no  # 导入ask_yes_no函数
import time  # 添加time模块的导入

class AccountManagePage(QWidget):
    """账号管理页面"""
    
    def __init__(self, parent, log_message, update_status_bar, save_config=None):
        """初始化账号管理页面"""
        super().__init__(parent)
        self.log_message = log_message
        self.update_status_bar = update_status_bar
        self.save_config = save_config
        
        # 创建页面布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        # 创建标题
        title_label = QLabel("账号管理")
        title_label.setProperty('class', 'card-title')
        self.main_layout.addWidget(title_label)
        
        # 创建说明文本
        desc_label = QLabel("管理游戏账号信息，用于自动登录和切换账号")
        desc_label.setProperty('class', 'page-description')
        self.main_layout.addWidget(desc_label)
        
        # 加载账号数据
        self.accounts = []
        self.filtered_accounts = []  # 用于存储过滤后的账号列表
        self.is_verifying = False  # 添加验证状态标志
        
        # 分页设置
        self.current_page = 1
        self.page_size = 20  # 默认每页显示20条
        self.page_sizes = [15, 20, 50, 100]  # 可选的每页显示条数
        self.search_text = ""  # 搜索文本
        self.banned_filter = "全部"  # 封禁状态筛选，默认显示全部
        
        # 创建按钮区域
        self.create_button_area()
        
        # 创建账号表格
        self.create_account_table()
        
        # 创建右键菜单
        self._setup_account_menu()
        
        # 加载账号数据
        self.accounts = []
        self.filtered_accounts = []  # 用于存储过滤后的账号列表
        self.is_verifying = False  # 添加验证状态标志
        
        # 分页设置
        self.current_page = 1
        self.page_size = 20  # 默认每页显示20条
        self.page_sizes = [15, 20, 50, 100]  # 可选的每页显示条数
        self.search_text = ""  # 搜索文本
    
    def create_button_area(self):
        """创建按钮区域"""
        # 创建按钮区域框架
        button_frame = QFrame()
        button_frame.setProperty('class', 'card-frame')
        button_layout = QVBoxLayout(button_frame)
        button_layout.setContentsMargins(10, 10, 10, 10)
        
        # 按钮布局
        controls_layout = QHBoxLayout()
        
        # 线程数设置
        thread_layout = QHBoxLayout()
        thread_label = QLabel("线程数:")
        self.thread_count_input = QSpinBox()
        self.thread_count_input.setRange(1, 10)  # 设置范围为1-10
        self.thread_count_input.setValue(1)  # 默认值为1
        self.thread_count_input.valueChanged.connect(self.on_thread_count_changed)
        thread_layout.addWidget(thread_label)
        thread_layout.addWidget(self.thread_count_input)
        controls_layout.addLayout(thread_layout)
        
        # 粘贴板导入按钮
        self.import_btn = QPushButton("粘贴板导入")
        self.import_btn.setProperty('class', 'normal-button')
        self.import_btn.clicked.connect(self.import_from_clipboard)
        controls_layout.addWidget(self.import_btn)
        
        # 刷新状态按钮
        self.refresh_btn = QPushButton("刷新状态")
        self.refresh_btn.setProperty('class', 'normal-button')
        self.refresh_btn.clicked.connect(self.refresh_account_status)
        controls_layout.addWidget(self.refresh_btn)
        
        # 添加账号按钮
        self.add_btn = QPushButton("添加账号")
        self.add_btn.setProperty('class', 'normal-button')
        self.add_btn.clicked.connect(self.add_account)
        controls_layout.addWidget(self.add_btn)
        
        # 删除账号按钮
        self.delete_btn = QPushButton("删除账号")
        self.delete_btn.setProperty('class', 'danger-button')
        self.delete_btn.clicked.connect(self.remove_selected_account)
        controls_layout.addWidget(self.delete_btn)
        
        controls_layout.addStretch()
        button_layout.addLayout(controls_layout)
        
        self.main_layout.addWidget(button_frame)
        
    def create_account_table(self):
        """创建账号表格"""
        # 表格标题
        table_title = QLabel("账号列表")
        table_title.setProperty('class', 'card-title')
        self.main_layout.addWidget(table_title)
        
        # 创建表格框架
        table_frame = QFrame()
        table_frame.setProperty('class', 'card-frame')
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建搜索和分页控制区域
        search_layout = QHBoxLayout()
        
        # 搜索框
        search_label = QLabel("搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键字搜索账号")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        # 封禁状态筛选下拉框
        banned_label = QLabel("封禁状态:")
        self.banned_filter_combo = QComboBox()
        self.banned_filter_combo.addItems(["全部", "已封禁", "未封禁", "待获取"])
        self.banned_filter_combo.currentTextChanged.connect(self._on_banned_filter_changed)
        search_layout.addWidget(banned_label)
        search_layout.addWidget(self.banned_filter_combo)
        
        # 每页显示条数选择
        page_size_label = QLabel("每页显示:")
        self.page_size_combo = QComboBox()
        for size in self.page_sizes:
            self.page_size_combo.addItem(str(size))
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        search_layout.addWidget(page_size_label)
        search_layout.addWidget(self.page_size_combo)
        
        table_layout.addLayout(search_layout)
        
        # 创建账号表格 - 增加刷新日期列
        self.account_table = QTableWidget(0, 7)  # 修改为7列
        self.account_table.setHorizontalHeaderLabels(["状态", "邮箱", "用户名", "Steam账号", "备注", "封禁", "刷新日期"])
        
        # 设置列宽
        self.account_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(1, 5):
            self.account_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.account_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.account_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.account_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.account_table.setSelectionMode(QTableWidget.SingleSelection)
        self.account_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.account_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.account_table.customContextMenuRequested.connect(self._show_context_menu)
        # 添加双击事件
        self.account_table.doubleClicked.connect(self.on_table_double_clicked)
        self.account_table.setStyleSheet(Styles().currency_table_style)
        
        table_layout.addWidget(self.account_table)
        
        # 创建分页控制区域
        pagination_frame = QFrame()
        pagination_frame.setFrameShape(QFrame.StyledPanel)
        pagination_frame.setStyleSheet(Styles().log_pagination_frame_style)
        
        pagination_layout = QHBoxLayout(pagination_frame)
        pagination_layout.setContentsMargins(10, 5, 10, 5)
        
        # 页码信息
        self.page_info_label = QLabel("第1页 / 共1页 (总计0条记录)")
        
        # 每页显示条数选择
        page_size_label = QLabel("每页显示:")
        self.page_size_combo = QComboBox()
        for size in self.page_sizes:
            self.page_size_combo.addItem(str(size))
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        
        # 页码导航按钮
        self.first_page_btn = QPushButton("首页")
        self.first_page_btn.clicked.connect(self._goto_first_page)
        
        self.prev_page_btn = QPushButton("上一页")
        self.prev_page_btn.clicked.connect(self._goto_prev_page)
        
        self.next_page_btn = QPushButton("下一页")
        self.next_page_btn.clicked.connect(self._goto_next_page)
        
        self.last_page_btn = QPushButton("末页")
        self.last_page_btn.clicked.connect(self._goto_last_page)
        
        # 设置按钮样式
        for btn in [self.first_page_btn, self.prev_page_btn, self.next_page_btn, self.last_page_btn]:
            btn.setProperty('class', 'normal-button')
            btn.setFixedWidth(60)
        
        # 添加到布局
        pagination_layout.addWidget(page_size_label)
        pagination_layout.addWidget(self.page_size_combo)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.first_page_btn)
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addWidget(self.next_page_btn)
        pagination_layout.addWidget(self.last_page_btn)
        
        table_layout.addWidget(pagination_frame)
        
        self.main_layout.addWidget(table_frame)
    
    def _setup_account_menu(self):
        """设置账号右键菜单"""
        self.account_menu = QMenu(self)
        
        edit_action = self.account_menu.addAction("📄 编辑")
        edit_action.triggered.connect(self.edit_account)
        
        delete_action = self.account_menu.addAction("❌ 删除")
        delete_action.triggered.connect(self.remove_selected_account)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        row = self.account_table.currentRow()
        if (row >= 0):
            self.account_menu.exec_(self.account_table.viewport().mapToGlobal(pos))
    
    def import_from_clipboard(self):
        """从粘贴板导入账号"""
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            QMessageBox.warning(self, "导入错误", "粘贴板内容为空")
            return
        
        lines = text.strip().split('\n')
        imported_count = 0
        
        for line in lines:
            parts = line.split('----')
            if len(parts) >= 1:
                # 至少需要邮箱
                email = parts[0].strip()
                if not email:
                    continue
                    
                # 提取其他字段，如果不存在则设为空字符串
                password = parts[1].strip() if len(parts) > 1 else ""
                steam_account = parts[2].strip() if len(parts) > 2 else ""
                steam_password = parts[3].strip() if len(parts) > 3 else ""
                email_password = parts[4].strip() if len(parts) > 4 else ""
                note = parts[5].strip() if len(parts) > 5 else ""
                
                # 检查是否已存在相同邮箱的账号
                exists = False
                for acc in self.accounts:
                    if acc.get('email') == email:
                        exists = True
                        break
                
                if not exists:
                    self.accounts.append({
                        'status': "待刷新",  # 使用标准状态
                        'email': email,
                        'password': password,
                        'steam_account': steam_account,
                        'steam_password': steam_password,
                        'email_password': email_password,
                        'note': note
                    })
                    imported_count += 1
        
        if imported_count > 0:
            self.refresh_account_table()
            self.update_status_bar(f"已导入{imported_count}个账号")
            self.log_message(f"从粘贴板导入了{imported_count}个账号")
            
            # 保存配置
            if self.save_config:
                self.save_config()
        else:
            QMessageBox.information(self, "导入结果", "没有导入任何新账号")
    
    # 添加验证线程类
    class VerifyThread(QThread):
        """账号验证线程"""
        # 定义信号
        update_signal = Signal(str, str, str, str)  # email, status, username, poesessid
        finished_signal = Signal()
        
        def __init__(self, accounts, thread_count, logger):
            super().__init__()
            self.accounts = accounts
            self.thread_count = thread_count
            self.logger = logger
            self.running = True  # 添加控制变量
            self.browser_processes = []  # 保存浏览器进程引用
            
        def run(self):
            """线程执行函数"""
            from core.account_info import AccountVerifier
            import time
            from concurrent.futures import ThreadPoolExecutor
            
            # 创建验证器
            verifier = AccountVerifier(logger=self.logger)
            
            # 设置回调函数
            def update_callback(email, status, username=None, poesessid=None):
                # 检查线程是否应该停止
                if not self.running:
                    return
                # 发送信号到主线程
                self.update_signal.emit(email, status, username or "", poesessid or "")
            
            # 更新所有账号状态为"刷新中"
            for account in self.accounts:
                account['status'] = "刷新中"
                self.update_signal.emit(account.get('email', ''), "刷新中", "", "")
            
            # 使用修改后的验证函数，传入运行标志和浏览器进程列表
            result = verifier.verify_accounts(
                self.accounts, 
                self.thread_count, 
                update_callback, 
                running_flag=self,
                browser_processes=self.browser_processes
            )
            
            # 验证完成，发送完成信号
            self.finished_signal.emit()
            
        def stop(self):
            """安全停止线程"""
            self.running = False
            self.logger.info("正在停止验证线程并关闭浏览器...")
            
            # 关闭所有打开的浏览器进程
            for browser in self.browser_processes:
                try:
                    if browser and hasattr(browser, 'close'):
                        browser.close()
                except Exception as e:
                    self.logger.error(f"关闭浏览器失败: {str(e)}")

    def refresh_account_status(self):
        """刷新账号状态或停止刷新"""
        # 如果正在验证，则停止验证
        if self.is_verifying:
            self.stop_verification()
            return
            
        if not self.accounts:
            QMessageBox.information(self, "提示", "没有账号需要验证")
            return
            
        # 获取线程数
        thread_count = self.thread_count_input.value()
        
        # 设置验证状态
        self.is_verifying = True
        
        # 改变按钮文本和样式
        self.refresh_btn.setText("停止刷新")
        self.refresh_btn.setProperty('class', 'danger-button')
        self.refresh_btn.style().unpolish(self.refresh_btn)
        self.refresh_btn.style().polish(self.refresh_btn)
        
        # 更新状态栏
        self.update_status_bar("正在验证账号...")
        self.log_message(f"开始验证账号，使用{thread_count}个线程")
        
        # 创建日志记录器
        class Logger:
            def __init__(self, log_func):
                self.log_func = log_func
            def info(self, msg):
                self.log_func(msg, "INFO")
            def error(self, msg):
                self.log_func(msg, "ERROR")
            def warning(self, msg):
                self.log_func(msg, "WARNING")
                
        logger = Logger(self.log_message)
        
        # 创建并启动验证线程
        self.verify_thread = self.VerifyThread(self.accounts, thread_count, logger)
        
        # 连接信号
        self.verify_thread.update_signal.connect(self.update_callback)
        self.verify_thread.finished_signal.connect(self.on_verify_finished)
        
        # 启动线程
        self.verify_thread.start()

    def stop_verification(self):
        """停止验证过程"""
        if hasattr(self, 'verify_thread') and self.verify_thread.isRunning():
            # 使用安全的方法停止线程
            self.verify_thread.stop()
            
            # 等待一段时间，让线程有机会停止
            import time
            start_time = time.time()
            while self.verify_thread.isRunning() and time.time() - start_time < 8:  # 最多等待8秒
                time.sleep(0.2)
                QApplication.processEvents()  # 让UI保持响应
                
            # 如果线程仍在运行，则尝试终止它（这是不安全的，但作为最后手段）
            if self.verify_thread.isRunning():
                self.log_message("警告：验证线程无法正常停止，尝试强制终止")
                self.verify_thread.terminate()
                self.verify_thread.wait()
            
            # 还原按钮状态
            self.is_verifying = False
            self.refresh_btn.setText("刷新状态")
            self.refresh_btn.setProperty('class', 'normal-button')
            self.refresh_btn.style().unpolish(self.refresh_btn)
            self.refresh_btn.style().polish(self.refresh_btn)
            
            # 还原所有正在刷新状态的账号为"待刷新"
            for account in self.accounts:
                if account.get('status') == "刷新中":
                    account['status'] = "待刷新"
            
            # 刷新表格
            self.refresh_account_table()
            
            self.log_message("已停止账号验证")
            self.update_status_bar("账号验证已停止")

    def update_callback(self, email, status, username, poesessid=None):
        """验证回调函数（由线程信号触发）"""
        # 更新账号状态
        updated = False
        for account in self.accounts:
            if account.get('email') == email:
                account['status'] = status
                # 如果获取到了用户名，添加到账号信息中
                if username:
                    account['username'] = username
                    updated = True
                # 如果获取到了POESESSID，添加到账号信息中
                if poesessid:
                    account['poesessid'] = poesessid
                    updated = True
                # 更新刷新日期
                account['refresh_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
                updated = True
                break
        
        # 刷新表格
        self.refresh_account_table()
        
        # 每次更新账号信息时立即保存配置
        if updated and self.save_config:
            self.save_config()
            self.log_message(f"账号 {email} 信息已更新并保存")

    def on_verify_finished(self):
        """验证完成回调"""
        # 还原按钮状态
        self.is_verifying = False
        self.refresh_btn.setText("刷新状态")
        self.refresh_btn.setProperty('class', 'normal-button')
        self.refresh_btn.style().unpolish(self.refresh_btn)
        self.refresh_btn.style().polish(self.refresh_btn)
        
        self.update_status_bar("账号验证完成")
        self.log_message("账号验证完成")
        
        # 保存配置
        if self.save_config:
            self.save_config()
        
        # 保存配置
        if self.save_config:
            self.save_config()
    
    def _update_account_status(self, email, status):
        """更新账号状态（由验证器回调）"""
        # 查找对应账号并更新状态
        for account in self.accounts:
            if account.get('email') == email:
                account['status'] = status
                break
        
        # 刷新表格
        self.refresh_account_table()
        
        # 检查是否所有账号都已验证完成
        all_verified = True
        for account in self.accounts:
            if account.get('status') == '未验证':
                all_verified = False
                break
        
        if all_verified:
            self.refresh_btn.setEnabled(True)  # 启用刷新按钮
            self.update_status_bar("账号验证完成")
            self.log_message("所有账号验证完成")
            
            # 保存配置
            if self.save_config:
                self.save_config()

    def add_account(self):
        """添加账号（弹窗方式）"""
        # 创建账号编辑对话框
        dialog = AccountDialog(self)
        
        # 显示对话框并等待用户操作
        if dialog.exec():
            # 获取用户输入的账号信息
            account = dialog.get_account()
            
            if account:
                # 检查是否有重复邮箱
                email = account.get('email')
                for acc in self.accounts:
                    if acc.get('email') == email:
                        QMessageBox.warning(self, "输入错误", f"邮箱 '{email}' 已存在")
                        return
                
                # 添加必要的字段
                account.update({
                    'status': "待刷新",  # 使用标准状态
                    'banned': "待获取",  # 默认封禁状态为"待获取"
                    'refresh_date': ""   # 未刷新过的账号刷新日期为空
                })
                
                # 添加到账号列表
                self.accounts.append(account)
                self.update_status_bar(f"已添加账号: {email}")
                
                # 刷新表格
                self.refresh_account_table()
                
                # 保存配置
                if self.save_config:
                    self.save_config()
    
    def update_account(self):
        """更新账号（已废弃，使用edit_account代替）"""
        self.edit_account()
    
    def on_table_double_clicked(self, index):
        """处理表格双击事件"""
        row = index.row()
        if row >= 0:
            self.edit_account(row)
    
    def edit_account(self, row=None):
        """编辑选中的账号（弹窗方式）"""
        if row is None:
            row = self.account_table.currentRow()
            
        if row >= 0:
            # 获取当前页的账号索引
            start_idx = (self.current_page - 1) * self.page_size
            account_idx = start_idx + row
            
            if account_idx < len(self.filtered_accounts):
                account = self.filtered_accounts[account_idx]
                
                # 创建账号编辑对话框
                dialog = AccountDialog(self, account, f"编辑账号 - {account.get('email', '')}")
                
                # 显示对话框并等待用户操作
                if dialog.exec():
                    # 获取用户修改后的账号信息
                    updated_account = dialog.get_account()
                    
                    if updated_account:
                        # 检查是否有重复邮箱（排除当前账号）
                        email = updated_account.get('email')
                        for i, acc in enumerate(self.accounts):
                            if acc.get('email') == email and acc != account:
                                QMessageBox.warning(self, "输入错误", f"邮箱 '{email}' 已存在")
                                return
                        
                        # 更新账号信息
                        # 找到原始账号在accounts列表中的位置
                        for i, acc in enumerate(self.accounts):
                            if acc == account:
                                self.accounts[i].update(updated_account)
                                self.update_status_bar(f"已更新账号: {email}")
                                break
                        
                        # 刷新表格
                        self.refresh_account_table()
                        
                        # 保存配置
                        if self.save_config:
                            self.save_config()
    
    def remove_selected_account(self):
        """删除选中的账号"""
        row = self.account_table.currentRow()
        if row >= 0:
            account = self.accounts[row]
            if ask_yes_no("确认删除", f"确定要删除账号 '{account.get('email', '')}' 吗？"):
                del self.accounts[row]
                self.refresh_account_table()
                self.update_status_bar(f"已删除账号: {account.get('email', '')}")
                
                # 如果正在编辑该账号，清空表单
                if hasattr(self, 'editing_index') and self.editing_index == row:
                    self.clear_form()
                
                # 保存配置
                if self.save_config:
                    self.save_config()
    
    def _on_banned_filter_changed(self, filter_value):
        """处理封禁状态筛选变化"""
        self.banned_filter = filter_value
        self.current_page = 1  # 重置到第一页
        self._filter_accounts()
        self.refresh_account_table()
    
    def _filter_accounts(self):
        """根据搜索文本和封禁状态过滤账号列表"""
        # 首先使用搜索文本过滤
        if not self.search_text:
            self.filtered_accounts = self.accounts.copy()
        else:
            search_text = self.search_text.lower()
            self.filtered_accounts = [account for account in self.accounts
                                    if search_text in account.get('email', '').lower() or
                                       search_text in account.get('username', '').lower() or
                                       search_text in account.get('steam_account', '').lower() or
                                       search_text in account.get('note', '').lower()]
        
        # 然后根据封禁状态进一步过滤
        if self.banned_filter != "全部":
            filtered_by_banned = []
            for account in self.filtered_accounts:
                banned_status = account.get('banned')
                
                if self.banned_filter == "已封禁" and banned_status == 1:
                    filtered_by_banned.append(account)
                elif self.banned_filter == "未封禁" and banned_status == 0:
                    filtered_by_banned.append(account)
                elif self.banned_filter == "待获取" and banned_status != 0 and banned_status != 1:
                    filtered_by_banned.append(account)
            
            self.filtered_accounts = filtered_by_banned
    
    def _update_pagination_controls(self):
        """更新分页控制器状态"""
        total_records = len(self.filtered_accounts)
        total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
        self.page_info_label.setText(f"第{self.current_page}页 / 共{total_pages}页 (总计{total_records}条记录)")
        
        # 更新按钮状态
        self.first_page_btn.setEnabled(self.current_page > 1)
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < total_pages)
        self.last_page_btn.setEnabled(self.current_page < total_pages)
    
    def _on_search_text_changed(self, text):
        """处理搜索文本变化"""
        self.search_text = text
        self.current_page = 1  # 重置到第一页
        self._filter_accounts()
        self.refresh_account_table()
    
    def _on_page_size_changed(self, text):
        """处理每页显示条数变化"""
        try:
            self.page_size = int(text)
            self.current_page = 1  # 重置到第一页
            self.refresh_account_table()
            self.update_status_bar(f"每页显示条数已更改为 {self.page_size}")
        except ValueError:
            pass
    
    def _goto_first_page(self):
        """跳转到第一页"""
        if self.current_page != 1:
            self.current_page = 1
            self.refresh_account_table()
    
    def _goto_prev_page(self):
        """跳转到上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_account_table()
    
    def _goto_next_page(self):
        """跳转到下一页"""
        total_pages = max(1, (len(self.filtered_accounts) + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.refresh_account_table()
    
    def _goto_last_page(self):
        """跳转到最后一页"""
        total_pages = max(1, (len(self.filtered_accounts) + self.page_size - 1) // self.page_size)
        if self.current_page != total_pages:
            self.current_page = total_pages
            self.refresh_account_table()
    
    def refresh_account_table(self):
        """刷新账号表格"""
        # 先过滤账号
        self._filter_accounts()
        
        # 计算当前页的数据范围
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        current_page_accounts = self.filtered_accounts[start_idx:end_idx]
        
        # 更新表格
        self.account_table.setRowCount(0)
        
        for account in current_page_accounts:
            row = self.account_table.rowCount()
            self.account_table.insertRow(row)
            
            # 显示状态 - 统一使用四种标准状态
            status = account.get('status', "待刷新")
            
            # 确保状态只显示四种标准状态之一
            if "成功" in status or "已更新" in status:
                status = "已刷新"
            elif "失败" in status:
                status = "失败"
            elif "刷新中" in status:
                status = "刷新中"
            elif status not in ["待刷新", "刷新中", "已刷新", "失败"]:
                status = "待刷新"
                
            # 更新状态到账号数据
            account['status'] = status
            self.account_table.setItem(row, 0, QTableWidgetItem(status))
            
            # 其他基本信息
            self.account_table.setItem(row, 1, QTableWidgetItem(account.get('email', '')))
            self.account_table.setItem(row, 2, QTableWidgetItem(account.get('username', '')))
            self.account_table.setItem(row, 3, QTableWidgetItem(account.get('steam_account', '')))
            self.account_table.setItem(row, 4, QTableWidgetItem(account.get('note', '')))
            
            # 显示封禁状态 - 标准化显示
            banned_status = account.get('banned')
            if banned_status == 1:
                banned_text = "是"
            elif banned_status == 0:
                banned_text = "否"
            else:
                banned_text = "待获取"
            self.account_table.setItem(row, 5, QTableWidgetItem(banned_text))
            
            # 显示刷新日期
            self.account_table.setItem(row, 6, QTableWidgetItem(account.get('refresh_date', '')))
            
            # 根据状态设置行样式
            if status == "已刷新":
                # 成功状态显示绿色
                row_color = QColor(200, 255, 200)  # 浅绿色
            elif status == "失败":
                # 失败状态显示红色
                row_color = QColor(255, 200, 200)  # 浅红色
            elif status == "刷新中":
                # 刷新中状态显示蓝色
                row_color = QColor(200, 200, 255)  # 浅蓝色
            else:
                # 默认状态不设置特殊颜色
                row_color = None
            
            # 如果账号被封禁，设置行背景色为浅红色，覆盖其他颜色
            if banned_text == "是":
                row_color = QColor(255, 200, 200)  # 浅红色
                
            # 应用颜色
            if row_color:
                for col in range(self.account_table.columnCount()):
                    item = self.account_table.item(row, col)
                    if item:
                        item.setBackground(row_color)
        
        # 更新分页控制器
        self._update_pagination_controls()
    
    def set_config_data(self, config_data):
        """设置配置数据"""
        self.accounts = config_data.get('accounts', [])
        
        # 设置线程数
        if hasattr(self, 'thread_count_input'):
            self.thread_count_input.setValue(config_data.get('thread_count', 1))
        
        # 还原筛选设置
        if hasattr(self, 'banned_filter_combo') and 'banned_filter' in config_data:
            index = self.banned_filter_combo.findText(config_data['banned_filter'])
            if index >= 0:
                self.banned_filter_combo.setCurrentIndex(index)
                self.banned_filter = config_data['banned_filter']
            
        self.refresh_account_table()
    
    def get_config_data(self):
        """获取配置数据"""
        return {
            'accounts': self.accounts,
            'thread_count': self.thread_count_input.value(),
            'banned_filter': self.banned_filter
        }
        
    def on_thread_count_changed(self):
        """处理线程数变化"""
        if self.save_config:
            self.save_config()