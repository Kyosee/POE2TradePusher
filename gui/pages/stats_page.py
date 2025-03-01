from tkinter import *
from tkinter import ttk

from PIL import Image, ImageTk
import os
import sys

class StatsPage(ttk.Frame):
    def __init__(self, master, callback_log, callback_status, callback_save=None):
        super().__init__(master, style='Content.TFrame')
        self.log_message = callback_log
        self.status_bar = callback_status
        self.save_config = callback_save
        
        self.currency_stats = {}  # 存储通货统计数据
        self.trade_message_count = 0  # 交易消息计数
        self.configured_currencies = []  # 已配置的通货单位
        
        # 创建统计区域
        self._create_stats_frame()
        
        # 统计重置按钮（界面最右上角）
        self.clear_btn = ttk.Button(self, text="统计重置", 
                                  command=self.clear_stats,
                                  style='Control.Stop.TButton')
        self.clear_btn.place(relx=1.0, rely=0, anchor=NE, x=-12, y=12)
        
        # 初始化显示
        self.refresh_stats_display()
        
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
        
        # 刷新显示（会显示所有已配置的通货单位，计数为0）
        self.refresh_stats_display()
        
        self.log_message("已清除统计数据")
        if callable(self.status_bar):
            self.status_bar("✨ 已清除统计数据")
        
        # 保存配置
        if self.save_config:
            self.save_config()
            
    def _get_resource_path(self, filename):
        """获取资源文件路径"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, "assets", "orb", filename)

    def refresh_stats_display(self):
        """刷新统计显示"""
        # 清除现有显示
        for widget in self.currency_frame_inner.winfo_children():
            widget.destroy()
            
        # 获取最新的配置通货单位和统计数据
        if hasattr(self.master, 'get_currency_config'):
            self.configured_currencies = self.master.get_currency_config()
        
        # 获取所有需要显示的通货
        currencies = set(self.currency_stats.keys())
        currencies.update(self.configured_currencies)
        
        # 重新创建显示项
        for currency in sorted(currencies):
            frame = ttk.Frame(self.currency_frame_inner, style='Currency.TFrame', height=34)
            frame.pack(fill=X, padx=6, pady=(0, 1))
            frame.pack_propagate(False)
            
            # 通货图标容器
            img_frame = ttk.Frame(frame, width=30, height=30)
            img_frame.pack(side=LEFT, padx=1)
            img_frame.pack_propagate(False)
            
            # 通货图标
            img_label = Label(img_frame, width=30, height=30)
            img_path = self._get_resource_path(f"{currency.lower()}.png")
            
            try:
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    img = img.resize((30, 30), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_label.configure(image=photo)
                    img_label.image = photo
            except Exception as e:
                self.log_message(f"加载图片失败: {e}", "ERROR")
                
            img_label.pack(side=LEFT, padx=2)
            
            # 通货名称
            ttk.Label(frame, text=currency,
                     font=('微软雅黑', 10)).pack(side=LEFT, fill=X, expand=True, padx=2)
            
            # 计数（右对齐）
            count = self.currency_stats.get(currency, 0)
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
        
        # 重新获取已配置的通货单位
        if hasattr(self.master, 'get_currency_config'):
            self.configured_currencies = self.master.get_currency_config()
            
        # 更新显示
        self.message_count_label.config(text=str(self.trade_message_count))
        self.refresh_stats_display()
