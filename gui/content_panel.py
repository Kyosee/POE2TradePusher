from PySide6.QtWidgets import QFrame, QVBoxLayout
from .pages import BasicConfigPage, PushManagePage, LogPage, CurrencyConfigPage, StatsPage
from .pages.stash_test_page import StashTestPage
from .pages.position_test_page import PositionTestPage
from .pages.command_test_page import CommandTestPage
from .pages.auto_trade_page import AutoTradePage
from .pages.tab_test_page import TabTestPage
from .pages.item_recognition_page import ItemRecognitionPage
from .pages.account_manage_page import AccountManagePage

class ContentPanel(QFrame):
    """右侧内容面板，管理所有页面"""
    
    def __init__(self, main_window):
        """初始化内容面板"""
        super().__init__()
        self.main_window = main_window
        self.setProperty('class', 'content-container')
        
        # 创建内容布局
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # 创建所有页面
        self.create_pages()
        
        # 默认隐藏所有页面
        self.hide_all_pages()
    
    def create_pages(self):
        """创建所有功能页面"""
        # 创建基本配置页面
        self.basic_config_page = BasicConfigPage(self, self.log_message, 
                                               self.update_status_bar, self.main_window.save_config)
        self.basic_config_page.setProperty('class', 'page-container')
        self.basic_config_page.set_main_window(self.main_window)
        self.content_layout.addWidget(self.basic_config_page)
        
        # 创建推送管理页面
        self.push_manage_page = PushManagePage(self, self.log_message, 
                                             self.update_status_bar)
        self.push_manage_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.push_manage_page)
        
        # 创建物品配置页面
        self.currency_config_page = CurrencyConfigPage(self, self.log_message, 
                                                     self.update_status_bar, self.main_window.save_config)
        self.currency_config_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.currency_config_page)
        
        # 创建账号管理页面
        self.account_manage_page = AccountManagePage(self, self.log_message, 
                                                  self.update_status_bar, self.main_window.save_config)
        self.account_manage_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.account_manage_page)
        
        # 创建日志页面
        self.log_page = LogPage(self, self.log_message, 
                              self.update_status_bar)
        self.log_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.log_page)
        
        # 创建统计页面
        self.stats_page = StatsPage(self, self.log_message,
                                  self.update_status_bar, self.main_window.save_config)
        self.stats_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.stats_page)
        
        # 创建仓库测试页面
        self.stash_recognition_page = StashTestPage(self, self.log_message,
                                                  self.update_status_bar)
        self.stash_recognition_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.stash_recognition_page)
        
        # 创建定位测试页面
        self.grid_recognition_page = PositionTestPage(self, self.log_message,
                                                    self.update_status_bar)
        self.grid_recognition_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.grid_recognition_page)
        
        # 创建命令测试页面
        self.command_test_page = CommandTestPage(self, self.log_message)
        self.command_test_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.command_test_page)
        
        # 创建自动交易页面
        self.auto_trade_page = AutoTradePage(self)
        self.auto_trade_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.auto_trade_page)
        
        # 创建Tab测试页面
        self.tab_test_page = TabTestPage(self, self.log_message, 
                                        self.update_status_bar)
        self.tab_test_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.tab_test_page)
        
        # 创建物品识别页面
        self.trade_test_page = ItemRecognitionPage(self, self.log_message,
                                          self.update_status_bar, self.main_window)
        self.trade_test_page.setProperty('class', 'page-container')
        self.content_layout.addWidget(self.trade_test_page)
        
        # 创建页面映射字典，方便按名称显示
        self.pages = {
            'basic_config': self.basic_config_page,
            'push_manage': self.push_manage_page,
            'currency_config': self.currency_config_page,
            'account_manage': self.account_manage_page,
            'log': self.log_page,
            'stats': self.stats_page,
            'stash_recognition': self.stash_recognition_page,
            'grid_recognition': self.grid_recognition_page,
            'command_test': self.command_test_page,
            'auto_trade': self.auto_trade_page,
            'tab_test': self.tab_test_page,
            'trade_test': self.trade_test_page
        }
    
    def show_page(self, page_name):
        """显示指定名称的页面"""
        self.hide_all_pages()
        if page_name in self.pages:
            self.pages[page_name].show()
    
    def hide_all_pages(self):
        """隐藏所有页面"""
        for page in self.pages.values():
            page.hide()
    
    def log_message(self, message, level="INFO"):
        """添加消息到日志区域"""
        self.main_window.log_message(message, level)
    
    def update_status_bar(self, text):
        """更新状态栏"""
        self.main_window.update_status_bar(text)
    
    def set_config_data(self, config_data):
        """设置配置数据到所有页面"""
        # 暂时禁用自动保存
        original_save_handlers = {}
        for page_name in ['basic_config_page', 'push_manage_page', 'currency_config_page', 'auto_trade_page']:
            page = getattr(self, page_name)
            if hasattr(page, 'save_config'):
                original_save_handlers[page_name] = page.save_config
                page.save_config = None
        
        # 设置配置数据
        for page_name in ['basic_config_page', 'push_manage_page', 'currency_config_page', 'account_manage_page', 'auto_trade_page']:
            page = getattr(self, page_name)
            if hasattr(page, 'set_config_data'):
                page.set_config_data(config_data)
        
        # 恢复自动保存
        for page_name, handler in original_save_handlers.items():
            page = getattr(self, page_name)
            page.save_config = handler
    
    def get_config_data(self):
        """从所有页面获取配置数据"""
        # 使用深度合并函数
        def deep_merge(current, new):
            if not isinstance(new, dict):
                return new
            result = current.copy()
            for key, value in new.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        # 获取并合并所有配置
        merged_config = {}
        for page_name in ['basic_config_page', 'push_manage_page', 'currency_config_page', 'account_manage_page', 'auto_trade_page']:
            page = getattr(self, page_name)
            if hasattr(page, 'get_config_data'):
                page_config = page.get_config_data()
                merged_config = deep_merge(merged_config, page_config)
        
        return merged_config
