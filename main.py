import os
import re
import time
import json
import requests
import chardet
import threading
import pystray
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext
from functools import lru_cache
import io
import traceback

class AdvancedLogMonitorPro:
    """POE2交易信息监控推送应用，支持关键词监控、WxPusher推送和系统托盘操作"""
    
    def __init__(self, root):
        """初始化应用程序"""
        # 基础设置
        self.root = root
        self.root.title("POE2 Trade Pusher")
        self.root.geometry("1000x800")
        self.config_file = "config.json"
        
        # 文件监控相关参数
        self.current_encoding = 'utf-8'
        self.fallback_encodings = ['gb18030', 'gbk', 'big5']
        self.last_position = 0
        self.last_size = 0
        self.last_timestamp = None
        self.monitoring = False
        self.buffer_size = 8192
        self.time_pattern = re.compile(r'^(\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})')
        self.buffer = io.StringIO()
        
        # 控制变量
        self.config = {}
        self.stop_event = threading.Event()
        self.last_push_time = 0
        self.push_interval = 0
        
        # 界面主题颜色
        self.wx_green = '#07C160'
        self.wx_bg = '#F7F7F7'
        self.wx_hover = '#06AD56'
        self.wx_text = '#2C2C2C'
        self.wx_border = '#E6E7E8'
        
        # 初始化界面
        self.setup_style()
        self.create_widgets()
        self.setup_layout()
        self.setup_bindings()
        self.setup_tray()
        self.load_config()
        
        # 添加初始提示信息
        self.log_message("应用程序已启动，等待配置...", "INFO")
        self.log_message("请设置日志路径、WxPusher信息和关键词", "INFO")

    def setup_style(self):
        """配置应用程序样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # 基础样式
        self._configure_card_style()
        self._configure_button_styles()
        self._configure_text_styles()
        self._configure_frame_styles()
        
        # 设置主窗口背景
        self.root.configure(bg=self.wx_bg)
        
        # 设置列表框样式
        self._configure_listbox_style()
    
    def _configure_card_style(self):
        """配置卡片样式"""
        self.style.configure('Card.TLabelframe', 
            background='white',
            relief='solid',
            borderwidth=1,
            bordercolor=self.wx_border)
            
        self.style.configure('Card.TLabelframe.Label',
            font=('微软雅黑', 10, 'bold'),
            foreground=self.wx_text,
            background='white',
            padding=(10, 5))
    
    def _configure_button_styles(self):
        """配置按钮样式"""
        # 基础按钮
        self.style.configure('TButton', 
            padding=(15, 8),
            font=('微软雅黑', 10),
            background=self.wx_green,
            foreground='white',
            borderwidth=0,
            focuscolor=self.wx_green)
            
        self.style.map('TButton',
            foreground=[('active', 'white'), ('disabled', '#A8A8A8')],
            background=[('active', self.wx_hover), ('disabled', '#E0E0E0')])
            
        # 停止按钮
        self.style.configure('Stop.TButton',
            background='#ff4d4f',
            foreground='white')
            
        self.style.map('Stop.TButton',
            background=[('active', '#ff7875'), ('disabled', '#E0E0E0')])
            
        # 对话框按钮
        self.style.configure('Dialog.TButton',
            padding=(10, 5),
            font=('微软雅黑', 9))
    
    def _configure_text_styles(self):
        """配置文本样式"""
        # 标签样式
        self.style.configure('TLabel', 
            font=('微软雅黑', 10),
            foreground=self.wx_text,
            background='white')
            
        self.style.configure('Frame.TLabel',
            font=('微软雅黑', 10),
            foreground=self.wx_text,
            background='white')
            
        # 状态栏
        self.style.configure('Status.TLabel', 
            padding=6,
            background=self.wx_bg,
            foreground=self.wx_text)
            
        # 输入框
        self.style.configure('TEntry', 
            font=('微软雅黑', 10),
            fieldbackground='white',
            borderwidth=1,
            relief='solid',
            padding=5)
    
    def _configure_frame_styles(self):
        """配置框架样式"""
        self.style.configure('TLabelframe', 
            padding=10,
            background='white',
            relief='flat')
            
        self.style.configure('TLabelframe.Label', 
            font=('微软雅黑', 10, 'bold'),
            foreground=self.wx_text,
            background='white')
            
        self.style.configure('Dialog.TFrame',
            background='white',
            relief='solid',
            borderwidth=1)
    
    def _configure_listbox_style(self):
        """配置列表样式"""
        self.root.option_add('*TListbox*background', 'white')
        self.root.option_add('*TListbox*foreground', self.wx_text)
        self.root.option_add('*TListbox*selectBackground', self.wx_green)
        self.root.option_add('*TListbox*selectForeground', 'white')
        self.root.option_add('*TListbox*selectBackground', '#E7F7EE')
        self.root.option_add('*TListbox*selectForeground', '#07C160')

    def create_widgets(self):
        """创建用户界面组件"""
        # 状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", style='Status.TLabel')
        
        # 创建各功能区域
        self._create_file_section()
        self._create_settings_section()
        self._create_keyword_section()
        self._create_wxpusher_section()
        self._create_log_section()
        self._create_control_section()
    
    def _create_file_section(self):
        """创建文件配置区域"""
        self.file_frame = ttk.LabelFrame(self.root, text="日志文件配置")
        ttk.Label(self.file_frame, text="日志路径:", style='Frame.TLabel').grid(row=0, column=0, padx=6)
        self.file_entry = ttk.Entry(self.file_frame, width=70)
        self.browse_btn = ttk.Button(self.file_frame, text="📂 浏览", command=self.select_file)
    
    def _create_settings_section(self):
        """创建监控设置区域"""
        self.settings_frame = ttk.LabelFrame(self.root, text="监控设置")
        
        # 检测间隔
        ttk.Label(self.settings_frame, text="检测间隔(ms):", style='Frame.TLabel').grid(row=0, column=0, padx=6)
        self.interval_spin = ttk.Spinbox(self.settings_frame, from_=500, to=5000, 
                                       increment=100, width=8, font=('Consolas', 10))
        
        # 推送间隔
        ttk.Label(self.settings_frame, text="推送间隔(ms):", style='Frame.TLabel').grid(row=0, column=2, padx=6)
        self.push_interval_entry = ttk.Entry(self.settings_frame, width=8, font=('Consolas', 10))
        
        # 默认设置值
        self.interval_spin.set(1000)
        self.push_interval_entry.insert(0, "0")
    
    def _create_keyword_section(self):
        """创建关键词管理区域"""
        self.keywords_frame = ttk.LabelFrame(self.root, text="关键词管理")
        
        # 输入框和按钮
        self.keyword_entry = ttk.Entry(self.keywords_frame, font=('微软雅黑', 10))
        self.add_btn = ttk.Button(self.keywords_frame, text="➕ 添加", command=self.add_keyword)
        self.clear_kw_btn = ttk.Button(self.keywords_frame, text="🔄 清空", command=self.clear_keywords)
        
        # 关键词列表
        self.keyword_list = Listbox(self.keywords_frame, height=6, font=('微软雅黑', 10), 
                                  selectmode=SINGLE, bg="white", 
                                  relief='solid', borderwidth=1,
                                  activestyle='none')
    
    def _create_wxpusher_section(self):
        """创建WxPusher配置区域"""
        self.wxpusher_frame = ttk.LabelFrame(self.root, text="WxPusher配置")
        
        # AppToken
        ttk.Label(self.wxpusher_frame, text="App Token:", style='Frame.TLabel').grid(row=0, column=0, padx=6, sticky="w")
        self.app_token_entry = ttk.Entry(self.wxpusher_frame, width=50, font=('Consolas', 10))
        
        # UID
        ttk.Label(self.wxpusher_frame, text="用户UID:", style='Frame.TLabel').grid(row=1, column=0, padx=6, sticky="w")
        self.uid_entry = ttk.Entry(self.wxpusher_frame, width=50, font=('Consolas', 10))
        
        # 添加测试按钮
        self.test_btn = ttk.Button(self.wxpusher_frame, text="🔔 测试", command=self.test_wxpusher,
                                  width=8)
    
    def _create_log_section(self):
        """创建日志区域"""
        self.log_frame = ttk.LabelFrame(self.root, text="触发日志")
        
        # 这个容器会在setup_layout中进行布局
    
    def _create_control_section(self):
        """创建控制按钮区域"""
        self.control_frame = ttk.Frame(self.root)
        
        # 主要控制按钮
        self.start_btn = ttk.Button(self.control_frame, text="▶️ 开始监控", 
                                   command=self.toggle_monitor)
        self.save_btn = ttk.Button(self.control_frame, text="💾 保存设置",
                                  command=self.save_config)

    def setup_layout(self):
        """设置界面布局"""
        # 状态栏布局
        self.status_bar.grid(row=6, column=0, sticky='ew', padx=12, pady=4)
        
        # 各区域布局
        self._layout_file_section()
        self._layout_settings_section() 
        self._layout_keywords_section()
        self._layout_wxpusher_section()
        self._layout_log_section()
        self._layout_control_section()
        
        # 主窗口布局权重配置
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=3)  # 增大日志区域的权重
        
        # 配置区域内权重
        self.file_frame.columnconfigure(1, weight=1)
        self.keywords_frame.columnconfigure(0, weight=1)
        self.wxpusher_frame.columnconfigure(1, weight=1)
    
    def _layout_file_section(self):
        """布局文件配置区域"""
        self.file_frame.grid(row=0, column=0, padx=12, pady=6, sticky="ew")
        self.file_entry.grid(row=0, column=1, padx=6, sticky="ew")
        self.browse_btn.grid(row=0, column=2, padx=6)
    
    def _layout_settings_section(self):
        """布局监控设置区域"""
        self.settings_frame.grid(row=1, column=0, padx=12, pady=6, sticky="ew")
        self.interval_spin.grid(row=0, column=1, padx=6)
        self.push_interval_entry.grid(row=0, column=3, padx=6)
    
    def _layout_keywords_section(self):
        """布局关键词管理区域"""
        self.keywords_frame.grid(row=2, column=0, padx=12, pady=6, sticky="ew")
        self.keyword_entry.grid(row=0, column=0, padx=6, pady=3, sticky="ew")
        self.add_btn.grid(row=0, column=1, padx=3)
        self.clear_kw_btn.grid(row=0, column=2, padx=3)
        self.keyword_list.grid(row=1, column=0, columnspan=3, padx=6, pady=3, sticky="ew")
    
    def _layout_wxpusher_section(self):
        """布局WxPusher配置区域"""
        self.wxpusher_frame.grid(row=3, column=0, padx=12, pady=6, sticky="ew")
        self.app_token_entry.grid(row=0, column=1, padx=6, sticky="ew")
        self.uid_entry.grid(row=1, column=1, padx=6, sticky="ew")
        self.test_btn.grid(row=0, column=2, rowspan=2, padx=6, sticky="ns")
    
    def _layout_log_section(self):
        """布局日志区域"""
        # 外层框架
        self.log_frame.grid(row=4, column=0, padx=12, pady=6, sticky="nsew")
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)

        # 日志容器
        log_container = Frame(self.log_frame, bg="white", relief="solid", bd=1)
        log_container.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        log_container.columnconfigure(0, weight=1)  # 文本区域占据大部分空间
        log_container.columnconfigure(1, weight=0)  # 按钮区域不占用额外空间
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
            style='TButton', width=9
        )
        self.clear_log_btn.pack(side=TOP, padx=5, pady=5, fill=X)

        self.export_log_btn = ttk.Button(
            right_panel, text="导出", command=self.export_log, 
            style='TButton', width=9
        )
        self.export_log_btn.pack(side=TOP, padx=5, pady=5, fill=X)
    
    def _layout_control_section(self):
        """布局控制按钮区域"""
        self.control_frame.grid(row=5, column=0, pady=12, sticky="ew")
        self.start_btn.pack(side="left", padx=6)
        self.save_btn.pack(side="right", padx=6)

    def setup_bindings(self):
        """设置事件绑定"""
        # 快捷键绑定
        self.root.bind('<Control-s>', lambda e: self.save_config())
        self.root.bind('<Control-q>', lambda e: self.on_close())
        self.root.bind('<Escape>', lambda e: self.toggle_window())
        
        # 窗口事件绑定
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.root.bind('<Unmap>', self.on_minimize)
        
        # 设置回车键绑定
        self.keyword_entry.bind('<Return>', lambda e: self.add_keyword())
        
        # 设置关键词列表事件
        self._setup_keyword_menu()
        self.keyword_list.bind('<Double-Button-1>', lambda e: self.edit_keyword())
    
    def _setup_keyword_menu(self):
        """设置关键词右键菜单"""
        # 创建菜单
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
        
        # 绑定右键菜单
        self.keyword_list.bind('<Button-3>', self.show_keyword_menu)

    def setup_tray(self):
        """初始化系统托盘"""
        self.is_minimized = False
        try:
            # 尝试加载或创建图标
            image = self._create_tray_icon()
            
            # 创建托盘菜单
            menu = pystray.Menu(lambda: (
                pystray.MenuItem("显示/隐藏", self.toggle_window, default=True),
                pystray.MenuItem("启动监控", self.start_monitoring),
                pystray.MenuItem("停止监控", self.stop_monitoring),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self.quit_app)
            ))
            
            # 创建托盘图标
            self.tray_icon = pystray.Icon(
                "POE2TradePusher",
                image,
                "POE2 Trade Pusher",
                menu
            )
            
            # 在单独的线程中运行托盘图标
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"托盘初始化失败: {str(e)}", "ERROR")
    
    def _create_tray_icon(self):
        """创建托盘图标"""
        icon_path = os.path.join('assets', 'icon.ico')
        if os.path.exists(icon_path):
            image = PIL.Image.open(icon_path)
            image = image.resize((32, 32), PIL.Image.Resampling.LANCZOS)
            return image
        else:
            # 创建默认图标
            image = PIL.Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            draw = PIL.ImageDraw.Draw(image)
            draw.ellipse((2, 2, 30, 30), fill='#07C160')
            
            # 加载字体
            try:
                font = PIL.ImageFont.truetype("arial", 12)
            except:
                font = PIL.ImageFont.load_default()
                
            # 添加文字
            draw.text((8, 8), "P2", fill='white', font=font)
            self.log_message("使用默认图标", "INFO")
            return image

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    
                # 更新界面
                self._apply_config_to_ui()
                self.log_message("配置加载完成")
            else:
                self.log_message("未找到配置文件，将使用默认设置")
        except Exception as e:
            self.log_message(f"配置加载失败: {str(e)}", "ERROR")
    
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
        """保存配置到文件"""
        try:
            config = {
                'interval': int(self.interval_spin.get()),
                'push_interval': int(self.push_interval_entry.get() or 0),
                'app_token': self.app_token_entry.get(),
                'uid': self.uid_entry.get(),
                'keywords': list(self.keyword_list.get(0, END)),
                'log_path': self.file_entry.get()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            self.config = config  # 更新内存中的配置
            self.log_message("配置保存成功")
            self.status_bar.config(text="✅ 配置已保存")
            
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
        if not self.validate_settings():
            return
            
        try:
            # 初始化监控状态
            file_path = self.file_entry.get()
            if os.path.exists(file_path):
                self.last_position = os.path.getsize(file_path)
                self.last_timestamp = self.get_last_timestamp(file_path)
                
            # 更新状态
            self.monitoring = True
            self.stop_event.clear()
            self.start_btn.config(text="⏹ 停止监控", style='Stop.TButton')
            self.status_bar.config(text="✅ 监控进行中...")
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            self.log_message("监控已启动")
        except Exception as e:
            self.log_message(f"启动监控失败: {str(e)}", "ERROR")
            self.monitoring = False
    
    def _stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.stop_event.set()
        self.start_btn.config(text="▶ 开始监控", style='TButton')
        self.status_bar.config(text="⏸️ 监控已停止")
        self.log_message("监控已停止")

    def validate_settings(self):
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

    def monitor_loop(self):
        """监控日志文件循环"""
        self.push_interval = int(self.push_interval_entry.get() or 0)
        self.log_message(f"检测间隔: {self.interval_spin.get()}ms, 推送间隔: {self.push_interval}ms", "INFO")
        
        while self.monitoring and not self.stop_event.is_set():
            try:
                self._process_log_file()
                
                # 休眠指定的检测间隔
                time.sleep(int(self.interval_spin.get()) / 1000)
                
            except Exception as e:
                if self.monitoring:
                    self.log_message(f"监控异常: {str(e)}", "ERROR")
                    self.log_message(traceback.format_exc(), "DEBUG")
                time.sleep(1)
    
    def _process_log_file(self):
        """处理日志文件更新"""
        file_path = self.file_entry.get()
        
        # 检查文件存在
        if not os.path.exists(file_path):
            self.log_message("日志文件不存在，停止监控", "ERROR")
            self.toggle_monitor()
            return

        current_size = os.path.getsize(file_path)
        
        # 处理文件截断
        if current_size < self.last_position:
            self.log_message("检测到文件被截断，重置读取位置", "WARN")
            self.last_position = 0
            self.last_timestamp = None

        # 读取新增内容
        if self.last_position < current_size:
            with open(file_path, 'rb') as f:
                f.seek(self.last_position)
                content = f.read()
                self.last_position = f.tell()
                
                # 解码内容
                try:
                    decoded = self.decode_content(content)
                except UnicodeDecodeError as ude:
                    self.log_message(f"解码失败: {str(ude)}，尝试重新检测编码...", "WARN")
                    if self.detect_encoding(file_path):
                        decoded = self.decode_content(content)
                    else:
                        return

                # 处理日志行
                self._process_log_lines(decoded)

    def _process_log_lines(self, content):
        """处理日志内容"""
        # 分割
        lines = content.replace('\r\n', '\n').split('\n')
        valid_lines = []
        
        # 时间戳过滤
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_timestamp = self.parse_timestamp(line)
            
            # 首次运行记录所有有效行
            if not self.last_timestamp:
                if line_timestamp:
                    self.last_timestamp = line_timestamp
                valid_lines.append(line)
                continue
            
            # 只处理新时间戳日志
            if line_timestamp and line_timestamp > self.last_timestamp:
                valid_lines.append(line)

        # 更新最后时间戳
        if valid_lines:
            last_line = valid_lines[-1]
            new_timestamp = self.parse_timestamp(last_line)
            if new_timestamp:
                self.last_timestamp = new_timestamp
            elif self.last_timestamp:  # 没有时间戳时使用最后位置
                self.last_timestamp = datetime.now()

        # 处理有效日志
        if valid_lines:
            self.log_message(f"发现 {len(valid_lines)} 条新日志", "INFO")
            self.process_lines(valid_lines)

    def detect_encoding(self, file_path):
        """增强的编码检测方法"""
        try:
            with open(file_path, 'rb') as f:
                rawdata = f.read(10000)
                
                # 使用中文优先策略
                result = chardet.detect(rawdata)
                if result['encoding'] and 'gb' in result['encoding'].lower():
                    self.current_encoding = result['encoding']
                else:
                    # 尝试所有备选编码
                    for enc in ['utf-8-sig', 'gb18030', 'gbk', 'big5'] + self.fallback_encodings:
                        try:
                            rawdata.decode(enc)
                            self.current_encoding = enc
                            break
                        except:
                            continue
                
                # 验证编码有效性
                test_str = rawdata[:100].decode(self.current_encoding, errors='replace')
                if '�' in test_str:
                    raise UnicodeDecodeError("检测到替换字符，编码可能不正确")
                
                self.log_message(f"最终使用编码: {self.current_encoding}")
                return True
        except Exception as e:
            self.log_message(f"编码检测失败: {str(e)}，使用备选编码", "ERROR")
            self.current_encoding = 'gb18030'  # 中文最通用编码
            return False

    def decode_content(self, content):
        """多重编码尝试解码"""
        try:
            return content.decode(self.current_encoding)
        except UnicodeDecodeError:
            for enc in self.fallback_encodings:
                try:
                    return content.decode(enc)
                except:
                    continue
            return content.decode(self.current_encoding, errors='replace')

    def process_lines(self, lines):
        """处理日志条目（带推送间隔控制）"""
        current_time = time.time() * 1000  # 毫秒
        for line in lines:
            if self.stop_event.is_set():
                break
            
            # 推送间隔检查
            if self.push_interval > 0 and (current_time - self.last_push_time) < self.push_interval:
                continue

            # 提取内容
            content = self.extract_content(line)
            
            # 关键词匹配
            for kw in self.keyword_list.get(0, END):
                if kw in line:
                    self.send_wxpush(kw, content)
                    self.last_push_time = time.time() * 1000  # 更新推送时间
                    break

    def extract_content(self, line):
        """增强的内容提取方法"""
        markers = ['@來自', '@来自']  # 支持简繁体
        for marker in markers:
            index = line.find(marker)
            if index != -1:
                # 提取冒号后的内容（如果存在）
                colon_index = line.find(':', index)
                if colon_index != -1:
                    return line[colon_index+1:].trip()
                # 如果没有冒号，直接取标记后的内容
                return line[index + len(marker):].strip()
        return line

    def select_file(self):
        """选择文件时初始化时间戳"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_entry.delete(0, END)
            self.file_entry.insert(0, file_path)
            self.last_position = os.path.getsize(file_path)
            self.last_timestamp = self.get_last_timestamp(file_path)
            try:
                self.last_size = os.path.getsize(file_path)
                with open(file_path, 'rb') as f:
                    rawdata = f.read(10000)
                    result = chardet.detect(rawdata)
                    self.current_encoding = result['encoding'] or 'utf-8'
                    self.log_message(f"文件编码检测为: {self.current_encoding}")
            except Exception as e:
                self.log_message(f"文件初始化失败: {str(e)}", "ERROR")

    def get_last_timestamp(self, file_path):
        """获取文件的最后有效时间戳"""
        try:
            with open(file_path, 'rb') as f:
                f.seek(-10240, os.SEEK_END)  # 读取最后10KB内容
                content = f.read().decode(self.current_encoding, errors='ignore')
                for line in reversed(content.splitlines()):
                    ts = self.parse_timestamp(line)
                    if ts:
                        return ts
        except:
            pass
        return None

    def send_wxpush(self, keyword, content):
        """发送WXPUSHER推送"""
        message = f"🔔 日志报警 [{keyword}]\n{content}"
        self.log_message(f"推送内容: {message}", "ALERT")
        try:
            response = requests.post(
                "http://wxpusher.zjiecode.com/api/send/message",
                json={
                    "appToken": self.app_token_entry.get(),
                    "content": message,
                    "contentType": 1,
                    "uids": [self.uid_entry.get()]
                },
                timeout=10
            )
            result = response.json()
            if result["code"] != 1000:
                raise Exception(result["msg"])
            self.log_message("推送成功", "INFO")
        except Exception as e:
            self.log_message(f"推送失败: {str(e)}", "ERROR")

    def show_keyword_menu(self, event):
        """显示关键词右键菜单"""
        if self.keyword_list.size() > 0:
            selection = self.keyword_list.curselection()
            if selection:  # 只在选中项目时显示菜单
                self.keyword_menu.post(event.x_root, event.y_root)

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

    def update_status(self, message, duration=3000):
        """更新状态栏信息"""
        self.status_bar.config(text=message)
        self.root.after(duration, lambda: self.status_bar.config(text="就绪"))

    def log_message(self, message, level="INFO"):
        """添加消息到日志区域"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        color_map = {
            "INFO": "#333333",
            "DEBUG": "#666666",
            "WARN": "#d35400",
            "ERROR": "#c0392b",
            "ALERT": "#8e44ad"
        }
        
        # 将日志区域设置为可编辑
        self.log_area.configure(state='normal')
        
        # 配置标签颜色
        self.log_area.tag_configure(level, foreground=color_map.get(level, "#333333"))
        
        # 插入日志条目
        self.log_area.insert(END, f"[{timestamp}] [{level}] {message}\n", level)
        
        # 返回只读状态
        self.log_area.configure(state='disabled')
        
        # 自动滚动到底部
        self.log_area.see(END)
        
        # 强制更新UI
        self.root.update_idletasks()

    def clear_log(self):
        """清空日志区域"""
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, END)
        self.log_area.configure(state='disabled')
        self.status_bar.config(text="日志已清空")

    def add_keyword(self):
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
        selection = self.keyword_list.curselection()
        if selection:
            keyword = self.keyword_list.get(selection[0])
            self.keyword_list.delete(selection[0])
            self.log_message(f"已移除关键词: {keyword}")

    def clear_keywords(self):
        """清空关键词带自定义确认对话框"""
        dialog = Toplevel(self.root)
        dialog.title("确认清空")
        dialog.geometry("300x140")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg='white')
        
        main_frame = ttk.Frame(dialog, style='Dialog.TFrame')
        main_frame.pack(expand=True, fill='both', padx=2, pady=2)
        
        ttk.Label(main_frame, text="确定要清空所有关键词吗？\n\n此操作无法撤销",
                 font=('微软雅黑', 9), wraplength=250).pack(padx=20, pady=(15, 10))
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(0, 10))
        
        result = BooleanVar(value=False)
        
        ttk.Button(btn_frame, text="✔️ 确定", command=lambda: (result.set(True), dialog.destroy()),
                  style='Dialog.TButton').pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ 取消", command=dialog.destroy,
                  style='Dialog.TButton').pack(side=LEFT, padx=5)

        # 居中对话框
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')
        
        dialog.bind('<Return>', lambda e: (result.set(True), dialog.destroy()))
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.focus_set()

        # 等待对话框关闭
        dialog.wait_window()
        
        if result.get():
            self.keyword_list.delete(0, END)
            self.log_message("已清空关键词列表")
            self.status_bar.config(text="✨ 已清空关键词列表")

    def on_minimize(self, event):
        """处理窗口最小化事件"""
        if not self.is_minimized:
            self.root.withdraw()
            self.is_minimized = True

    def toggle_window(self, icon=None, item=None):
        """切换窗口显示状态"""
        if self.is_minimized:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.is_minimized = False
        else:
            self.root.withdraw()
            self.is_minimized = True

    def start_monitoring(self, icon=None, item=None):
        """从托盘菜单启动监控"""
        if not self.monitoring:
            self.toggle_monitor()

    def stop_monitoring(self, icon=None, item=None):
        """从托盘菜单停止监控"""
        if self.monitoring:
            self.toggle_monitor()

    def quit_app(self, icon=None, item=None):
        """退出应用程序"""
        if self.monitoring:
            self.toggle_monitor()  # 停止监控
        self.tray_icon.stop()  # 删除托盘图标
        self.root.quit()

    def on_close(self):
        """处理窗口关闭事件"""
        # 创建自定义消息框样式
        dialog = Toplevel(self.root)
        dialog.title("确认")
        dialog.geometry("300x140")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg='white')
        
        main_frame = ttk.Frame(dialog, style='Dialog.TFrame')
        main_frame.pack(expand=True, fill='both', padx=2, pady=2)
        
        ttk.Label(main_frame, text="是否要最小化到系统托盘？\n\n选择\"否\"将退出程序",
                 font=('微软雅黑', 9), wraplength=250).pack(padx=20, pady=(15, 10))
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(0, 10))
        
        result = BooleanVar(value=True)
        
        ttk.Button(btn_frame, text="✔️ 是", command=lambda: (result.set(True), dialog.destroy()),
                  style='Dialog.TButton').pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ 否", command=lambda: (result.set(False), dialog.destroy()),
                  style='Dialog.TButton').pack(side=LEFT, padx=5)

        # 居中对话框
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')
        
        dialog.focus_set()
        dialog.wait_window()
        
        if result.get():
            self.root.withdraw()
            self.is_minimized = True
        else:
            self.quit_app()

    def test_wxpusher(self):
        """测试WxPusher推送"""
        self.send_wxpush("测试", "这是一条测试消息")

if __name__ == "__main__":
    root = Tk()
    app = AdvancedLogMonitorPro(root)
    root.mainloop()