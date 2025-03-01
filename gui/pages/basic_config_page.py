from tkinter import *
from tkinter import ttk, filedialog, messagebox
import os

class BasicConfigPage(ttk.Frame):
    def __init__(self, master, callback_log, callback_status, callback_save=None):
        super().__init__(master, style='Content.TFrame')
        self.log_message = callback_log
        self.status_bar = callback_status
        self.save_config = callback_save
        
        # 创建各组件
        self._create_file_frame()
        self._create_settings_frame()
        self._create_keywords_frame()
        self._setup_keyword_menu()
        
    def _create_file_frame(self):
        """创建文件配置区域"""
        self.file_frame = ttk.LabelFrame(self, text="日志文件配置")
        ttk.Label(self.file_frame, text="日志路径:", style='Frame.TLabel').grid(row=0, column=0, padx=6)
        self.file_entry = ttk.Entry(self.file_frame, width=70)
        self.browse_btn = ttk.Button(self.file_frame, text="📂 浏览", command=self.select_file)
        
        # 布局文件配置区域
        self.file_frame.pack(fill=X, padx=12, pady=6)
        self.file_entry.grid(row=0, column=1, padx=6, sticky="ew")
        self.browse_btn.grid(row=0, column=2, padx=6)
        self.file_frame.columnconfigure(1, weight=1)
        
        # 绑定值变化事件
        self.file_entry.bind('<KeyRelease>', lambda e: self._on_settings_change())
        
    def _create_settings_frame(self):
        """创建监控设置区域"""
        self.settings_frame = ttk.LabelFrame(self, text="监控设置")
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
        
        # 绑定值变化事件
        self.interval_spin.bind('<KeyRelease>', lambda e: self._on_settings_change())
        self.interval_spin.bind('<ButtonRelease-1>', lambda e: self._on_settings_change())
        self.push_interval_entry.bind('<KeyRelease>', lambda e: self._on_settings_change())
        
    def _on_settings_change(self):
        """处理设置值变化"""
        if self.save_config:
            self.save_config()
        
    def _create_keywords_frame(self):
        """创建关键词管理区域"""
        self.keywords_frame = ttk.LabelFrame(self, text="关键词管理")
        
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
        
        # 布局关键词管理区域
        self.keywords_frame.pack(fill=BOTH, expand=True, padx=12, pady=6)
        
        # 绑定事件
        self.keyword_list.bind('<Double-Button-1>', lambda e: self.edit_keyword())
        self.keyword_list.bind('<Button-3>', self.show_keyword_menu)
        self.keyword_entry.bind('<Return>', lambda e: self.add_keyword())
        
    def _setup_keyword_menu(self):
        """设置关键词右键菜单"""
        self.keyword_menu = Menu(self, tearoff=0, font=('微软雅黑', 9))
        self.keyword_menu.configure(bg='white', activebackground='#E7F7EE',
                                  activeforeground='#07C160', relief='flat')
        
        # 添加菜单项
        self.keyword_menu.add_command(label="📄 编辑", command=self.edit_keyword,
                                    font=('微软雅黑', 9))
        self.keyword_menu.add_command(label="❌ 删除", command=self.remove_selected_keyword,
                                    font=('微软雅黑', 9))
        self.keyword_menu.add_separator()
        self.keyword_menu.add_command(label="📋 复制", command=self.copy_keyword,
                                    font=('微软雅黑', 9))
                                    
    # 关键词相关方法
    def add_keyword(self, *args):
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
        if self.save_config:
            self.save_config()
        
    def edit_keyword(self):
        """编辑选中的关键词"""
        selection = self.keyword_list.curselection()
        if selection:
            current_keyword = self.keyword_list.get(selection[0])
            dialog = Toplevel(self)
            dialog.title("编辑关键词")
            dialog.geometry("300x140")
            dialog.transient(self)
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
                        if self.save_config:
                            self.save_config()
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
            
    def remove_selected_keyword(self):
        """删除选中的关键词"""
        selection = self.keyword_list.curselection()
        if selection:
            keyword = self.keyword_list.get(selection[0])
            self.keyword_list.delete(selection[0])
            self.log_message(f"已移除关键词: {keyword}")
            if self.save_config:
                self.save_config()
            
    def clear_keywords(self):
        """清空关键词"""
        if messagebox.askyesno("确认清空", "确定要清空所有关键词吗？\n此操作无法撤销"):
            self.keyword_list.delete(0, END)
            self.log_message("已清空关键词列表")
            self.status_bar.config(text="✨ 已清空关键词列表")
            if self.save_config:
                self.save_config()
            
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
            self.clipboard_clear()
            self.clipboard_append(keyword)
            self.status_bar.config(text=f"已复制: {keyword}")
            
    def select_file(self):
        """选择文件"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_entry.delete(0, END)
            self.file_entry.insert(0, file_path)
            self.log_message(f"已选择日志文件: {file_path}")
            if self.save_config:
                self.save_config()
            
    # 获取/设置数据方法
    def get_data(self):
        """获取页面数据"""
        return {
            'log_path': self.file_entry.get(),
            'interval': int(self.interval_spin.get()),
            'push_interval': int(self.push_interval_entry.get() or 0),
            'keywords': list(self.keyword_list.get(0, END))
        }
        
    def set_data(self, data):
        """设置页面数据"""
        self.file_entry.delete(0, END)
        self.file_entry.insert(0, data.get('log_path', ''))
        
        self.interval_spin.set(data.get('interval', 1000))
        
        self.push_interval_entry.delete(0, END)
        self.push_interval_entry.insert(0, data.get('push_interval', 0))
        
        self.keyword_list.delete(0, END)
        for kw in data.get('keywords', []):
            self.keyword_list.insert(END, kw)
