import tkinter as tk
from tkinter import ttk, messagebox
from .styles import Styles
from .tray_icon import TrayIcon
from .pages import BasicConfigPage, PushManagePage, LogPage
from core.config import Config
from core.log_monitor import LogMonitor
from push.wxpusher import WxPusher

class MainWindow:
    """主窗口类"""
    
    def __init__(self, root):
        """初始化主窗口"""
        self.root = root
        self.root.title("POE2 Trade Pusher")
        self.root.geometry("1000x800")
        
        # 初始化组件
        self.styles = Styles()
        self.config = Config()
        self.tray_icon = TrayIcon()
        
        # 初始化状态
        self.is_minimized = False
        self.monitoring = False
        self.current_menu = None
        
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
        
        # 初始化推送器和监控器
        self.push_handler = None
        self.monitor = None
        
        # 添加初始提示信息
        self.log_message("应用程序已启动，等待配置...", "INFO")
        self.log_message("请设置日志路径、WxPusher信息和关键词", "INFO")
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        self.main_container = ttk.Frame(self.root)
        
        # 创建左侧菜单区域
        self.menu_frame = ttk.Frame(self.main_container, style='Menu.TFrame', width=200)
        self.menu_frame.pack_propagate(False)  # 固定宽度
        
        # 创建菜单按钮
        self.menu_buttons = []
        menu_items = [
            ('基本配置', self._show_basic_config),
            ('推送管理', self._show_push_manage),
            ('触发日志', self._show_log)
        ]
        
        for text, command in menu_items:
            btn = ttk.Button(self.menu_frame, text=text, style='Menu.TButton',
                           command=command)
            btn.pack(fill=tk.X, pady=1)
            self.menu_buttons.append(btn)
            
        # 添加弹性空间
        ttk.Frame(self.menu_frame).pack(fill=tk.Y, expand=True)
        
        # 控制按钮
        control_frame = ttk.Frame(self.menu_frame, style='Menu.TFrame')
        control_frame.pack(fill=tk.X, pady=1)
        
        # 添加分隔线
        separator = ttk.Separator(control_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=1)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ 开始监控",
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
                                               lambda text: self.status_bar.config(text=text))
        self.push_manage_page = PushManagePage(self.content_frame, self.log_message, 
                                             lambda text: self.status_bar.config(text=text))
        self.log_page = LogPage(self.content_frame, self.log_message, 
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
        
    def _show_push_manage(self):
        """显示推送管理页面"""
        self._hide_all_pages()
        self.push_manage_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(1)
        
    def _show_log(self):
        """显示日志页面"""
        self._hide_all_pages()
        self.log_page.pack(fill=tk.BOTH, expand=True)
        self._update_menu_state(2)
        
    def _hide_all_pages(self):
        """隐藏所有页面"""
        self.basic_config_page.pack_forget()
        self.push_manage_page.pack_forget()
        self.log_page.pack_forget()
        
    def _update_menu_state(self, selected_index):
        """更新菜单按钮状态"""
        for i, btn in enumerate(self.menu_buttons):
            if i == selected_index:
                btn.state(['selected'])
            else:
                btn.state(['!selected'])
        
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
            # 应用配置到各个页面
            self.basic_config_page.set_data(self.config.config)
            self.push_manage_page.set_data(self.config.config)
        
    def save_config(self):
        """保存配置"""
        try:
            # 从各页面获取配置数据
            basic_config = self.basic_config_page.get_data()
            push_config = self.push_manage_page.get_data()
            
            # 合并配置数据
            config = {**basic_config, **push_config}
            
            # 更新并保存配置
            self.config.update(config)
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
            # 初始化推送器
            self.push_handler = WxPusher(self.config, self.log_message)
            success, msg = self.push_handler.validate_config()
            if not success:
                self.log_message(msg, "ERROR")
                return
                
            # 初始化监控器
            self.monitor = LogMonitor(
                self.config,
                lambda kw, content: self.push_handler.send(kw, content),
                self.log_message
            )
            
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
        basic_data = self.basic_config_page.get_data()
        push_data = self.push_manage_page.get_data()
        
        required = [
            (basic_data.get('log_path'), "请选择日志文件"),
            (push_data.get('app_token'), "请输入App Token"),
            (push_data.get('uid'), "请输入用户UID"),
            (basic_data.get('keywords', []), "请至少添加一个关键词")
        ]
        
        for value, msg in required:
            if not value:
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
            self.is_minimized = False
        else:
            self.root.withdraw()
            self.is_minimized = True
            
    def on_close(self):
        """处理窗口关闭事件"""
        if messagebox.askyesno("确认", "是否要最小化到系统托盘？\n\n选择\"否\"将退出程序"):
            self.root.withdraw()
            self.is_minimized = True
        else:
            self.quit_app()
            
    def quit_app(self):
        """退出应用程序"""
        if self.monitoring:
            self.toggle_monitor()  # 停止监控
        self.tray_icon.stop()  # 删除托盘图标
        self.root.quit()
