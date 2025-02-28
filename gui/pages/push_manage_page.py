from tkinter import *
from tkinter import ttk

class PushManagePage(ttk.Frame):
    def __init__(self, master, callback_log, callback_status):
        super().__init__(master, style='Content.TFrame')
        self.log_message = callback_log
        self.status_bar = callback_status
        
        self._create_wxpusher_frame()
        
    def _create_wxpusher_frame(self):
        """创建WxPusher配置区域"""
        self.wxpusher_frame = ttk.LabelFrame(self, text="WxPusher配置")
        
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
        
    def test_wxpusher(self):
        """提供给外部调用的测试方法"""
        self.log_message("正在测试WxPusher配置...", "INFO")
        
    def get_data(self):
        """获取页面数据"""
        return {
            'app_token': self.app_token_entry.get(),
            'uid': self.uid_entry.get()
        }
        
    def set_data(self, data):
        """设置页面数据"""
        self.app_token_entry.delete(0, END)
        self.app_token_entry.insert(0, data.get('app_token', ''))
        
        self.uid_entry.delete(0, END)
        self.uid_entry.insert(0, data.get('uid', ''))
