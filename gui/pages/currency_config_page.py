from tkinter import *
from tkinter import ttk, messagebox
from tkinter import TclError
from PIL import Image, ImageTk
import os
import sys

class CurrencyConfigPage(ttk.Frame):
    def __init__(self, master, callback_log, callback_status, callback_save=None):
        super().__init__(master, style='Content.TFrame')
        self.log_message = callback_log
        self.status_bar = callback_status
        self.save_config = callback_save
        self.currency_items = []  # 存储通货单位项的引用
        self.selected_currency_item = None
        
        # 创建通货单位配置框架
        self.currency_label_frame = ttk.LabelFrame(self, text="通货单位配置")
        self.currency_label_frame.pack(fill=BOTH, expand=True, padx=6, pady=3)
        
        # 创建样式
        style = ttk.Style()
        style.configure('Currency.TFrame', background='white')
        style.configure('CurrencySelected.TFrame', background='#E7F7EE')
        style.configure('Dialog.TButton', font=('微软雅黑', 9))
        
        # 设置框架样式
        style.layout('Currency.TFrame', [
            ('Frame.border', {'sticky': 'nsew', 'children': [
                ('Frame.padding', {'sticky': 'nsew'})
            ]})
        ])
        style.layout('CurrencySelected.TFrame', [
            ('Frame.border', {'sticky': 'nsew', 'children': [
                ('Frame.padding', {'sticky': 'nsew'})
            ]})
        ])
        
        # 配置边框样式
        style.configure('Currency.TFrame', borderwidth=1, relief='solid', bordercolor='#E5E5E5')
        style.configure('CurrencySelected.TFrame', borderwidth=1, relief='solid', bordercolor='#07C160')
        
        # 创建通货单位配置区域
        self._create_currency_frame()
        self._setup_currency_menu()
        
    def _get_resource_path(self, filename):
        """获取资源文件路径"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, "assets", "orb", filename)
        
    def _create_currency_item(self, currency):
        """创建通货单位项"""
        # 创建固定高度的框架
        frame = ttk.Frame(self.currency_frame_inner, style='Currency.TFrame', height=34)
        frame.pack(fill=X, padx=0, pady=0)
        frame.pack_propagate(False)  # 固定高度
        
        # 创建标签
        img_frame = ttk.Frame(frame, width=30, height=30)
        img_frame.pack(side=LEFT, padx=1)
        img_frame.pack_propagate(False)  # 固定图片容器大小
        
        img_label = Label(img_frame, width=30, height=30)
        img_path = self._get_resource_path(f"{currency.lower()}.png")
        
        try:
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img = img.resize((30, 30), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                img_label.configure(image=photo)
                img_label.image = photo  # 保持引用
        except Exception as e:
            self.log_message(f"加载图片失败: {e}", "ERROR")
            
        img_label.pack(side=LEFT, padx=2)
        
        # 通货名称标签
        text_label = ttk.Label(frame, text=currency, font=('微软雅黑', 10))
        text_label.pack(side=LEFT, fill=X, expand=True, padx=2)
        
        # 绑定事件
        def on_select(event=None):
            # 清除其他项的选中状态
            if self.selected_currency_item and self.selected_currency_item.winfo_exists():
                try:
                    self.selected_currency_item.configure(style='Currency.TFrame')
                except TclError:
                    pass  # Widget no longer exists
            # 设置当前项的选中状态
            frame.configure(style='CurrencySelected.TFrame')
            self.selected_currency_item = frame
            
        frame.bind('<Button-1>', on_select)
        img_label.bind('<Button-1>', lambda e: on_select())
        text_label.bind('<Button-1>', lambda e: on_select())
        
        # 绑定右键菜单
        def on_right_click(event):
            on_select()  # 先选中
            self._show_currency_menu(event)  # 再显示菜单
            
        frame.bind('<Button-3>', on_right_click)
        text_label.bind('<Button-3>', on_right_click)
        img_label.bind('<Button-3>', on_right_click)
        
        return frame
        
    def _create_currency_frame(self):
        """创建通货单位配置区域"""
        # 输入框和按钮
        input_frame = ttk.Frame(self.currency_label_frame)
        self.currency_entry = ttk.Entry(input_frame, font=('微软雅黑', 10))
        self.add_currency_btn = ttk.Button(input_frame, text="➕ 添加", command=self.add_currency)
        self.clear_currency_btn = ttk.Button(input_frame, text="🔄 清空", command=self.clear_currencies)
        
        # 布局输入区域
        input_frame.pack(fill=X, padx=6, pady=3)
        self.currency_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 3))
        self.add_currency_btn.pack(side=LEFT, padx=3)
        self.clear_currency_btn.pack(side=LEFT, padx=3)
        
        # 通货单位列表容器
        self.currency_container = ttk.Frame(self.currency_label_frame)
        self.currency_container.pack(fill=BOTH, expand=True, padx=6, pady=3)
        
        # 创建滚动条和画布
        self.currency_canvas = Canvas(self.currency_container, bg="white", 
                                    relief='flat', borderwidth=0,
                                    highlightthickness=0)
        self.currency_scrollbar = ttk.Scrollbar(self.currency_container, 
                                               orient="vertical", 
                                               command=self.currency_canvas.yview)
        self.currency_frame_inner = ttk.Frame(self.currency_canvas)
        
        # 配置画布和滚动条
        self.currency_canvas.configure(yscrollcommand=self.currency_scrollbar.set)
        self.currency_canvas.create_window((0, 0), window=self.currency_frame_inner, 
                                         anchor='nw', tags=("currency_frame",))
        
        # 布局
        self.currency_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.currency_scrollbar.pack(side=RIGHT, fill=Y)
        
        # 绑定事件
        self.currency_frame_inner.bind('<Configure>', self._on_frame_configure)
        self.currency_canvas.bind('<Configure>', self._on_canvas_configure)
        self.currency_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.currency_canvas.bind("<Enter>", lambda e: self.currency_canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.currency_canvas.bind("<Leave>", lambda e: self.currency_canvas.unbind_all("<MouseWheel>"))
        self.currency_entry.bind('<Return>', lambda e: self.add_currency())
        
    def _show_currency_menu(self, event):
        """显示通货单位右键菜单"""
        if hasattr(self, 'selected_currency_item') and self.selected_currency_item.winfo_exists():
            self.currency_menu.post(event.x_root, event.y_root)
            
    def _setup_currency_menu(self):
        """设置通货单位右键菜单"""
        self.currency_menu = Menu(self, tearoff=0, font=('微软雅黑', 9))
        self.currency_menu.configure(bg='white', activebackground='#E7F7EE',
                                   activeforeground='#07C160', relief='flat')
        
        # 添加菜单项
        self.currency_menu.add_command(label="📄 编辑", command=self.edit_currency,
                                     font=('微软雅黑', 9))
        self.currency_menu.add_command(label="❌ 删除", command=self.remove_selected_currency,
                                     font=('微软雅黑', 9))
        self.currency_menu.add_separator()
        self.currency_menu.add_command(label="📋 复制", command=self.copy_currency,
                                     font=('微软雅黑', 9))
                                     
    def _update_canvas_scroll(self):
        """更新canvas的滚动区域"""
        self.currency_canvas.update_idletasks()
        self.currency_canvas.configure(scrollregion=self.currency_canvas.bbox("all"))
        
    def _on_frame_configure(self, event=None):
        """处理内部frame大小变化"""
        self._update_canvas_scroll()
        
    def _on_canvas_configure(self, event):
        """处理画布大小变化"""
        self.currency_canvas.itemconfig("currency_frame", width=event.width)
        self._on_frame_configure()
        
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        if self.currency_canvas.winfo_exists():
            self.currency_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
    def add_currency(self, *args):
        """添加通货单位"""
        currency = self.currency_entry.get().strip()
        if not currency:
            self.log_message("无法添加空通货单位", "WARN")
            return
            
        # 检查是否已存在
        for item in self.currency_items:
            if item.winfo_children()[1].cget("text") == currency:
                self.log_message(f"重复通货单位: {currency}", "WARN")
                return
                
        # 创建新的通货单位项
        item_frame = self._create_currency_item(currency)
        self.currency_items.append(item_frame)
        self._update_canvas_scroll()
        
        self.currency_entry.delete(0, END)
        self.log_message(f"已添加通货单位: {currency}")
        
        # 自动保存配置
        if self.save_config:
            try:
                self.save_config()
                self.status_bar.config(text=f"✨ 已添加并保存通货单位: {currency}")
            except Exception as e:
                self.log_message(f"保存配置失败: {e}", "ERROR")
                
    def edit_currency(self):
        """编辑选中的通货单位"""
        if hasattr(self, 'selected_currency_item') and self.selected_currency_item.winfo_exists():
            try:
                current_currency = self.selected_currency_item.winfo_children()[1].cget("text")
            except TclError:
                return  # Widget no longer exists
            dialog = Toplevel(self)
            dialog.title("编辑通货单位")
            dialog.geometry("300x140")
            dialog.transient(self)
            dialog.grab_set()
            dialog.configure(bg='white')
            
            # 设置对话框样式
            main_frame = ttk.Frame(dialog, style='Dialog.TFrame')
            main_frame.pack(expand=True, fill='both', padx=2, pady=2)
            
            ttk.Label(main_frame, text="请输入新的通货单位：",
                     font=('微软雅黑', 9)).pack(padx=10, pady=(10, 5))
            
            entry = ttk.Entry(main_frame, width=40, font=('微软雅黑', 9))
            entry.insert(0, current_currency)
            entry.pack(padx=10, pady=(0, 10))
            
            def save_edit():
                new_currency = entry.get().strip()
                if new_currency and new_currency != current_currency:
                    # 检查是否已存在
                    for item in self.currency_items:
                        if item != self.selected_currency_item and \
                           item.winfo_children()[1].cget("text") == new_currency:
                            messagebox.showwarning("提示", "通货单位已存在")
                            return
                            
                    # 更新通货单位
                    self.selected_currency_item.destroy()
                    self.currency_items.remove(self.selected_currency_item)
                    new_item = self._create_currency_item(new_currency)
                    self.currency_items.append(new_item)
                    self.log_message(f"通货单位已更新: {current_currency} → {new_currency}")
                    if self.save_config:
                        self.save_config()
                    dialog.destroy()
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
            
    def remove_selected_currency(self):
        """删除选中的通货单位"""
        if hasattr(self, 'selected_currency_item') and self.selected_currency_item.winfo_exists():
            try:
                currency = self.selected_currency_item.winfo_children()[1].cget("text")
            except TclError:
                return  # Widget no longer exists
            self.selected_currency_item.destroy()
            self.currency_items.remove(self.selected_currency_item)
            self.selected_currency_item = None
            self.log_message(f"已移除通货单位: {currency}")
            if self.save_config:
                self.save_config()
            
    def clear_currencies(self):
        """清空通货单位"""
        if messagebox.askyesno("确认清空", "确定要清空所有通货单位吗？\n此操作无法撤销"):
            for item in self.currency_items:
                item.destroy()
            self.currency_items.clear()
            self.selected_currency_item = None
            self.log_message("已清空通货单位列表")
            self.status_bar.config(text="✨ 已清空通货单位列表")
            if self.save_config:
                self.save_config()
            
    def copy_currency(self):
        """复制选中的通货单位到剪贴板"""
        if hasattr(self, 'selected_currency_item') and self.selected_currency_item.winfo_exists():
            try:
                currency = self.selected_currency_item.winfo_children()[1].cget("text")
                self.clipboard_clear()
                self.clipboard_append(currency)
                self.status_bar.config(text=f"已复制: {currency}")
            except TclError:
                pass  # Widget no longer exists
            
    def get_data(self):
        """获取页面数据"""
        currencies = []
        for item in self.currency_items:
            try:
                if item.winfo_exists():
                    currencies.append(item.winfo_children()[1].cget("text"))
            except TclError:
                continue  # Skip invalid items
        return {'currencies': currencies}
        
    def set_data(self, data):
        """设置页面数据"""
        # 清空现有通货单位
        for item in self.currency_items:
            item.destroy()
        self.currency_items.clear()
        self.selected_currency_item = None
        
        # 添加新的通货单位
        for currency in data.get('currencies', []):
            item_frame = self._create_currency_item(currency)
            self.currency_items.append(item_frame)
        
        # 更新滚动区域
        self._update_canvas_scroll()
