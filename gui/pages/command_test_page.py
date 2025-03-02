import tkinter as tk
from tkinter import ttk
from core.process_modules.game_command import GameCommandModule

class CommandTestPage(ttk.Frame):
    def __init__(self, parent, log_callback=None):
        super().__init__(parent)
        self.log_callback = log_callback if log_callback else lambda x, y: None
        self.game_command = GameCommandModule()
        self.game_command.logger.info = lambda x: self.log_callback(x, "INFO")
        self.game_command.logger.error = lambda x: self.log_callback(x, "ERROR")
        self.init_ui()

    def init_ui(self):
        # 创建命令输入框
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(input_frame, text="命令:").pack(side=tk.LEFT, padx=(0, 5))
        self.command_input = ttk.Entry(input_frame)
        self.command_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 添加测试按钮
        self.test_button = ttk.Button(input_frame, text="测试", command=self.on_test_clicked)
        self.test_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # 添加日志显示区域
        log_frame = ttk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建日志文本框
        self.log_display = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_display.config(yscrollcommand=scrollbar.set)
        
        # 设置只读
        self.log_display.config(state=tk.DISABLED)
    
    def add_log(self, message):
        """添加日志到显示区域"""
        self.log_display.config(state=tk.NORMAL)
        self.log_display.insert(tk.END, message + "\n")
        self.log_display.see(tk.END)
        self.log_display.config(state=tk.DISABLED)
    
    def on_test_clicked(self):
        """测试按钮点击事件处理"""
        command = self.command_input.get()
        if command:
            self.add_log(f"执行命令: {command}")
            result = self.game_command.run(command_text=command)
            if result:
                self.add_log("命令执行成功")
            else:
                self.add_log("命令执行失败")
