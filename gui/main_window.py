import tkinter as tk
from tkinter import ttk, messagebox
from .styles import Styles
from .tray_icon import TrayIcon
from .pages import BasicConfigPage, ProcessConfigPage, PushManagePage, LogPage, CurrencyConfigPage, StatsPage
from .pages.stash_test_page import StashTestPage
from .pages.position_test_page import PositionTestPage
from core.config import Config
from core.log_monitor import LogMonitor
from push.wxpusher import WxPusher
from push.email_pusher import EmailPusher

class MainWindow:
    """主窗口类"""
    
    def __init__(self, root):
        """初始化主窗口"""
        self.root = root
        self.root.title("POE2 Trade Pusher")
        self.root.geometry("1000x800")
        self.always_on_top = False
        
        # 初始化组件
        self.styles = Styles()
        self.config = Config()
        self.tray_icon = TrayIcon()
        
        # 初始化状态
        self.is_minimized = False
        self.monitoring = False
        self.current_menu = None
        self.current_submenu = None  # 当前选中的子菜单
        
        # 设置样式
        self.styles.setup(root)
        
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
        
        # 添加初始提示信息
        self.log_message("应用程序已启动，等待配置...", "INFO")
        self.log_message("请配置日志路径和至少一种推送方式", "INFO")
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        self.main_container = ttk.Frame(self.root)
        
        # 创建左侧菜单区域
        self.menu_frame = ttk.Frame(self.main_container, style='Menu.TFrame', width=200)
        self.menu_frame.pack_propagate(False)  # 固定宽度
        
        # 创建菜单按钮
        self.menu_buttons = []
        self.submenu_frames = {}  # 存储二级菜单框架
        
        menu_items = [
            ('基本配置', self._show_basic_config, []),
            ('流程配置', self._show_process_config, []),
            ('推送配置', self._show_push_manage, []),
            ('通货配置', self._show_currency_config, []),
            ('数据统计', self._show_stats, []),
            ('触发日志', self._show_log, []),
            ('识别测试', None, [
                ('仓库测试', self._show_stash_recognition),
                ('定位测试', self._show_grid_recognition)
            ])
        ]
        
        for text, command, submenus in menu_items:
            btn = ttk.Button(self.menu_frame, text=text, style='Menu.TButton',
                           command=command if command else lambda t=text: self._toggle_submenu(t))
            btn.pack(fill=tk.X, pady=1)
            self.menu_buttons.append(btn)
            
            # 如果有子菜单，创建子菜单框架
            if submenus:
                submenu_frame = ttk.Frame(self.menu_frame, style='Menu.TFrame')
                self.submenu_frames[text] = {
                    'frame': submenu_frame,
                    'visible': False,
                    'buttons': []
                }
                
                # 创建子菜单按钮
                for sub_text, sub_command in submenus:
                    sub_btn = ttk.Button(submenu_frame, text='  ' + sub_text,
                                       style='SubMenu.TButton',
                                       command=sub_command)
                    sub_btn.pack(fill=tk.X, pady=1)
                    self.submenu_frames[text]['buttons'].append(sub_btn)
            
        # 添加弹性空间
        ttk.Frame(self.menu_frame).pack(fill=tk.Y, expand=True)
        
        # 控制按钮
        control_frame = ttk.Frame(self.menu_frame, style='Menu.TFrame')
        control_frame.pack(fill=tk.X, pady=1)
        
        # 添加分隔线
        separator = ttk.Separator(control_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=1)
        
        self.start_btn = ttk.Button(control_frame, text="▶ 开始监控",
                                   command=self.toggle_monitor,
                                   style='Control.TButton')
        self.start_btn.pack(fill=tk.X, pady=(1, 0))
        
        self.save_btn = ttk.Button(control_frame, text="💾 保存设置",
                                  command=self.save_config,
                                  style='Control.Save.TButton')
        self.save_btn.pack(fill=tk.X, pady=(1, 1))
        
        # 创建右侧内容区域
        self.content_frame = ttk.Frame(self.main_container, style='Content.TFrame')
        
        # 创建各功能页面
        self.basic_config_page = BasicConfigPage(self.content_frame, self.log_message, 
                                               lambda text: self.status_bar.config(text=text),
                                               self.save_config)
        self.basic_config_page.set_main_window(self)
        
        self.process_config_page = ProcessConfigPage(self.content_frame, self.log_message,
                                                   lambda text: self.status_bar.config(text=text),
                                                   self.save_config)
        self.push_manage_page = PushManagePage(self.content_frame, self.log_message, 
                                             lambda text: self.status_bar.config(text=text))
        self.currency_config_page = CurrencyConfigPage(self.content_frame, self.log_message, 
                                                     lambda text: self.status_bar.config(text=text),
                                                     self.save_config)
        self.log_page = LogPage(self.content_frame, self.log_message, 
                              lambda text: self.status_bar.config(text=text))
        self.stats_page = StatsPage(self.content_frame, self.log_message,
                                  lambda text: self.status_bar.config(text=text),
                                  self.save_config)
        self.stash_recognition_page = StashTestPage(self.content_frame, self.log_message,
                                                  lambda text: self.status_bar.config(text=text))
        self.grid_recognition_page = PositionTestPage(self.content_frame, self.log_message,
                                                    lambda text: self.status_bar.config(text=text))
        
        # 创建状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", style='Status.TLabel')
    
    def setup_layout(self):
        """设置界面布局"""
        # 主容器布局
        self.main_container.grid(row=0, column=0, sticky='nsew')
        
        # 左侧菜单布局
        self.menu_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # 右侧内容区域布局
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 状态栏布局
        self.status_bar.grid(row=1, column=0, sticky='nsew', padx=12, pady=4)
        
        # 主窗口布局权重配置
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 默认显示基本配置页面
        self._show_basic_config()
        
    def _show_basic_config(self):
        """显示基本配置页面"""
        self._hide_all_pages()
        self.basic_config_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(0)
        
    def _show_process_config(self):
        """显示流程配置页面"""
        self._hide_all_pages()
        self.process_config_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(1)
                
    def _show_push_manage(self):
        """显示推送管理页面"""
        self._hide_all_pages()
        self.push_manage_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(2)

    def _show_currency_config(self):
        """显示通货配置页面"""
        self._hide_all_pages()
        self.currency_config_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(3)
        
    def _show_stats(self):
        """显示数据统计页面"""
        self._hide_all_pages()
        self.stats_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(4)
        
    def _show_log(self):
        """显示日志页面"""
        self._hide_all_pages()
        self.log_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(5)
        
    def _show_stash_recognition(self):
        """显示仓库识别页面"""
        self._hide_all_pages()
        self.stash_recognition_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(6, '仓库测试')  # 选中识别测试菜单和仓库测试子菜单
        # 确保二级菜单可见
        if '识别测试' in self.submenu_frames:
            submenu_info = self.submenu_frames['识别测试']
            if not submenu_info['visible']:
                self._toggle_submenu('识别测试')
        
    def _show_grid_recognition(self):
        """显示仓位识别页面"""
        self._hide_all_pages()
        self.grid_recognition_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(6, '定位测试')  # 选中识别测试菜单和定位测试子菜单
        # 确保二级菜单可见
        if '识别测试' in self.submenu_frames:
            submenu_info = self.submenu_frames['识别测试']
            if not submenu_info['visible']:
                self._toggle_submenu('识别测试')
        
    def _hide_all_pages(self):
        """隐藏所有页面"""
        self.basic_config_page.pack_forget()
        self.process_config_page.pack_forget()
        self.currency_config_page.pack_forget()
        self.push_manage_page.pack_forget()
        self.stats_page.pack_forget()
        self.log_page.pack_forget()
        self.stash_recognition_page.pack_forget()
        self.grid_recognition_page.pack_forget()
        
    def _toggle_submenu(self, menu_text):
        """切换子菜单的显示状态"""
        if menu_text in self.submenu_frames:
            submenu_info = self.submenu_frames[menu_text]
            submenu_frame = submenu_info['frame']
            
            # 如果当前子菜单是隐藏的，显示它
            if not submenu_info['visible']:
                submenu_frame.pack(fill=tk.X, after=self.menu_buttons[6])  # 在父菜单按钮后显示
                submenu_info['visible'] = True
            else:
                submenu_frame.pack_forget()
                submenu_info['visible'] = False
                
    def _update_menu_state(self, selected_index, selected_submenu=None):
        """更新菜单按钮状态"""
        for i, btn in enumerate(self.menu_buttons):
            menu_text = btn.cget('text')
            
            # 更新一级菜单状态
            if i == selected_index:
                if menu_text in self.submenu_frames and not selected_submenu:
                    btn.state(['!selected'])  # 如果是有子菜单的项目但没有选中子菜单，取消选中状态
                else:
                    btn.state(['selected'])
            else:
                btn.state(['!selected'])
            
            # 更新二级菜单状态
            if menu_text in self.submenu_frames:
                submenu_info = self.submenu_frames[menu_text]
                for sub_btn in submenu_info['buttons']:
                    sub_text = sub_btn.cget('text').strip()  # 移除前导空格再比较
                    if i == selected_index and sub_text == selected_submenu:
                        sub_btn.state(['selected'])
                        btn.state(['selected'])  # 当子菜单选中时，父菜单也选中
                    else:
                        sub_btn.state(['!selected'])
        
        # 更新当前选中状态
        self.current_menu = selected_index
        self.current_submenu = selected_submenu
        
    def setup_bindings(self):
        """设置事件绑定"""
        # 快捷键绑定
        self.root.bind('<Control-s>', lambda e: self.save_config())
        self.root.bind('<Control-q>', lambda e: self.on_close())
        self.root.bind('<Escape>', lambda e: self.toggle_window())
        
        # 窗口事件绑定
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        
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
            self.process_config_page.save_config = None
            self.currency_config_page.save_config = None
            self.push_manage_page.save_config = None

            # 设置配置数据
            self.basic_config_page.set_config_data(self.config.config)
            self.process_config_page.set_config_data(self.config.config)
            self.currency_config_page.set_config_data(self.config.config)
            self.push_manage_page.set_config_data(self.config.config)

            # 恢复自动保存
            self.basic_config_page.save_config = self.save_config
            self.process_config_page.save_config = self.save_config
            self.currency_config_page.save_config = self.save_config
            self.push_manage_page.save_config = self.save_config
        
    def save_config(self):
        """保存配置"""
        try:
            # 从各页面获取配置数据
            basic_config = self.basic_config_page.get_config_data()
            process_config = self.process_config_page.get_config_data()
            currency_config = self.currency_config_page.get_config_data()
            push_config = self.push_manage_page.get_config_data()
            
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
            deep_merge(merged_config, process_config)
            deep_merge(merged_config, currency_config)
            deep_merge(merged_config, push_config)
            
            # 更新并保存配置
            self.config.config = merged_config
            success, msg = self.config.save()
            
            # 在日志页面显示结果
            self.log_page.append_log(msg, "INFO" if success else "ERROR")
            self.status_bar.config(text="✅ 配置已保存" if success else "❌ 配置保存失败")
            
            # 2秒后恢复状态栏
            self.root.after(2000, lambda: self.status_bar.config(text="就绪"))
            
        except Exception as e:
            self.log_page.append_log(f"配置保存失败: {str(e)}", "ERROR")
            
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
            
            # 根据配置创建并添加推送处理器
            push_data = self.push_manage_page.get_config_data()
            handlers_added = 0
            
            # 添加WxPusher处理器
            if push_data.get('wxpusher', {}).get('enabled'):
                wxpusher = WxPusher(self.config, self.log_message)
                success, msg = wxpusher.validate_config()
                if success:
                    self.monitor.add_push_handler(wxpusher)
                    handlers_added += 1
                else:
                    self.log_message(msg, "ERROR")
                    
            # 添加Email处理器
            if push_data.get('email', {}).get('enabled'):
                emailer = EmailPusher(self.config, self.log_message)
                success, msg = emailer.validate_config()
                if success:
                    self.monitor.add_push_handler(emailer)
                    handlers_added += 1
                else:
                    self.log_message(msg, "ERROR")
            
            # 验证是否成功添加了推送处理器
            if handlers_added == 0:
                self.log_message("没有可用的推送处理器", "ERROR")
                return
                    
            # 启动监控
            if self.monitor.start():
                self.monitoring = True
                self.start_btn.config(text="⏹ 停止监控", style='Control.Stop.TButton')
                encoding_info = self.monitor.file_utils.get_encoding_info()
                self.status_bar.config(text=f"✅ 监控进行中... | 编码: {encoding_info}")
            
        except Exception as e:
            self.log_message(f"启动监控失败: {str(e)}", "ERROR")
            self.monitoring = False
    
    def _stop_monitoring(self):
        """停止监控"""
        if self.monitor:
            self.monitor.stop()
        self.monitoring = False
        self.start_btn.config(text="▶ 开始监控", style='Control.TButton')
        self.status_bar.config(text="⏸️ 监控已停止")
        
    def _validate_settings(self):
        """验证设置完整性"""
        basic_success, basic_message = self.basic_config_page.validate_config()
        if not basic_success:
            self.log_page.append_log(basic_message, "ERROR")
            messagebox.showerror("设置不完整", basic_message)
            return False

        # 验证是否启用了至少一种推送方式
        push_data = self.push_manage_page.get_config_data()
        wxpusher_enabled = push_data.get('wxpusher', {}).get('enabled', False)
        email_enabled = push_data.get('email', {}).get('enabled', False)
        
        if not wxpusher_enabled and not email_enabled:
            msg = "请至少启用一种推送方式"
            self.log_page.append_log(msg, "ERROR")
            messagebox.showerror("设置不完整", msg)
            return False
        
        return True
        
    def log_message(self, message, level="INFO"):
        """添加消息到日志区域"""
        self.log_page.append_log(message, level)
        
    def toggle_window(self):
        """切换窗口显示状态"""
        if self.is_minimized:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            if self.always_on_top:
                self.root.attributes('-topmost', True)
            self.is_minimized = False
        else:
            self.root.withdraw()
            self.is_minimized = True
            
    def set_always_on_top(self, value):
        """设置窗口是否置顶"""
        self.always_on_top = value
        self.root.attributes('-topmost', value)
            
    def on_close(self):
        """处理窗口关闭事件"""
        if messagebox.askyesno("确认", "是否要最小化到系统托盘？\n\n选择\"否\"将退出程序"):
            self.root.withdraw()
            self.is_minimized = True
        else:
            self.quit_app()
            
    def get_currency_config(self):
        """获取已配置的通货单位列表"""
        if hasattr(self, 'currency_config_page'):
            return self.currency_config_page.get_config_data().get('currencies', [])
        return []

    def quit_app(self):
        """退出应用程序"""
        if self.monitoring:
            self.toggle_monitor()  # 停止监控
        self.tray_icon.stop()  # 删除托盘图标
        self.root.quit()
