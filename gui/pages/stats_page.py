from tkinter import *
from tkinter import ttk

class StatsPage(ttk.Frame):
    def __init__(self, master, callback_log, callback_status, callback_save=None):
        super().__init__(master, style='Content.TFrame')
        self.log_message = callback_log
        self.status_bar = callback_status
        self.save_config = callback_save
        
        self.currency_stats = {}  # 存储通货统计数据
        self.trade_message_count = 0  # 交易消息计数
        
        # 创建统计区域
        self._create_stats_frame()
        
    def _create_stats_frame(self):
        """创建统计区域"""
        # 交易消息数统计
        message_frame = ttk.LabelFrame(self, text="交易消息数")
        message_frame.pack(fill=X, padx=6, pady=3)
        
        self.message_count_label = ttk.Label(message_frame, 
                                           text="0", 
                                           font=('微软雅黑', 12, 'bold'))
        self.message_count_label.pack(padx=6, pady=3)
        
        # 交易消息通货统计
        currency_frame = ttk.LabelFrame(self, text="交易消息通货统计")
        currency_frame.pack(fill=BOTH, expand=True, padx=6, pady=3)
        
        # 容器框架
        container = ttk.Frame(currency_frame)
        container.pack(fill=BOTH, expand=True, padx=6, pady=3)
        
        # 创建Canvas和滚动条
        self.canvas = Canvas(container, bg="white",
                           relief='flat', borderwidth=0,
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                command=self.canvas.yview)
        
        self.currency_frame_inner = ttk.Frame(self.canvas)
        
        # 配置Canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.create_window((0, 0), window=self.currency_frame_inner,
                                anchor="nw", tags=("inner_frame",))
        
        # 布局
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # 绑定事件
        self.currency_frame_inner.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        
        # 清除数据按钮
        clear_btn = ttk.Button(self, text="清除数据", command=self.clear_stats)
        clear_btn.pack(pady=6)
        
    def _on_frame_configure(self, event=None):
        """处理内部frame大小变化"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _on_canvas_configure(self, event):
        """处理Canvas大小变化"""
        self.canvas.itemconfig("inner_frame", width=event.width)
        
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
    def update_currency_stats(self, currency, amount):
        """更新通货统计"""
        if currency in self.currency_stats:
            self.currency_stats[currency] += float(amount)
        else:
            self.currency_stats[currency] = float(amount)
        self.refresh_stats_display()
        
    def increment_message_count(self):
        """增加交易消息计数"""
        self.trade_message_count += 1
        self.message_count_label.config(text=str(self.trade_message_count))
        
    def clear_stats(self):
        """清除所有统计数据"""
        self.currency_stats.clear()
        self.trade_message_count = 0
        self.message_count_label.config(text="0")
        
        # 清除现有的通货统计显示
        for widget in self.currency_frame_inner.winfo_children():
            widget.destroy()
        
        self.log_message("已清除统计数据")
        self.status_bar.config(text="✨ 已清除统计数据")
        
        # 保存配置
        if self.save_config:
            self.save_config()
            
    def refresh_stats_display(self):
        """刷新统计显示"""
        # 清除现有显示
        for widget in self.currency_frame_inner.winfo_children():
            widget.destroy()
            
        # 重新创建显示项
        for currency, count in self.currency_stats.items():
            frame = ttk.Frame(self.currency_frame_inner, style='Currency.TFrame', height=34)
            frame.pack(fill=X, padx=6, pady=(0, 1))
            frame.pack_propagate(False)
            
            # 通货名称
            ttk.Label(frame, text=currency,
                     font=('微软雅黑', 10)).pack(side=LEFT, padx=6)
            
            # 计数（右对齐）
            ttk.Label(frame, text=f"{count:.1f}",
                     font=('微软雅黑', 10, 'bold')).pack(side=RIGHT, padx=6)
            
    def get_data(self):
        """获取页面数据"""
        return {
            'currency_stats': self.currency_stats,
            'trade_message_count': self.trade_message_count
        }
        
    def set_data(self, data):
        """设置页面数据"""
        self.currency_stats = data.get('currency_stats', {})
        self.trade_message_count = data.get('trade_message_count', 0)
        
        # 更新显示
        self.message_count_label.config(text=str(self.trade_message_count))
        self.refresh_stats_display()
