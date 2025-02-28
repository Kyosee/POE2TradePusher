import os
import time
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext
from .styles import Styles
from .tray_icon import TrayIcon
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
            btn.pack(fill=X, pady=1)
            self.menu_buttons.append(btn)
            
        # 添加弹性空间
        ttk.Frame(self.menu_frame).pack(fill=Y, expand=True)
        
        # 控制按钮
        control_frame = ttk.Frame(self.menu_frame, style='Menu.TFrame')
        control_frame.pack(fill=X, pady=1)
        
        # 添加分隔线
        separator = ttk.Separator(control_frame, orient='horizontal')
        separator.pack(fill=X, pady=1)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ 开始监控",
                                   command=self.toggle_monitor,
                                   style='Control.TButton')
        self.start_btn.pack(fill=X, pady=(1, 0))
        
        self.save_btn = ttk.Button(control_frame, text="💾 保存设置",
                                  command=self.save_config,
                                  style='Control.Save.TButton')
        self.save_btn.pack(fill=X, pady=(1, 1))
        
        # 创建右侧内容区域
        self.content_frame = ttk.Frame(self.main_container, style='Content.TFrame')
        
        # 创建各功能页面
        self.basic_config_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        self.push_manage_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        self.log_frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        
        # 创建各页面内容
        self._create_basic_config_page()
        self._create_push_manage_page()
        self._create_log_page()
        
        # 状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", style='Status.TLabel')
                                  
    def _create_basic_config_page(self):
        """创建基本配置页面"""
        # 创建文件配置区域
        self.file_frame = ttk.LabelFrame(self.basic_config_frame, text="日志文件配置")
        ttk.Label(self.file_frame, text="日志路径:", style='Frame.TLabel').grid(row=0, column=0, padx=6)
        self.file_entry = ttk.Entry(self.file_frame, width=70)
        self.browse_btn = ttk.Button(self.file_frame, text="📂 浏览", command=self.select_file)
        
        # 布局文件配置区域
        self.file_frame.pack(fill=X, padx=12, pady=6)
        self.file_entry.grid(row=0, column=1, padx=6, sticky="ew")
        self.browse_btn.grid(row=0, column=2, padx=6)
        self.file_frame.columnconfigure(1, weight=1)
        
        # 创建监控设置区域
        self.settings_frame = ttk.LabelFrame(self.basic_config_frame, text="监控设置")
        ttk.Label(self.settings_frame, text="检测间隔(ms):", style='Frame.TLabel').grid(row=0, column=0, padx=6)
        self.interval_spin = ttk.Spinbox(self.settings_frame, from_=500, to=5000, 
                                       increment=100, width=8, font=('Consolas', 10))
        
        ttk.Label(self.settings_frame, text="推送间隔(ms):", style='Frame.TLabel').grid(row=0, column=2, padx=6)
        self.push_interval_entry = ttk.Entry(self.settings_frame, width=8, font=('Consolas', 10))
        
        # 布局监控设置区域
        self.settings_frame.pack(fill=X, padx=12, pady=6)
        self.interval_spin.grid(row=0, column=1, padx=6)
        self.push_interval_entry.grid(row=0, column=3, padx=6)
        
        # 设置默认值
        self.interval_spin.set(1000)
        self.push_interval_entry.insert(0, "0")
        
        # 创建关键词管理区域
        self.keywords_frame = ttk.LabelFrame(self.basic_config_frame, text="关键词管理")
        
        # 输入框和按钮
        input_frame = ttk.Frame(self.keywords_frame)
        self.keyword_entry = ttk.Entry(input_frame, font=('微软雅黑', 10))
        self.add_btn = ttk.Button(input_frame, text="➕ 添加", command=self.add_keyword)
        self.clear_kw_btn = ttk.Button(input_frame, text="🔄 清空", command=self.clear_keywords)
        
        # 布局输入区域
        input_frame.pack(fill=X, padx=6, pady=3)
        self.keyword_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 3))
        self.add_btn.pack(side=LEFT, padx=3)
        self.clear_kw_btn.pack(side=LEFT, padx=3)
        
        # 关键词列表
        self.keyword_list = Listbox(self.keywords_frame, height=8, font=('微软雅黑', 10),
                                  selectmode=SINGLE, bg="white",
                                  relief='solid', borderwidth=1,
                                  activestyle='none')
        self.keyword_list.pack(fill=BOTH, expand=True, padx=6, pady=3)
        
        # 设置关键词右键菜单
        self._setup_keyword_menu()
        
        # 布局关键词管理区域
        self.keywords_frame.pack(fill=BOTH, expand=True, padx=12, pady=6)
        
    def _create_push_manage_page(self):
        """创建推送管理页面"""
        # 创建WxPusher配置区域
        self.wxpusher_frame = ttk.LabelFrame(self.push_manage_frame, text="WxPusher配置")
        
        # AppToken
        ttk.Label(self.wxpusher_frame, text="App Token:", style='Frame.TLabel').grid(row=0, column=0, padx=6, sticky="w")
        self.app_token_entry = ttk.Entry(self.wxpusher_frame, width=50, font=('Consolas', 10))
        
        # UID
        ttk.Label(self.wxpusher_frame, text="用户UID:", style='Frame.TLabel').grid(row=1, column=0, padx=6, sticky="w")
        self.uid_entry = ttk.Entry(self.wxpusher_frame, width=50, font=('Consolas', 10))
        
        # 添加测试按钮
        self.test_btn = ttk.Button(self.wxpusher_frame, text="🔔 测试", command=self.test_wxpusher, width=8)
        
        # 布局WxPusher配置区域
        self.wxpusher_frame.pack(fill=BOTH, expand=True, padx=12, pady=6)
        self.app_token_entry.grid(row=0, column=1, padx=6, sticky="ew")
        self.uid_entry.grid(row=1, column=1, padx=6, sticky="ew")
        self.test_btn.grid(row=0, column=2, rowspan=2, padx=6, sticky="ns")
        self.wxpusher_frame.columnconfigure(1, weight=1)
        
    def _create_log_page(self):
        """创建日志页面"""
        # 日志容器
        log_container = Frame(self.log_frame, bg="white", relief="solid", bd=1)
        log_container.pack(fill=BOTH, expand=True, padx=12, pady=6)
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)
        
        # 文本区域
        self.log_area = scrolledtext.ScrolledText(
            log_container,
            wrap=WORD,
            font=('微软雅黑', 9),
            bg="white",
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=8,
            selectbackground='#e1e1e1',
            selectforeground='#2C2C2C',
        )
        self.log_area.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        self.log_area.configure(state='disabled')
        
        # 滚动条
        scrollbar = Scrollbar(log_container, orient="vertical", command=self.log_area.yview)
        scrollbar.grid(row=0, column=0, sticky="nse")
        self.log_area.configure(yscrollcommand=scrollbar.set)
        
        # 右侧按钮区域
        right_panel = Frame(log_container, bg="white", width=100)
        right_panel.grid(row=0, column=1, sticky="ns", padx=(2, 0))
        right_panel.grid_propagate(False)
        
        # 添加按钮
        self.clear_log_btn = ttk.Button(
            right_panel, text="清空", command=self.clear_log,
            style='Control.TButton', width=9
        )
        self.clear_log_btn.pack(side=TOP, padx=5, pady=5, fill=X)
        
        self.export_log_btn = ttk.Button(
            right_panel, text="导出", command=self.export_log,
            style='Control.TButton', width=9
        )
        self.export_log_btn.pack(side=TOP, padx=5, pady=5, fill=X)
        
    def setup_layout(self):
        """设置界面布局"""
        # 主容器布局
        self.main_container.grid(row=0, column=0, sticky='nsew')
        
        # 左侧菜单布局
        self.menu_frame.pack(side=LEFT, fill=Y)
        
        # 右侧内容区域布局
        self.content_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        # 状态栏布局
        self.status_bar.grid(row=1, column=0, sticky='ew', padx=12, pady=4)
        
        # 主窗口布局权重配置
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 默认显示基本配置页面
        self._show_basic_config()
        
    def _show_basic_config(self):
        """显示基本配置页面"""
        self._hide_all_pages()
        self.basic_config_frame.pack(fill=BOTH, expand=True)
        self._update_menu_state(0)
        
    def _show_push_manage(self):
        """显示推送管理页面"""
        self._hide_all_pages()
        self.push_manage_frame.pack(fill=BOTH, expand=True)
        self._update_menu_state(1)
        
    def _show_log(self):
        """显示日志页面"""
        self._hide_all_pages()
        self.log_frame.pack(fill=BOTH, expand=True)
        self._update_menu_state(2)
        
    def _hide_all_pages(self):
        """隐藏所有页面"""
        self.basic_config_frame.pack_forget()
        self.push_manage_frame.pack_forget()
        self.log_frame.pack_forget()
        
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
        
        # 设置回车键绑定
        self.keyword_entry.bind('<Return>', lambda e: self.add_keyword())
        
        # 设置关键词列表事件
        self.keyword_list.bind('<Double-Button-1>', lambda e: self.edit_keyword())
        self.keyword_list.bind('<Button-3>', self.show_keyword_menu)
        
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
            
    def _setup_keyword_menu(self):
        """设置关键词右键菜单"""
        self.keyword_menu = Menu(self.root, tearoff=0, font=('微软雅黑', 9))
        self.keyword_menu.configure(bg='white', activebackground='#E7F7EE',
                                  activeforeground='#07C160', relief='flat')
        
        # 添加菜单项
        self.keyword_menu.add_command(label="✏️ 编辑", command=self.edit_keyword,
                                    font=('微软雅黑', 9))
        self.keyword_menu.add_command(label="❌ 删除", command=self.remove_selected_keyword,
                                    font=('微软雅黑', 9))
        self.keyword_menu.add_separator()
        self.keyword_menu.add_command(label="📋 复制", command=self.copy_keyword,
                                    font=('微软雅黑', 9))
                                    
    def load_config(self):
        """加载配置"""
        success, msg = self.config.load()
        self.log_message(msg, "INFO" if success else "WARN")
        if success:
            self._apply_config_to_ui()
            
    def _apply_config_to_ui(self):
        """将配置应用到界面控件"""
        # 应用关键词
        self.keyword_list.delete(0, END)
        for kw in self.config.get('keywords', []):
            self.keyword_list.insert(END, kw)
            
        # 应用检测间隔
        self.interval_spin.set(self.config.get('interval', 1000))
        
        # 应用推送间隔
        self.push_interval_entry.delete(0, END)
        self.push_interval_entry.insert(0, self.config.get('push_interval', 0))
        
        # 应用WxPusher配置
        self.app_token_entry.delete(0, END)
        self.app_token_entry.insert(0, self.config.get('app_token', ''))
        
        self.uid_entry.delete(0, END)
        self.uid_entry.insert(0, self.config.get('uid', ''))
        
        # 应用日志路径
        self.file_entry.delete(0, END)
        self.file_entry.insert(0, self.config.get('log_path', ''))
        
    def save_config(self):
        """保存配置"""
        try:
            config = {
                'interval': int(self.interval_spin.get()),
                'push_interval': int(self.push_interval_entry.get() or 0),
                'app_token': self.app_token_entry.get(),
                'uid': self.uid_entry.get(),
                'keywords': list(self.keyword_list.get(0, END)),
                'log_path': self.file_entry.get()
            }
            
            self.config.update(config)
            success, msg = self.config.save()
            
            self.log_message(msg, "INFO" if success else "ERROR")
            self.status_bar.config(text="✅ 配置已保存" if success else "❌ 配置保存失败")
            
            # 2秒后恢复状态栏
            self.root.after(2000, lambda: self.status_bar.config(text="就绪"))
            
        except Exception as e:
            self.log_message(f"配置保存失败: {str(e)}", "ERROR")
            
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
        required = [
            (self.file_entry.get(), "请选择日志文件"),
            (self.app_token_entry.get(), "请输入App Token"),
            (self.uid_entry.get(), "请输入用户UID"),
            (self.keyword_list.size() > 0, "请至少添加一个关键词")
        ]
        
        for value, msg in required:
            if not value:
                self.log_message(msg, "ERROR")
                messagebox.showerror("设置不完整", msg)
                return False
                
        return True
        
    def select_file(self):
        """选择文件"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_entry.delete(0, END)
            self.file_entry.insert(0, file_path)
            self.log_message(f"已选择日志文件: {file_path}")
            
    def test_wxpusher(self):
        """测试WxPusher配置"""
        # 保存当前配置
        self.save_config()
        
        # 创建临时推送器
        pusher = WxPusher(self.config, self.log_message)
        pusher.test()
        
    def add_keyword(self):
        """添加关键词"""
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            self.log_message("无法添加空关键词", "WARN")
            return
        if keyword in self.keyword_list.get(0, END):
            self.log_message(f"重复关键词: {keyword}", "WARN")
            return
        self.keyword_list.insert(END, keyword)
        self.keyword_entry.delete(0, END)
        self.log_message(f"已添加关键词: {keyword}")
        
    def remove_selected_keyword(self):
        """删除选中的关键词"""
        selection = self.keyword_list.curselection()
        if selection:
            keyword = self.keyword_list.get(selection[0])
            self.keyword_list.delete(selection[0])
            self.log_message(f"已移除关键词: {keyword}")
            
    def clear_keywords(self):
        """清空关键词"""
        if messagebox.askyesno("确认清空", "确定要清空所有关键词吗？\n此操作无法撤销"):
            self.keyword_list.delete(0, END)
            self.log_message("已清空关键词列表")
            self.status_bar.config(text="✨ 已清空关键词列表")
            
    def edit_keyword(self):
        """编辑选中的关键词"""
        selection = self.keyword_list.curselection()
        if selection:
            current_keyword = self.keyword_list.get(selection[0])
            dialog = Toplevel(self.root)
            dialog.title("编辑关键词")
            dialog.geometry("300x140")
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.configure(bg='white')
            
            # 设置对话框样式
            main_frame = ttk.Frame(dialog, style='Dialog.TFrame')
            main_frame.pack(expand=True, fill='both', padx=2, pady=2)
            
            ttk.Label(main_frame, text="请输入新的关键词：",
                     font=('微软雅黑', 9)).pack(padx=10, pady=(10, 5))
            
            entry = ttk.Entry(main_frame, width=40, font=('微软雅黑', 9))
            entry.insert(0, current_keyword)
            entry.pack(padx=10, pady=(0, 10))
            
            def save_edit():
                new_keyword = entry.get().strip()
                if new_keyword and new_keyword != current_keyword:
                    if new_keyword not in self.keyword_list.get(0, END):
                        self.keyword_list.delete(selection[0])
                        self.keyword_list.insert(selection[0], new_keyword)
                        self.log_message(f"关键词已更新: {current_keyword} → {new_keyword}")
                        dialog.destroy()
                    else:
                        messagebox.showwarning("提示", "关键词已存在")
                else:
                    dialog.destroy()
            
            btn_frame = ttk.Frame(main_frame)
            ttk.Button(btn_frame, text="✔️ 确定", command=save_edit, 
                      style='Dialog.TButton').pack(side=LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ 取消", command=dialog.destroy, 
                      style='Dialog.TButton').pack(side=LEFT, padx=5)
            btn_frame.pack(pady=(0, 10))

            # 居中对话框
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')
            
            entry.focus_set()
            dialog.bind('<Return>', lambda e: save_edit())
            dialog.bind('<Escape>', lambda e: dialog.destroy())
            
    def show_keyword_menu(self, event):
        """显示关键词右键菜单"""
        if self.keyword_list.size() > 0:
            selection = self.keyword_list.curselection()
            if selection:  # 只在选中项目时显示菜单
                self.keyword_menu.post(event.x_root, event.y_root)
                
    def copy_keyword(self):
        """复制选中的关键词到剪贴板"""
        selection = self.keyword_list.curselection()
        if selection:
            keyword = self.keyword_list.get(selection[0])
            self.root.clipboard_clear()
            self.root.clipboard_append(keyword)
            self.status_bar.config(text=f"已复制: {keyword}")
            
    def export_log(self):
        """导出日志到文件"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"trade_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_area.get(1.0, END))
                self.status_bar.config(text=f"日志已导出: {file_path}")
                self.log_message("日志导出成功")
            except Exception as e:
                self.log_message(f"日志导出失败: {str(e)}", "ERROR")
                
    def clear_log(self):
        """清空日志区域"""
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, END)
        self.log_area.configure(state='disabled')
        self.status_bar.config(text="日志已清空")
        
    def log_message(self, message, level="INFO"):
        """添加消息到日志区域"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 将日志区域设置为可编辑
        self.log_area.configure(state='normal')
        
        # 配置标签颜色
        self.log_area.tag_configure(level, foreground=self.styles.log_colors.get(level, "#333333"))
        
        # 插入日志条目
        self.log_area.insert(END, f"[{timestamp}] [{level}] {message}\n", level)
        
        # 返回只读状态
        self.log_area.configure(state='disabled')
        
        # 自动滚动到底部
        self.log_area.see(END)
        
        # 强制更新UI
        self.root.update_idletasks()
        
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
