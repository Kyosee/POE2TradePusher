from PySide6.QtWidgets import (QMainWindow, QWidget, QPushButton, QLabel, 
                                    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox)
import traceback
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from .styles import Styles
from .tray_icon import TrayIcon
from .pages import BasicConfigPage, PushManagePage, LogPage, CurrencyConfigPage, StatsPage
from .pages.stash_test_page import StashTestPage
from .pages.position_test_page import PositionTestPage
from .pages.command_test_page import CommandTestPage
from .pages.auto_trade_page import AutoTradePage
from core.config import Config
from core.log_monitor import LogMonitor
from core.auto_trade import AutoTrade, TradeConfig
from .widgets.toast import show_toast, Toast
from utils.currency_fetcher import CurrencyFetcher

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        self.setWindowTitle("POE2 Trade Pusher")
        self.resize(1000, 800)
        self.always_on_top = False
        
        # 设置应用图标
        self.setWindowIcon(QIcon("assets/icon.png"))
        
        # 初始化组件
        self.styles = Styles()
        self.config = Config()
        self.tray_icon = TrayIcon(icon_path="assets/icon.png")
        
        # 初始化状态
        self.is_minimized = False
        self.monitoring = False
        self.current_menu = None
        self.current_submenu = None  # 当前选中的子菜单
        
        # 提前初始化对话框，避免首次弹窗卡顿
        self._pre_init_dialogs()
        
        # 创建中央窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建界面
        self.create_widgets()
        self.setup_layout()
        self.setup_bindings()
        
        # 初始化托盘
        self.setup_tray()
        
        # 加载配置
        self.load_config()
        
        # 初始化监控器
        self.monitor = None
        
        # 初始化自动交易
        self.auto_trade = AutoTrade()
        
        # 添加初始提示信息
        self.log_message("应用程序已启动，等待配置...", "INFO")
        self.log_message("请配置日志路径和至少一种推送方式", "INFO")
        
        # 默认显示基本配置页面
        self._show_basic_config()
        
    def _pre_init_dialogs(self):
        """预先初始化对话框组件，避免首次显示时卡顿"""
        # 创建并隐藏一个消息框，触发Qt组件的预加载
        self.message_box = QMessageBox(self)
        self.message_box.setWindowTitle("初始化")
        self.message_box.setText("正在初始化组件...")
        self.message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        # 不显示对话框，只创建实例
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建左侧菜单区域
        self.menu_frame = QFrame()
        self.menu_frame.setFixedWidth(200)
        self.menu_frame.setProperty('class', 'menu-frame')
        
        # 创建菜单布局
        self.menu_layout = QVBoxLayout(self.menu_frame)
        self.menu_layout.setContentsMargins(1, 1, 1, 1)
        self.menu_layout.setSpacing(1)
        
        # 创建菜单按钮
        self.menu_buttons = []
        self.submenu_frames = {}
        
        menu_items = [
            ('基本配置', self._show_basic_config, []),
            ('推送配置', self._show_push_manage, []),
            ('通货配置', self._show_currency_config, []),
            ('数据统计', self._show_stats, []),
            ('自动交易', self._show_auto_trade, []),
            ('触发日志', self._show_log, []),
            ('识别测试', None, [
                ('仓库测试', self._show_stash_recognition),
                ('定位测试', self._show_grid_recognition),
                ('命令测试', self._show_command_test)
            ])
        ]
        
        for text, command, submenus in menu_items:
            btn = QPushButton(text)
            btn.setProperty('class', 'menu-button')
            if command:
                btn.clicked.connect(command)
            else:
                # 修复二级菜单显示问题，使用functools.partial确保正确传递参数
                from functools import partial
                btn.clicked.connect(partial(self._toggle_submenu, text))
            
            self.menu_layout.addWidget(btn)
            self.menu_buttons.append(btn)
            
            # 如果有子菜单，创建子菜单框架
            if submenus:
                submenu_frame = QFrame()
                submenu_frame.setProperty('class', 'submenu-frame')
                submenu_layout = QVBoxLayout(submenu_frame)
                submenu_layout.setContentsMargins(0, 0, 0, 0)
                submenu_layout.setSpacing(1)
                
                self.submenu_frames[text] = {
                    'frame': submenu_frame,
                    'visible': False,
                    'buttons': []
                }
                
                # 创建子菜单按钮
                for sub_text, sub_command in submenus:
                    sub_btn = QPushButton('  ' + sub_text)
                    sub_btn.setProperty('class', 'submenu-button')
                    sub_btn.clicked.connect(sub_command)
                    submenu_layout.addWidget(sub_btn)
                    self.submenu_frames[text]['buttons'].append(sub_btn)
                
                submenu_frame.hide()
                self.menu_layout.addWidget(submenu_frame)
        
        # 添加弹性空间
        self.menu_layout.addStretch()
        
        # 创建控制按钮区域
        control_frame = QFrame()
        control_frame.setProperty('class', 'control-frame')
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(1, 1, 1, 1)
        control_layout.setSpacing(1)
        
        # 启动按钮
        self.start_btn = QPushButton("▶ 开始监控")
        self.start_btn.setProperty('class', 'control-button')
        self.start_btn.clicked.connect(self.toggle_monitor)
        control_layout.addWidget(self.start_btn)
        
        # 保存按钮
        self.save_btn = QPushButton("💾 保存设置")
        self.save_btn.setProperty('class', 'control-save-button')
        self.save_btn.clicked.connect(self.save_config)
        control_layout.addWidget(self.save_btn)
        
        self.menu_layout.addWidget(control_frame)
        
        # 创建右侧内容区域
        self.content_frame = QFrame()
        self.content_frame.setProperty('class', 'content-container')  # 更改样式类
        
        # 创建内容布局
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # 创建各功能页面
        self.basic_config_page = BasicConfigPage(self.content_frame, self.log_message, 
                                               self.update_status_bar, self.save_config)
        self.basic_config_page.setProperty('class', 'page-container')  # 添加样式类
        self.basic_config_page.set_main_window(self)
        self.content_layout.addWidget(self.basic_config_page)
        
        # 其他页面也设置page-container样式
        
        self.push_manage_page = PushManagePage(self.content_frame, self.log_message, 
                                             self.update_status_bar)
        self.push_manage_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.push_manage_page)
        
        self.currency_config_page = CurrencyConfigPage(self.content_frame, self.log_message, 
                                                     self.update_status_bar, self.save_config)
        self.currency_config_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.currency_config_page)
        
        self.log_page = LogPage(self.content_frame, self.log_message, 
                              self.update_status_bar)
        self.log_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.log_page)
        
        self.stats_page = StatsPage(self.content_frame, self.log_message,
                                  self.update_status_bar, self.save_config)
        self.stats_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.stats_page)
        
        self.stash_recognition_page = StashTestPage(self.content_frame, self.log_message,
                                                  self.update_status_bar)
        self.stash_recognition_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.stash_recognition_page)
        
        self.grid_recognition_page = PositionTestPage(self.content_frame, self.log_message,
                                                    self.update_status_bar)
        self.grid_recognition_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.grid_recognition_page)
        
        self.command_test_page = CommandTestPage(self.content_frame, self.log_message)
        self.command_test_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.command_test_page)
        
        self.auto_trade_page = AutoTradePage(self.content_frame)
        self.auto_trade_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.auto_trade_page)
        
        # 默认隐藏所有页面
        self._hide_all_pages()
        
        # 创建状态栏
        status_layout = QHBoxLayout()
        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        
        self.status_bar = QLabel("就绪")
        self.status_bar.setProperty('class', 'status-label')
        status_layout.addWidget(self.status_bar)
        
        status_layout.addStretch()
        
        self.price_label = QLabel("神圣石-等待获取...")
        self.price_label.setProperty('class', 'status-label')
        status_layout.addWidget(self.price_label)
        
        self.statusBar().addWidget(status_widget)
        
        # 初始化通货价格获取器
        self.currency_fetcher = CurrencyFetcher()
        self.currency_fetcher.price_updated.connect(self._update_currency_price)
        # 立即获取一次价格
        self.currency_fetcher.fetch_price()
    
    def setup_layout(self):
        """设置界面布局"""
        self.main_layout.addWidget(self.menu_frame)
        self.main_layout.addWidget(self.content_frame)
        
    def update_status_bar(self, text):
        """更新状态栏"""
        self.status_bar.setText(text)
        
    def _show_basic_config(self):
        """显示基本配置页面"""
        self._hide_all_pages()
        self.basic_config_page.show()
        self._update_menu_state(0)
        
    # 已移除流程配置页面
                
    def _show_push_manage(self):
        """显示推送管理页面"""
        self._hide_all_pages()
        self.push_manage_page.show()
        self._update_menu_state(1)

    def _show_currency_config(self):
        """显示通货配置页面"""
        self._hide_all_pages()
        self.currency_config_page.show()
        self._update_menu_state(2)
        
    def _show_stats(self):
        """显示数据统计页面"""
        self._hide_all_pages()
        self.stats_page.show()
        self._update_menu_state(3)
        
    def _show_log(self):
        """显示日志页面"""
        self._hide_all_pages()
        self.log_page.show()
        self._update_menu_state(5)
        
    def _show_stash_recognition(self):
        """显示仓库识别页面"""
        self._hide_all_pages()
        self.stash_recognition_page.show()
        self._update_menu_state(6, '仓库测试')
                
    def _show_command_test(self):
        """显示命令测试页面"""
        self._hide_all_pages()
        self.command_test_page.show()
        self._update_menu_state(6, '命令测试')
        
    def _show_grid_recognition(self):
        """显示仓位识别页面"""
        self._hide_all_pages()
        self.grid_recognition_page.show()
        self._update_menu_state(6, '定位测试')
    
    def _show_auto_trade(self):
        """显示自动交易页面"""
        self._hide_all_pages()
        self.auto_trade_page.show()
        self._update_menu_state(4)
        
    def _hide_all_pages(self):
        """隐藏所有页面"""
        self.basic_config_page.hide()
        self.currency_config_page.hide()
        self.push_manage_page.hide()
        self.stats_page.hide()
        self.log_page.hide()
        self.stash_recognition_page.hide()
        self.grid_recognition_page.hide()
        self.command_test_page.hide()
        self.auto_trade_page.hide()
        
    def _toggle_submenu(self, menu_text):
        """切换子菜单的显示状态"""
        if menu_text in self.submenu_frames:
            submenu_info = self.submenu_frames[menu_text]
            submenu_frame = submenu_info['frame']
            
            submenu_info['visible'] = not submenu_info['visible']
            if submenu_info['visible']:
                submenu_frame.show()
            else:
                submenu_frame.hide()
                
    def _update_menu_state(self, selected_index, selected_submenu=None):
        """更新菜单按钮状态"""
        for i, btn in enumerate(self.menu_buttons):
            menu_text = btn.text()
            btn.setProperty('selected', i == selected_index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
            # 更新二级菜单状态
            if menu_text in self.submenu_frames:
                submenu_info = self.submenu_frames[menu_text]
                for sub_btn in submenu_info['buttons']:
                    sub_text = sub_btn.text().strip()
                    is_selected = (i == selected_index and sub_text == selected_submenu)
                    sub_btn.setProperty('selected', is_selected)
                    sub_btn.style().unpolish(sub_btn)
                    sub_btn.style().polish(sub_btn)
                    
                    if is_selected:
                        btn.setProperty('selected', True)
                        btn.style().unpolish(btn)
                        btn.style().polish(btn)
        
        # 更新当前选中状态
        self.current_menu = selected_index
        self.current_submenu = selected_submenu
        
    def setup_bindings(self):
        """设置事件绑定"""
        pass
        
    def setup_tray(self):
        """初始化系统托盘"""
        # 设置回调函数
        self.tray_icon.set_callback('on_toggle', self.toggle_window)
        self.tray_icon.set_callback('on_start', lambda: self.toggle_monitor() if not self.monitoring else None)
        self.tray_icon.set_callback('on_stop', lambda: self.toggle_monitor() if self.monitoring else None)
        self.tray_icon.set_callback('on_quit', self.quit_app)
        
        # 初始化托盘
        success, msg = self.tray_icon.setup()
        if not success:
            self.log_message(msg, "ERROR")
    
    def load_config(self):
        """加载配置"""
        success, msg = self.config.load()
        self.log_page.append_log(msg, "INFO" if success else "WARN")
        if success:
            # 应用配置到各个页面，但暂时禁用自动保存
            self.basic_config_page.save_config = None
            self.currency_config_page.save_config = None
            self.push_manage_page.save_config = None
            self.auto_trade_page.save_config = None

            # 设置配置数据
            self.basic_config_page.set_config_data(self.config.config)
            self.currency_config_page.set_config_data(self.config.config)
            self.push_manage_page.set_config_data(self.config.config)
            self.auto_trade_page.set_config_data(self.config.config)

            # 恢复自动保存
            self.basic_config_page.save_config = self.save_config
            self.currency_config_page.save_config = self.save_config
            self.push_manage_page.save_config = self.save_config
            self.auto_trade_page.save_config = self.save_config
        
    def save_config(self):
        """保存配置"""
        try:
            # 从各页面获取配置数据
            basic_config = self.basic_config_page.get_config_data()
            currency_config = self.currency_config_page.get_config_data()
            push_config = self.push_manage_page.get_config_data()
            auto_trade_config = self.auto_trade_page.get_config_data()
            
            # 使用深度更新合并配置
            def deep_merge(current, new):
                for key, value in new.items():
                    if isinstance(value, dict) and key in current and isinstance(current[key], dict):
                        deep_merge(current[key], value)
                    else:
                        current[key] = value

            # 获取当前配置的复制以保留完整结构
            merged_config = self.config.config.copy()
            
            # 依次合并各部分配置
            deep_merge(merged_config, basic_config)
            deep_merge(merged_config, currency_config)
            deep_merge(merged_config, push_config)
            deep_merge(merged_config, auto_trade_config)
            
            # 更新通货价格获取间隔
            self.currency_fetcher.set_interval(merged_config.get('currency_interval', 5))
            
            # 更新并保存配置
            self.config.config = merged_config
            success, msg = self.config.save()
            
            # 在日志页面显示结果
            self.log_page.append_log(msg, "INFO" if success else "ERROR")
            self.status_bar.setText("✅ 配置已保存" if success else "❌ 配置保存失败")
            
            # 2秒后恢复状态栏
            self.timer = self.startTimer(2000)
            
        except Exception as e:
            self.log_page.append_log(f"配置保存失败: {str(e)}", "ERROR")
            
    def timerEvent(self, event):
        """处理定时器事件"""
        self.killTimer(event.timerId())
        self.status_bar.setText("就绪")
            
    def toggle_monitor(self):
        """切换监控状态"""
        if not self.monitoring:
            self._start_monitoring()
        else:
            self._stop_monitoring()
    
    def _start_monitoring(self):
        """开始监控"""
        if not self._validate_settings():
            return
            
        try:
            # 创建并初始化监控器
            self.monitor = LogMonitor(self.config, self.log_message, self.stats_page)
            
            # 先设置自动交易配置
            auto_trade_config = self.auto_trade_page.get_config_data().get('auto_trade', {})
            
            # 配置自动交易回调
            self.auto_trade.set_callbacks(
                self.auto_trade_page.update_trade_status,
                self.auto_trade_page.add_trade_history
            )
            
            # 设置自动交易配置
            trade_config = TradeConfig(
                party_timeout_ms=auto_trade_config.get('party_timeout_ms', 30000),
                trade_timeout_ms=auto_trade_config.get('trade_timeout_ms', 10000),
                stash_interval_ms=auto_trade_config.get('stash_interval_ms', 1000),
                trade_interval_ms=auto_trade_config.get('trade_interval_ms', 1000)
            )
            self.auto_trade.set_config(trade_config)
            
            # 添加自动交易处理器
            self.monitor.add_handler(self.auto_trade)
            self.log_message("已添加自动交易处理器", "SYSTEM")
            
            # 根据配置决定是否启用自动交易
            if auto_trade_config.get('enabled', False):
                self.auto_trade.enable()
                self.log_message("自动交易已启用", "SYSTEM")
            else:
                self.auto_trade.disable()
                self.log_message("自动交易已禁用", "SYSTEM")
            
            # 根据配置创建并添加推送处理器
            push_data = self.push_manage_page.get_config_data()
            handlers_added = 0
            
            # 推送平台映射
            pusher_mapping = {
                'wxpusher': ('push.wxpusher', 'WxPusher'),
                'email': ('push.email_pusher', 'EmailPusher'),
                'serverchan': ('push.serverchan', 'ServerChan'),
                'qmsgchan': ('push.qmsgchan', 'QmsgChan')
            }
            
            # 动态导入和初始化每个启用的推送平台
            for platform, config in push_data.items():
                if isinstance(config, dict) and config.get('enabled'):
                    if platform not in pusher_mapping:
                        self.log_message(f"未知的推送平台: {platform}", "ERROR")
                        continue
                        
                    try:
                        # 动态导入推送类
                        module_path, class_name = pusher_mapping[platform]
                        module = __import__(module_path, fromlist=[class_name])
                        pusher_class = getattr(module, class_name)
                        
                        # 实例化并验证配置
                        pusher = pusher_class(self.config, self.log_message)
                        success, msg = pusher.validate_config()
                        
                        if success:
                            self.monitor.add_push_handler(pusher)
                            handlers_added += 1
                            self.log_message(f"已添加 {class_name} 推送处理器", "INFO")
                        else:
                            self.log_message(f"{class_name} 配置验证失败: {msg}", "ERROR")
                            
                    except Exception as e:
                        self.log_message(f"初始化 {platform} 推送处理器失败: {str(e)}", "ERROR")
            
            # 验证是否成功添加了推送处理器
            if handlers_added == 0:
                self.log_message("没有可用的推送处理器", "ERROR")
                return
                    
            # 启动监控
            if self.monitor.start():
                self.monitoring = True
                self.start_btn.setText("⏹ 停止监控")
                self.start_btn.setProperty('class', 'control-stop-button')
                self.start_btn.style().unpolish(self.start_btn)
                self.start_btn.style().polish(self.start_btn)
                encoding_info = self.monitor.file_utils.get_encoding_info()
                self.status_bar.setText(f"✅ 监控进行中... | 编码: {encoding_info}")
                self.log_message("监控已成功启动", "SYSTEM")
                
                # 启动通货价格获取
                self.currency_fetcher.start()
                
        except Exception as e:
            self.log_message(f"启动监控失败: {str(e)}", "ERROR")
            self.log_message(traceback.format_exc(), "DEBUG")
            self.monitoring = False
    
    def _stop_monitoring(self):
        """停止监控"""
        if self.monitor:
            self.monitor.stop()
            
        # 确保停止自动交易处理
        if hasattr(self, 'auto_trade'):
            self.auto_trade.disable()
            
        if hasattr(self, 'currency_fetcher'):
            self.currency_fetcher.stop()
            
        self.monitoring = False
        self.start_btn.setText("▶ 开始监控")
        self.start_btn.setProperty('class', 'control-button')
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.status_bar.setText("⏸️ 监控已停止")
        
    def _validate_settings(self):
        """验证设置完整性"""
        basic_success, basic_message = self.basic_config_page.validate_config()
        if not basic_success:
            self.log_page.append_log(basic_message, "ERROR")
            # 使用Toast组件显示错误
            show_toast(self, "设置不完整", basic_message, Toast.ERROR)
            return False

        # 验证是否启用了至少一种推送方式
        push_data = self.push_manage_page.get_config_data()
        enabled_pushers = [
            platform for platform, config in push_data.items()
            if isinstance(config, dict) and config.get('enabled', False)
        ]
        
        if not enabled_pushers:
            msg = "请至少启用一种推送方式"
            self.log_page.append_log(msg, "ERROR")
            show_toast(self, "设置不完整", msg, Toast.ERROR)
            return False
        
        return True
    
    def show_error_message(self, title, message):
        """显示错误消息对话框，使用Toast替代QMessageBox"""
        show_toast(self, title, message, Toast.ERROR)
    
    def log_message(self, message, level="INFO"):
        """添加消息到日志区域"""
        self.log_page.append_log(message, level)
        
    def toggle_window(self):
        """切换窗口显示状态"""
        if self.is_minimized:
            self.show()
            self.activateWindow()
            self.raise_()
            if self.always_on_top:
                self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                self.show()
            self.is_minimized = False
        else:
            self.hide()
            self.is_minimized = True
            
    def set_always_on_top(self, value):
        """设置窗口是否置顶"""
        self.always_on_top = value
        self.setWindowFlag(Qt.WindowStaysOnTopHint, value)
        if not self.is_minimized:
            self.show()
            
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        reply = QMessageBox.question(self, "确认", "是否要最小化到系统托盘？\n\n选择\"否\"将退出程序",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.ignore()
            self.hide()
            self.is_minimized = True
        else:
            self.quit_app()
            
    def get_currency_config(self):
        """获取已配置的通货单位列表"""
        if hasattr(self, 'currency_config_page'):
            return self.currency_config_page.get_config_data().get('currencies', [])
        return []

    def _update_currency_price(self, price):
        """更新通货价格显示"""
        self.price_label.setText(price)
        self.log_message(f"神圣石价格更新: {price}")
        
    def quit_app(self):
        """退出应用程序"""
        if self.monitoring:
            self.toggle_monitor()  # 停止监控
        if hasattr(self, 'currency_fetcher'):
            self.currency_fetcher.stop()
        self.tray_icon.stop()  # 删除托盘图标
        self.close()
