from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, 
                                    QLabel, QLineEdit, QPushButton, QSpinBox,
                                    QListWidget, QMenu, QTextEdit, QFileDialog,
                                    QComboBox)
from PySide6.QtCore import Qt, Signal
from ..utils import LoggingMixin, ConfigMixin, show_message, ask_yes_no
from ..widgets.dialog import MessageDialog, InputDialog
from ..widgets.switch import Switch
import os

class BasicConfigPage(QWidget, LoggingMixin, ConfigMixin):
    """基本配置页面"""
    def __init__(self, parent, log_callback, status_callback, callback_save=None):
        super().__init__(parent)
        LoggingMixin.__init__(self, log_callback, status_callback)
        self.init_config()  # 初始化配置对象
        self.save_config = callback_save
        self.main_window = None  # 用于存储MainWindow引用
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        # 创建各组件
        self._create_game_frame()
        self._create_file_frame()
        self._create_settings_frame()
        self._create_keywords_frame()
        self._setup_keyword_menu()
        
    def _create_game_frame(self):
        """创建游戏窗口配置区域"""
        game_frame = QFrame()
        game_frame.setProperty('class', 'card-frame')
        game_layout = QHBoxLayout(game_frame)
        game_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("游戏窗口配置")
        title_label.setProperty('class', 'card-title')
        
        name_label = QLabel("窗口名称:")
        self.game_entry = QLineEdit()
        self.game_entry.setText("Path of Exile")
        self.game_entry.textChanged.connect(self._on_settings_change)
        self.switch_btn = QPushButton("切换窗口")
        self.switch_btn.setProperty('class', 'normal-button')
        self.switch_btn.clicked.connect(self._switch_to_game)
        
        game_layout.addWidget(name_label)
        game_layout.addWidget(self.game_entry, 1)
        game_layout.addWidget(self.switch_btn)
        
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(game_frame)
        
    def _create_file_frame(self):
        """创建文件配置区域"""
        file_frame = QFrame()
        file_frame.setProperty('class', 'card-frame')
        file_layout = QHBoxLayout(file_frame)
        file_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("日志文件配置")
        title_label.setProperty('class', 'card-title')
        
        path_label = QLabel("日志路径:")
        self.file_entry = QLineEdit()
        self.file_entry.textChanged.connect(self._on_settings_change)
        self.browse_btn = QPushButton("📂 浏览")
        self.browse_btn.setProperty('class', 'normal-button')
        self.browse_btn.clicked.connect(self.select_file)
        
        file_layout.addWidget(path_label)
        file_layout.addWidget(self.file_entry, 1)
        file_layout.addWidget(self.browse_btn)
        
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(file_frame)
        
    def _create_settings_frame(self):
        """创建监控设置区域"""
        settings_frame = QFrame()
        settings_frame.setProperty('class', 'card-frame')
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("监控设置")
        title_label.setProperty('class', 'card-title')
        
        # 间隔设置行
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("检测间隔(ms):"))
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(500, 5000)
        self.interval_spin.setSingleStep(100)
        self.interval_spin.setValue(1000)
        self.interval_spin.valueChanged.connect(self._on_settings_change)
        interval_layout.addWidget(self.interval_spin)
        
        interval_layout.addWidget(QLabel("推送间隔(ms):"))
        self.push_interval_entry = QSpinBox()
        self.push_interval_entry.setRange(0, 99999)
        self.push_interval_entry.setValue(0)
        self.push_interval_entry.valueChanged.connect(self._on_settings_change)
        interval_layout.addWidget(self.push_interval_entry)
        interval_layout.addStretch()
        
        # 置顶设置行
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("置顶本程序窗口:"))
        
        self.top_switch = Switch()
        self.top_switch.stateChanged.connect(self._on_top_switch_change)
        top_layout.addWidget(self.top_switch)
        top_layout.addStretch()
        
        settings_layout.addLayout(interval_layout)
        settings_layout.addLayout(top_layout)
        
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(settings_frame)
        
    def _create_keywords_frame(self):
        """创建关键词管理区域"""
        keywords_frame = QFrame()
        keywords_frame.setProperty('class', 'card-frame')
        keywords_layout = QVBoxLayout(keywords_frame)
        keywords_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("关键词管理")
        title_label.setProperty('class', 'card-title')
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["消息模式", "交易模式"])
        input_layout.addWidget(self.mode_combo)
        
        self.keyword_entry = QLineEdit()
        self.keyword_entry.returnPressed.connect(self.add_keyword)
        input_layout.addWidget(self.keyword_entry)
        
        add_btn = QPushButton("➕ 添加")
        add_btn.setProperty('class', 'normal-button')
        add_btn.clicked.connect(self.add_keyword)
        input_layout.addWidget(add_btn)
        
        clear_btn = QPushButton("🔄 清空")
        clear_btn.setProperty('class', 'danger-button')
        clear_btn.clicked.connect(self.clear_keywords)
        input_layout.addWidget(clear_btn)
        
        help_btn = QPushButton("❓ 帮助")
        help_btn.setProperty('class', 'control-save-button')
        help_btn.clicked.connect(self.show_help)
        input_layout.addWidget(help_btn)
        
        keywords_layout.addLayout(input_layout)
        
        # 关键词列表
        self.keyword_list = QListWidget()
        self.keyword_list.itemSelectionChanged.connect(self.on_keyword_select)
        self.keyword_list.itemDoubleClicked.connect(self.edit_keyword)
        self.keyword_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.keyword_list.customContextMenuRequested.connect(self.show_keyword_menu)
        keywords_layout.addWidget(self.keyword_list)
        
        # 测试区域
        test_frame = QFrame()
        test_frame.setProperty('class', 'card-frame')
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(10, 10, 10, 10)
        
        test_input_layout = QHBoxLayout()
        self.test_text = QTextEdit()
        self.test_text.setFixedHeight(50)
        test_input_layout.addWidget(self.test_text)
        
        test_btn = QPushButton("测试")
        test_btn.setProperty('class', 'normal-button')
        test_btn.clicked.connect(self.test_keyword)
        test_input_layout.addWidget(test_btn)
        
        test_layout.addLayout(test_input_layout)
        
        self.test_result = QTextEdit()
        self.test_result.setReadOnly(True)
        self.test_result.setFixedHeight(100)
        test_layout.addWidget(self.test_result)
        
        keywords_layout.addWidget(test_frame)
        
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(keywords_frame)
        
    def _setup_keyword_menu(self):
        """设置关键词右键菜单"""
        self.keyword_menu = QMenu(self)
        
        edit_action = self.keyword_menu.addAction("📄 编辑")
        edit_action.triggered.connect(self.edit_keyword)
        
        delete_action = self.keyword_menu.addAction("❌ 删除")
        delete_action.triggered.connect(self.remove_selected_keyword)
        
        self.keyword_menu.addSeparator()
        
        copy_action = self.keyword_menu.addAction("📋 复制")
        copy_action.triggered.connect(self.copy_keyword)
                                    
    def show_help(self):
        """显示帮助信息"""
        help_content = """消息模式：
填写 来自 则日志中匹配到包含 来自 的消息就会推送，支持多关键词匹配用"|"进行分隔，如：来自|我想購買 则只会匹配日志中同时包含这两个关键词的行进行推送

交易模式：
示例 *来自 {@user}: 你好，我想購買 {@item} 標價 {@price} {@currency} 在 {@mode} (倉庫頁 "{@tab}"; 位置: {@p1} {@p1_num}, {@p2} {@p2_num})
*代表会变化的任意内容（因为时间和客户端ID会变化）
@user 玩家昵称
@item 装备名称
@price 通货数量
@currency 通货单位
@mode 游戏模式
@tab 仓库页
@p1 位置1方向
@p1_num 位置1坐标
@p2 位置2方向
@p2_num 位置2坐标"""
        
        dialog = MessageDialog(self, "关键词帮助", help_content)
        dialog.show()

    def add_keyword(self):
        """添加关键词"""
        keyword = self.keyword_entry.text().strip()
        if not keyword:
            self.log_message("无法添加空关键词", "WARN")
            return
            
        mode = self.mode_combo.currentText()
        formatted_keyword = f"[{mode}] {keyword}"
            
        # 检查是否已存在
        for i in range(self.keyword_list.count()):
            if self.keyword_list.item(i).text() == formatted_keyword:
                self.log_message(f"重复关键词: {keyword}", "WARN")
                return
            
        self.keyword_list.addItem(formatted_keyword)
        self.keyword_entry.clear()
        self.log_message(f"已添加关键词: {formatted_keyword}")
        if self.save_config:
            self.save_config()

    def test_keyword(self):
        """测试关键词"""
        current_item = self.keyword_list.currentItem()
        if not current_item:
            show_message("提示", "请先选择要测试的关键词", "warning")
            return
            
        keyword = current_item.text()
        test_text = self.test_text.toPlainText()
        
        if not test_text:
            show_message("提示", "请输入要测试的文本", "warning")
            return
            
        # 从关键词中提取模式
        if "[消息模式]" in keyword:
            mode = "消息模式"
            pattern = keyword.replace("[消息模式]", "").strip()
        else:
            mode = "交易模式"
            pattern = keyword.replace("[交易模式]", "").strip()
            
        self.test_result.clear()
        
        if mode == "消息模式":
            # 消息模式测试
            keywords = pattern.split('|')
            if all(kw.strip() in test_text for kw in keywords):
                self.test_result.setText(f"匹配成功：{pattern}")
            else:
                self.test_result.setText("[消息模式]不匹配")
        else:
            # 交易模式测试
            # 将模板中的*替换为通配符
            template = pattern.replace('*', '.*?')
            # 替换占位符为捕获组
            placeholders = [
                '@user', '@item', '@price', '@currency', '@mode',
                '@tab', '@p1', '@p1_num', '@p2', '@p2_num'
            ]
            template = template.replace('(', '\(')
            template = template.replace(')', '\)')
            for ph in placeholders:
                template = template.replace('{' + ph + '}', '(.+?)')
           
            import re
            match = re.match(template, test_text)
            if match:
                result = "匹配成功，解析结果：\n"
                for i, ph in enumerate(placeholders, 1):
                    if i <= len(match.groups()):
                        result += f"{ph[1:]}: {match.group(i)}\n"
                self.test_result.setText(result)
            else:
                self.test_result.setText("[交易模式]不匹配")
        
    def edit_keyword(self):
        """编辑选中的关键词"""
        current_item = self.keyword_list.currentItem()
        if not current_item:
            return
            
        current_keyword = current_item.text()
        # 从关键词中提取模式和内容
        if "[消息模式]" in current_keyword:
            mode = "消息模式"
            pattern = current_keyword.replace("[消息模式]", "").strip()
        else:
            mode = "交易模式"
            pattern = current_keyword.replace("[交易模式]", "").strip()
            
        def save_edit(new_pattern):
            new_keyword = f"[{mode}] {new_pattern}"
            if new_pattern and new_keyword != current_keyword:
                # 检查是否已存在
                exists = False
                for i in range(self.keyword_list.count()):
                    if i != self.keyword_list.currentRow() and self.keyword_list.item(i).text() == new_keyword:
                        exists = True
                        break
                        
                if not exists:
                    current_item.setText(new_keyword)
                    self.log_message(f"关键词已更新: {current_keyword} → {new_keyword}")
                    if self.save_config:
                        self.save_config()
                else:
                    show_message("提示", "关键词已存在", "warning")
                    
        # 使用InputDialog进行编辑
        dialog = InputDialog(self, "编辑关键词", "请输入新的关键词：", pattern, save_edit)
        dialog.show()  # 确保对话框显示

    def remove_selected_keyword(self):
        """删除选中的关键词"""
        current_item = self.keyword_list.currentItem()
        if current_item:
            keyword = current_item.text()
            self.keyword_list.takeItem(self.keyword_list.row(current_item))
            self.log_message(f"已移除关键词: {keyword}")
            if self.save_config:
                self.save_config()
            
    def clear_keywords(self):
        """清空关键词"""
        if ask_yes_no("确认清空", "确定要清空所有关键词吗？\n此操作无法撤销"):
            self.keyword_list.clear()
            self.log_message("已清空关键词列表")
            self.update_status("✨ 已清空关键词列表")
            if self.save_config:
                self.save_config()
            
    def show_keyword_menu(self, pos):
        """显示关键词右键菜单"""
        if self.keyword_list.count() > 0 and self.keyword_list.currentItem():
            self.keyword_menu.exec_(self.keyword_list.mapToGlobal(pos))

    def copy_keyword(self):
        """复制选中的关键词到剪贴板"""
        current_item = self.keyword_list.currentItem()
        if current_item:
            from PySide6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(current_item.text())
            self.update_status(f"已复制: {current_item.text()}")
            
    def select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择日志文件")
        if file_path:
            self.file_entry.setText(file_path)
            self.log_message(f"已选择日志文件: {file_path}")
            if self.save_config:
                self.save_config()
                
    def validate_config(self):
        """验证配置数据"""
        data = self.get_config_data()
        
        if not data.get('log_path'):
            return False, "请选择日志文件"
            
        if not data.get('keywords', []):
            return False, "请至少添加一个关键词"
            
        interval = data.get('interval', 0)
        if interval < 500 or interval > 5000:
            return False, "检测间隔必须在500-5000毫秒之间"
            
        push_interval = data.get('push_interval', 0)
        if push_interval < 0:
            return False, "推送间隔不能为负数"
            
        return True, None

    def _on_settings_change(self):
        """处理设置值变化"""
        if self.save_config:
            self.save_config()
            
    def _switch_to_game(self):
        """切换到游戏窗口"""
        from ..utils import switch_to_window
        window_name = self.game_entry.text().strip()
        if switch_to_window(window_name):
            self.log_message(f"已切换到游戏窗口: {window_name}")
        else:
            self.log_message(f"切换窗口失败: {window_name}", "ERROR")
            
    def get_config_data(self):
        """获取配置数据"""
        keywords = []
        for i in range(self.keyword_list.count()):
            kw = self.keyword_list.item(i).text()
            if "[消息模式]" in kw:
                mode = "消息模式"
                pattern = kw.replace("[消息模式]", "").strip()
            else:
                mode = "交易模式"
                pattern = kw.replace("[交易模式]", "").strip()
                
            keywords.append({
                "mode": mode,
                "pattern": pattern
            })
        
        # 获取当前配置以保留其他设置
        current_config = self.config.config if hasattr(self, 'config') else {}
        
        # 创建新配置，保留现有的wxpusher和email配置
        new_config = {
            'game_window': self.game_entry.text(),
            'log_path': self.file_entry.text(),
            'interval': self.interval_spin.value(),
            'push_interval': self.push_interval_entry.value(),
            'keywords': keywords,
            'always_on_top': self.top_switch.isChecked(),
            'wxpusher': current_config.get('wxpusher', {
                'enabled': False,
                'app_token': '',
                'uid': ''
            }),
            'email': current_config.get('email', {
                'enabled': False,
                'smtp_server': '',
                'smtp_port': '',
                'sender_email': '',
                'email_password': '',
                'receiver_email': ''
            })
        }
        
        return new_config
        
    def set_config_data(self, data):
        """设置配置数据"""
        self.game_entry.setText(data.get('game_window', 'Path of Exile'))
        
        # 设置置顶开关状态并触发置顶效果
        always_on_top = data.get('always_on_top', False)
        self.top_switch.setChecked(always_on_top)
        # 设置置顶状态
        if self.main_window:
            self.main_window.set_always_on_top(always_on_top)
        
        self.file_entry.setText(data.get('log_path', ''))
        self.interval_spin.setValue(data.get('interval', 1000))
        self.push_interval_entry.setValue(data.get('push_interval', 0))
        
        self.keyword_list.clear()
        for kw in data.get('keywords', []):
            # 兼容旧版数据格式
            if isinstance(kw, str):
                self.keyword_list.addItem(f"[消息模式] {kw}")
            else:
                mode = kw.get('mode', '消息模式')
                pattern = kw.get('pattern', '')
                self.keyword_list.addItem(f"[{mode}] {pattern}")
                
    def on_keyword_select(self):
        """处理关键词选择变化"""
        pass
    
    def set_main_window(self, main_window):
        """设置MainWindow引用"""
        self.main_window = main_window

    def _on_top_switch_change(self, checked):
        """处理置顶开关状态变化"""
        if self.main_window:
            self.main_window.set_always_on_top(checked)
        if self.save_config:
            self.save_config()
