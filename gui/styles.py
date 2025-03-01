from tkinter import ttk

class Styles:
    """GUI样式管理类"""
    
    def __init__(self):
        # 界面主题颜色
        self.wx_green = '#07C160'
        self.wx_bg = '#f0f0f0'
        self.wx_hover = '#06AD56'
        self.wx_text = '#2C2C2C'
        self.wx_border = '#E6E7E8'
        
        # iOS Switch颜色
        self.switch_off = '#e9e9ea'      # 关闭状态背景色
        self.switch_thumb = '#ffffff'     # 滑块颜色
        self.switch_shadow = '#00000026'  # 滑块阴影颜色
        
        # 日志颜色映射
        self.log_colors = {
            "INFO": "#333333",
            "DEBUG": "#666666",
            "WARN": "#d35400",
            "ERROR": "#c0392b",
            "ALERT": "#8e44ad"
        }
        
    def setup(self, root):
        """配置应用程序样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # 基础样式
        self._configure_card_style()
        self._configure_button_styles()
        self._configure_text_styles()
        self._configure_frame_styles()
        self._configure_menu_style()
        
        # 设置主窗口背景
        root.configure(bg=self.wx_bg)
        
        # 设置列表框样式
        self._configure_listbox_style(root)
    
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
            padding=(13, 7),
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
            
        # 保存按钮
        self.style.configure('Save.TButton',
            background='#1890ff',
            foreground='white')
            
        self.style.map('Save.TButton',
            background=[('active', '#40a9ff'), ('disabled', '#E0E0E0')])
            
        # 对话框按钮
        self.style.configure('Dialog.TButton',
            padding=(10, 5),
            font=('微软雅黑', 9))
            
        # 控制按钮
        self.style.configure('Control.TButton',
            padding=(20, 7),
            font=('微软雅黑', 10),
            background=self.wx_green,
            foreground='white',
            borderwidth=0,
            relief='flat')
            
        self.style.map('Control.TButton',
            background=[('active', self.wx_hover), ('disabled', '#E0E0E0')])
            
        # 继承Control.TButton的所有属性，只修改颜色
        self.style.configure('Control.Stop.TButton', background='#ff4d4f')
        self.style.map('Control.Stop.TButton', background=[('active', '#ff7875'), ('disabled', '#E0E0E0')])
            
        self.style.configure('Control.Save.TButton', background='#1890ff')
        self.style.map('Control.Save.TButton', background=[('active', '#40a9ff'), ('disabled', '#E0E0E0')])
    
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
            background='white',
            padding=(0, 0, 12, 0))  # 右侧添加12像素间距
            
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
            
        # iOS7风格Switch开关
        self.style.configure('Switch.TCheckbutton',
            background='white',
            foreground=self.wx_text,
            font=('微软雅黑', 10),
            indicatorsize=28,          # 开关大小
            indicatormargin=2,         # 滑块边距
            padding=(0, 4),            # 整体内边距
            relief='flat',             # 扁平风格
            borderwidth=0)             # 无边框
            
        self.style.map('Switch.TCheckbutton',
            background=[('active', 'white'), ('selected', 'white')],
            foreground=[('active', self.wx_text), ('selected', self.wx_text)],
            indicatorcolor=[           # 开关背景颜色
                ('!selected', self.switch_off), 
                ('selected', self.wx_green),
                ('active !selected', self.switch_off),
                ('active selected', self.wx_green)
            ],
            indicatorrelief=[('!selected', 'round'), ('selected', 'round')],  # 圆角效果
            indicatorbackground=[      # 滑块颜色
                ('!selected', self.switch_thumb),
                ('selected', self.switch_thumb),
                ('pressed !selected', self.switch_thumb),
                ('pressed selected', self.switch_thumb),
                ('active !selected', self.switch_thumb),
                ('active selected', self.switch_thumb)
            ])
    
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
    
    def _configure_listbox_style(self, root):
        """配置列表样式"""
        root.option_add('*TListbox*background', 'white')
        root.option_add('*TListbox*foreground', self.wx_text)
        root.option_add('*TListbox*selectBackground', self.wx_green)
        root.option_add('*TListbox*selectForeground', 'white')
        root.option_add('*TListbox*selectBackground', '#E7F7EE')
        root.option_add('*TListbox*selectForeground', '#07C160')
        
    def _configure_menu_style(self):
        """配置左侧菜单样式"""
        self.style.configure('Menu.TFrame',
            background=self.wx_bg,
            relief='flat')
            
        self.style.configure('Menu.TButton',
            font=('微软雅黑', 10),
            padding=(20, 12),
            background=self.wx_bg,
            foreground=self.wx_text,
            borderwidth=0,
            relief='flat')
            
        self.style.map('Menu.TButton',
            background=[('active', 'white'), ('selected', 'white'), ('!selected', self.wx_bg)],
            foreground=[('active', self.wx_green), ('selected', self.wx_green), ('!selected', self.wx_text)])
            
        self.style.configure('Content.TFrame',
            background='white',
            relief='flat')
