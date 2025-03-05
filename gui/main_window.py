from PySide6.QtWidgets import QMainWindow, QWidget, QMessageBox, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QThread
from PySide6.QtGui import QIcon
import threading

from core.config import Config
from utils.currency_fetcher import CurrencyFetcher
from .styles import Styles
from .tray_icon import TrayIcon
from .menu_panel import MenuPanel
from .content_panel import ContentPanel
from .status_bar import StatusBarWidget
from .monitor_manager import MonitorManager
from .widgets.toast import show_toast, Toast

class InitThread(QThread):
    """非必要组件初始化线程"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
    def run(self):
        """运行初始化任务"""
        # 预先初始化对话框，避免首次弹窗卡顿
        self.main_window._pre_init_dialogs()
        
        # 初始化通货价格获取器
        self.main_window._init_currency_fetcher()
        
        # 初始化监控管理器
        self.main_window._init_monitor_manager()
        
        # 添加初始提示信息
        self.main_window.log_message("应用程序已启动，等待配置...", "INFO")
        self.main_window.log_message("请配置日志路径和至少一种推送方式", "INFO")

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
        
        # 初始化必要组件
        self.styles = Styles()
        self.config = Config()
        self.tray_icon = TrayIcon(icon_path="assets/icon.png")
        
        # 初始化状态
        self.is_minimized = False
        self.monitoring = False
        
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
        
        # 初始化托盘
        self.setup_tray()
        
        # 加载配置
        self.load_config()
        
        # 默认显示基本配置页面
        self._show_basic_config()
        
        # 启动非必要组件初始化线程
        self.init_thread = InitThread(self)
        self.init_thread.start()
        
    def _pre_init_dialogs(self):
        """预先初始化对话框组件，避免首次显示时卡顿"""
        self.message_box = QMessageBox(self)
        self.message_box.setWindowTitle("初始化")
        self.message_box.setText("正在初始化组件...")
        self.message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    
    def _init_currency_fetcher(self):
        """初始化通货价格获取器"""
        self.currency_fetcher = CurrencyFetcher()
        self.currency_fetcher.price_updated.connect(self._update_currency_price)
        # 立即获取一次价格
        self.currency_fetcher.fetch_price()
    
    def _init_monitor_manager(self):
        """初始化监控管理器"""
        self.monitor_manager = MonitorManager(
            self.config, 
            self.log_message,
            self.content_panel.stats_page,
            self.content_panel.auto_trade_page,
            self.update_status_bar
        )
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建左侧菜单区域
        self.menu_panel = MenuPanel(self)
        
        # 创建右侧内容区域
        self.content_panel = ContentPanel(self)
        
        # 创建状态栏
        self.status_bar_widget = StatusBarWidget()
        self.statusBar().addWidget(self.status_bar_widget)
        
    def setup_layout(self):
        """设置界面布局"""
        self.main_layout.addWidget(self.menu_panel)
        self.main_layout.addWidget(self.content_panel)
        
    def update_status_bar(self, text):
        """更新状态栏"""
        self.status_bar_widget.set_status(text)
        
    def _show_basic_config(self):
        """显示基本配置页面"""
        self.content_panel.show_page('basic_config')
                
    def _show_push_manage(self):
        """显示推送管理页面"""
        self.content_panel.show_page('push_manage')

    def _show_currency_config(self):
        """显示通货配置页面"""
        self.content_panel.show_page('currency_config')
        
    def _show_stats(self):
        """显示数据统计页面"""
        self.content_panel.show_page('stats')
        
    def _show_log(self):
        """显示日志页面"""
        self.content_panel.show_page('log')
        
    def _show_stash_recognition(self):
        """显示仓库识别页面"""
        self.content_panel.show_page('stash_recognition')
                
    def _show_command_test(self):
        """显示命令测试页面"""
        self.content_panel.show_page('command_test')
        
    def _show_grid_recognition(self):
        """显示仓位识别页面"""
        self.content_panel.show_page('grid_recognition')
    
    def _show_auto_trade(self):
        """显示自动交易页面"""
        self.content_panel.show_page('auto_trade')
        
    def _show_tab_test(self):
        """显示Tab测试页面"""
        self.content_panel.show_page('tab_test')
        
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
        self.log_message(msg, "INFO" if success else "WARN")
        if success:
            # 应用配置到内容面板
            self.content_panel.set_config_data(self.config.config)
        
    def save_config(self):
        """保存配置"""
        try:
            # 从内容面板获取配置数据
            merged_config = self.content_panel.get_config_data()
            
            # 更新通货价格获取间隔
            if hasattr(self, 'currency_fetcher'):
                self.currency_fetcher.set_interval(merged_config.get('currency_interval', 5))
            
            # 更新并保存配置
            self.config.config = merged_config
            success, msg = self.config.save()
            
            # 在日志页面显示结果
            self.log_message(msg, "INFO" if success else "ERROR")
            self.update_status_bar("✅ 配置已保存" if success else "❌ 配置保存失败")
            
            # 2秒后恢复状态栏
            self.timer = self.startTimer(2000)
            
        except Exception as e:
            self.log_message(f"配置保存失败: {str(e)}", "ERROR")
            
    def timerEvent(self, event):
        """处理定时器事件"""
        self.killTimer(event.timerId())
        self.update_status_bar("就绪")
            
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
            
        # 确保监控管理器已初始化
        if not hasattr(self, 'monitor_manager'):
            self.log_message("监控管理器尚未初始化完成，请稍后再试", "ERROR")
            show_toast(self, "初始化未完成", "监控管理器尚未初始化完成，请稍后再试", Toast.ERROR)
            return
            
        # 获取推送和自动交易配置    
        push_config = self.content_panel.push_manage_page.get_config_data()
        auto_trade_config = self.content_panel.auto_trade_page.get_config_data()
        
        # 启动监控
        success, encoding_info = self.monitor_manager.start_monitoring(
            push_config, auto_trade_config
        )
        
        if success:
            self.monitoring = True
            self.menu_panel.set_monitor_active(True)
            self.update_status_bar(f"✅ 监控进行中... | 编码: {encoding_info}")
            self.log_message("监控已成功启动", "SYSTEM")
            
            # 启动通货价格获取
            if hasattr(self, 'currency_fetcher'):
                self.currency_fetcher.start()
    
    def _stop_monitoring(self):
        """停止监控"""
        if hasattr(self, 'monitor_manager'):
            self.monitor_manager.stop_monitoring()
            
        if hasattr(self, 'currency_fetcher'):
            self.currency_fetcher.stop()
            
        self.monitoring = False
        self.menu_panel.set_monitor_active(False)
        self.update_status_bar("⏸️ 监控已停止")
        
    def _validate_settings(self):
        """验证设置完整性"""
        basic_success, basic_message = self.content_panel.basic_config_page.validate_config()
        if not basic_success:
            self.log_message(basic_message, "ERROR")
            show_toast(self, "设置不完整", basic_message, Toast.ERROR)
            return False

        # 验证是否启用了至少一种推送方式
        push_data = self.content_panel.push_manage_page.get_config_data()
        enabled_pushers = [
            platform for platform, config in push_data.items()
            if isinstance(config, dict) and config.get('enabled', False)
        ]
        
        if not enabled_pushers:
            msg = "请至少启用一种推送方式"
            self.log_message(msg, "ERROR")
            show_toast(self, "设置不完整", msg, Toast.ERROR)
            return False
        
        return True
    
    def show_error_message(self, title, message):
        """显示错误消息对话框，使用Toast替代QMessageBox"""
        show_toast(self, title, message, Toast.ERROR)
    
    def log_message(self, message, level="INFO"):
        """添加消息到日志区域"""
        if hasattr(self, 'content_panel') and hasattr(self.content_panel, 'log_page'):
            self.content_panel.log_page.append_log(message, level)
        
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
        if hasattr(self, 'content_panel') and hasattr(self.content_panel, 'currency_config_page'):
            return self.content_panel.currency_config_page.get_config_data().get('currencies', [])
        return []

    def _update_currency_price(self, price):
        """更新通货价格显示"""
        self.status_bar_widget.set_price(price)
        self.log_message(f"神圣石价格更新: {price}")
        
    def quit_app(self):
        """退出应用程序"""
        if self.monitoring:
            self.toggle_monitor()  # 停止监控
        if hasattr(self, 'currency_fetcher'):
            self.currency_fetcher.stop()
        self.tray_icon.stop()  # 删除托盘图标
        self.close()
