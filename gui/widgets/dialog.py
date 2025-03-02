import tkinter as tk
from tkinter import ttk

class BaseDialog:
    """基础对话框类，用于创建统一风格的对话框"""
    def __init__(self, parent, title, width=300, height=180):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg='white')
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.dialog, style='Dialog.TFrame')
        self.main_frame.pack(expand=True, fill='both', padx=2, pady=2)
        
        # 居中显示
        self.center_window()
        
        # 绑定Escape键关闭对话框
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        
    def center_window(self):
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'+{x}+{y}')
        
class MessageDialog(BaseDialog):
    """消息对话框，用于显示帮助信息等长文本内容"""
    def __init__(self, parent, title, message, width=600, height=400):
        super().__init__(parent, title, width, height)
        
        # 创建文本区域
        self.text = tk.Text(self.main_frame, wrap=tk.WORD, padx=10, pady=10,
                           font=('微软雅黑', 10))
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # 插入消息内容
        self.text.insert('1.0', message)
        self.text.config(state='disabled')
        
        # 确定按钮
        ttk.Button(self.main_frame, text="确定", 
                  command=self.dialog.destroy,
                  style='Dialog.TButton').pack(pady=10)
                  
class InputDialog(BaseDialog):
    """输入对话框，用于编辑单个值"""
    def __init__(self, parent, title, prompt, initial_value="", callback=None):
        super().__init__(parent, title)
        
        # 提示文本
        ttk.Label(self.main_frame, text=prompt,
                 font=('微软雅黑', 9)).pack(padx=10, pady=(10, 5))
        
        # 输入框
        self.entry = ttk.Entry(self.main_frame, width=40, font=('微软雅黑', 9))
        self.entry.insert(0, initial_value)
        self.entry.pack(padx=10, pady=(0, 10))
        
        # 按钮框架
        btn_frame = ttk.Frame(self.main_frame)
        ttk.Button(btn_frame, text="✔️ 确定", 
                  command=lambda: self._on_confirm(callback),
                  style='Dialog.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ 取消",
                  command=self.dialog.destroy,
                  style='Dialog.TButton').pack(side=tk.LEFT, padx=5)
        btn_frame.pack(pady=(0, 10))
        
        # 焦点设置和按键绑定
        self.entry.focus_set()
        self.dialog.bind('<Return>', lambda e: self._on_confirm(callback))
        
    def _on_confirm(self, callback):
        """确认按钮点击处理"""
        if callback:
            callback(self.entry.get().strip())
        self.dialog.destroy()
