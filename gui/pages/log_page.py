from tkinter import *
from tkinter import ttk, filedialog, scrolledtext
import time

class LogPage(ttk.Frame):
    def __init__(self, master, callback_log, callback_status):
        super().__init__(master, style='Content.TFrame')
        self.log_message = callback_log
        self.status_bar = callback_status
        
        self._create_log_area()
        
    def _create_log_area(self):
        """创建日志区域"""
        # 日志容器
        log_container = Frame(self, bg="white", relief="solid", bd=1)
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
        
    def append_log(self, message, level="INFO"):
        """添加日志条目"""
        # 将日志区域设置为可编辑
        self.log_area.configure(state='normal')
        
        # 配置标签颜色
        self.log_area.tag_configure(level, foreground=self._get_level_color(level))
        
        # 插入日志条目
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_area.insert(END, f"[{timestamp}] [{level}] {message}\n", level)
        
        # 返回只读状态
        self.log_area.configure(state='disabled')
        
        # 自动滚动到底部
        self.log_area.see(END)
        
    def _get_level_color(self, level):
        """获取日志级别对应的颜色"""
        colors = {
            "INFO": "#333333",
            "WARN": "#FF9800",
            "ERROR": "#F44336",
            "SUCCESS": "#4CAF50"
        }
        return colors.get(level, "#333333")
        
    def get_data(self):
        """获取页面数据"""
        # 日志页面不需要保存数据
        return {}
        
    def set_data(self, data):
        """设置页面数据"""
        # 日志页面不需要恢复数据
        pass
