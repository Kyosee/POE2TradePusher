from tkinter import *
from tkinter import ttk
from ..utils import LoggingMixin, ConfigMixin, show_message
from ..widgets.dialog import MessageDialog

class ProcessConfigPage(ttk.Frame, LoggingMixin, ConfigMixin):
    """流程配置页面"""
    def __init__(self, master, log_callback, status_callback, callback_save=None):
        ttk.Frame.__init__(self, master, style='Content.TFrame')
        LoggingMixin.__init__(self, log_callback, status_callback)
        self.init_config()
        self.save_config = callback_save
        
        # 创建界面组件
        self._create_process_frame()
        
    def _create_process_frame(self):
        """创建流程配置区域"""
        # 创建处理间隔配置框架
        self.interval_frame = ttk.LabelFrame(self, text="处理间隔配置")
        self.interval_frame.pack(fill=X, padx=12, pady=6)
        
        # 添加处理间隔配置
        ttk.Label(self.interval_frame, text="处理间隔(ms):", style='Frame.TLabel').grid(row=0, column=0, padx=6)
        self.process_interval_spin = ttk.Spinbox(self.interval_frame, from_=100, to=1000, 
                                               increment=100, width=8, font=('Consolas', 10))
        self.process_interval_spin.set(200)
        self.process_interval_spin.grid(row=0, column=1, padx=6)
        
        # 创建按键设置框架
        self.key_frame = ttk.LabelFrame(self, text="按键设置")
        self.key_frame.pack(fill=X, padx=12, pady=6)
        
        # 添加按键配置
        ttk.Label(self.key_frame, text="鼠标移动后延时(ms):", style='Frame.TLabel').grid(row=0, column=0, padx=6)
        self.mouse_delay_spin = ttk.Spinbox(self.key_frame, from_=0, to=500,
                                          increment=50, width=8, font=('Consolas', 10))
        self.mouse_delay_spin.set(100)
        self.mouse_delay_spin.grid(row=0, column=1, padx=6)
        
        ttk.Label(self.key_frame, text="按键延时(ms):", style='Frame.TLabel').grid(row=1, column=0, padx=6, pady=(6,0))
        self.key_delay_spin = ttk.Spinbox(self.key_frame, from_=0, to=500,
                                        increment=50, width=8, font=('Consolas', 10))
        self.key_delay_spin.set(50)
        self.key_delay_spin.grid(row=1, column=1, padx=6, pady=(6,0))
        
        # 创建按键序列框架
        self.sequence_frame = ttk.LabelFrame(self, text="按键序列")
        self.sequence_frame.pack(fill=BOTH, expand=True, padx=12, pady=6)
        
        # 添加按键序列说明
        help_text = """按键序列说明：
1. 每行一个操作，格式为：动作 参数
2. 支持的动作：
   - MOVE x y: 移动鼠标到指定坐标
   - CLICK: 点击鼠标左键
   - KEY key: 模拟按下指定按键
   - DELAY ms: 等待指定毫秒数
3. 示例：
   MOVE 100 200
   CLICK
   KEY enter
   DELAY 500"""
        
        self.help_text = Text(self.sequence_frame, height=6, font=('Consolas', 9),
                            bg='#F8F9FA', relief='flat', padx=8, pady=8)
        self.help_text.pack(fill=X, padx=6, pady=(6,0))
        self.help_text.insert('1.0', help_text)
        self.help_text.configure(state='disabled')
        
        # 添加序列编辑区
        self.sequence_text = Text(self.sequence_frame, height=8, font=('Consolas', 10),
                                bg='white', relief='solid', borderwidth=1, padx=8, pady=8)
        self.sequence_text.pack(fill=BOTH, expand=True, padx=6, pady=6)
        
        # 绑定事件
        self.process_interval_spin.bind('<KeyRelease>', lambda e: self._on_settings_change())
        self.process_interval_spin.bind('<ButtonRelease-1>', lambda e: self._on_settings_change())
        self.mouse_delay_spin.bind('<KeyRelease>', lambda e: self._on_settings_change())
        self.mouse_delay_spin.bind('<ButtonRelease-1>', lambda e: self._on_settings_change())
        self.key_delay_spin.bind('<KeyRelease>', lambda e: self._on_settings_change())
        self.key_delay_spin.bind('<ButtonRelease-1>', lambda e: self._on_settings_change())
        self.sequence_text.bind('<KeyRelease>', lambda e: self._on_settings_change())
        
    def _on_settings_change(self, *args):
        """处理设置变化"""
        if self.save_config:
            self.save_config()
            
    def validate_config(self):
        """验证配置"""
        data = self.get_config_data()
        
        try:
            interval = int(data.get('process_interval', 0))
            if interval < 100 or interval > 1000:
                return False, "处理间隔必须在100-1000毫秒之间"
        except ValueError:
            return False, "无效的处理间隔值"
            
        try:
            mouse_delay = int(data.get('mouse_delay', 0))
            if mouse_delay < 0 or mouse_delay > 500:
                return False, "鼠标移动延时必须在0-500毫秒之间"
        except ValueError:
            return False, "无效的鼠标移动延时值"
            
        try:
            key_delay = int(data.get('key_delay', 0))
            if key_delay < 0 or key_delay > 500:
                return False, "按键延时必须在0-500毫秒之间"
        except ValueError:
            return False, "无效的按键延时值"
            
        if not data.get('sequence', '').strip():
            return False, "请添加至少一个按键序列操作"
            
        return True, None
        
    def get_config_data(self):
        """获取配置数据"""
        return {
            'process_interval': int(self.process_interval_spin.get()),
            'mouse_delay': int(self.mouse_delay_spin.get()),
            'key_delay': int(self.key_delay_spin.get()),
            'sequence': self.sequence_text.get('1.0', END).strip()
        }
        
    def set_config_data(self, data):
        """设置配置数据"""
        self.process_interval_spin.set(data.get('process_interval', 200))
        self.mouse_delay_spin.set(data.get('mouse_delay', 100))
        self.key_delay_spin.set(data.get('key_delay', 50))
        
        self.sequence_text.delete('1.0', END)
        self.sequence_text.insert('1.0', data.get('sequence', ''))
