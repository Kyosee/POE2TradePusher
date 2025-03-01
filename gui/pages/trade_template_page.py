from tkinter import *
from tkinter import ttk, messagebox
import re

class TradeTemplatePage(ttk.Frame):
    def __init__(self, master, callback_log, callback_status, callback_save=None):
        super().__init__(master, style='Content.TFrame')
        self.log_message = callback_log
        self.status_bar = callback_status
        self.save_config = callback_save
        
        # 创建各组件
        self._create_template_frame()
        self._create_test_frame()
        self._setup_template_menu()
        
    def _create_template_frame(self):
        """创建模板管理区域"""
        self.template_frame = ttk.LabelFrame(self, text="交易模板管理")
        
        # 输入区域
        input_frame = ttk.Frame(self.template_frame)
        self.template_entry = ttk.Entry(input_frame, font=('微软雅黑', 10), width=50)
        self.add_btn = ttk.Button(input_frame, text="➕ 添加", command=self.add_template)
        self.clear_btn = ttk.Button(input_frame, text="🔄 清空", command=self.clear_templates)
        
        # 布局输入区域
        input_frame.pack(fill=X, padx=6, pady=3)
        self.template_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 3))
        self.add_btn.pack(side=LEFT, padx=3)
        self.clear_btn.pack(side=LEFT, padx=3)
        
        # 模板列表
        self.template_list = Listbox(self.template_frame, height=8, font=('微软雅黑', 10),
                                   selectmode=SINGLE, bg="white",
                                   relief='solid', borderwidth=1,
                                   activestyle='none')
        self.template_list.pack(fill=BOTH, expand=True, padx=6, pady=3)
        
        # 布局模板管理区域
        self.template_frame.pack(fill=BOTH, expand=True, padx=12, pady=6)
        
        # 绑定事件
        self.template_list.bind('<Double-Button-1>', lambda e: self.edit_template())
        self.template_list.bind('<Button-3>', self.show_template_menu)
        self.template_entry.bind('<Return>', lambda e: self.add_template())

    def _create_test_frame(self):
        """创建测试区域"""
        self.test_frame = ttk.LabelFrame(self, text="模板测试")
        
        # 测试输入
        test_input_frame = ttk.Frame(self.test_frame)
        self.test_entry = ttk.Entry(test_input_frame, font=('微软雅黑', 10), width=70)
        self.test_btn = ttk.Button(test_input_frame, text="🔍 测试", command=self.test_template)
        
        # 布局测试输入区域
        test_input_frame.pack(fill=X, padx=6, pady=3)
        self.test_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 3))
        self.test_btn.pack(side=LEFT, padx=3)
        
        # 测试结果区域
        self.result_text = Text(self.test_frame, height=6, font=('微软雅黑', 10),
                              relief='solid', borderwidth=1)
        self.result_text.pack(fill=BOTH, expand=True, padx=6, pady=3)
        
        # 布局测试区域
        self.test_frame.pack(fill=BOTH, expand=True, padx=12, pady=6)
        
        # 绑定事件
        self.test_entry.bind('<Return>', lambda e: self.test_template())
        
    def _setup_template_menu(self):
        """设置模板右键菜单"""
        self.template_menu = Menu(self, tearoff=0, font=('微软雅黑', 9))
        self.template_menu.configure(bg='white', activebackground='#E7F7EE',
                                   activeforeground='#07C160', relief='flat')
        
        # 添加菜单项
        self.template_menu.add_command(label="📄 编辑", command=self.edit_template,
                                     font=('微软雅黑', 9))
        self.template_menu.add_command(label="❌ 删除", command=self.remove_selected_template,
                                     font=('微软雅黑', 9))
        self.template_menu.add_separator()
        self.template_menu.add_command(label="📋 复制", command=self.copy_template,
                                     font=('微软雅黑', 9))

    def add_template(self, *args):
        """添加模板"""
        template = self.template_entry.get().strip()
        if not template:
            self.log_message("无法添加空模板", "WARN")
            return
        if template in self.template_list.get(0, END):
            self.log_message(f"重复模板: {template}", "WARN")
            return
        self.template_list.insert(END, template)
        self.template_entry.delete(0, END)
        self.log_message(f"已添加模板: {template}")
        # 自动保存
        if self.save_config:
            self.save_config()

    def edit_template(self):
        """编辑选中的模板"""
        selection = self.template_list.curselection()
        if selection:
            current_template = self.template_list.get(selection[0])
            dialog = Toplevel(self)
            dialog.title("编辑模板")
            dialog.geometry("500x200")
            dialog.transient(self)
            dialog.grab_set()
            dialog.configure(bg='white')
            
            # 设置对话框样式
            main_frame = ttk.Frame(dialog, style='Dialog.TFrame')
            main_frame.pack(expand=True, fill='both', padx=2, pady=2)
            
            ttk.Label(main_frame, text="请输入新的模板内容：",
                     font=('微软雅黑', 9)).pack(padx=10, pady=(10, 5))
            
            entry = ttk.Entry(main_frame, width=60, font=('微软雅黑', 9))
            entry.insert(0, current_template)
            entry.pack(padx=10, pady=(0, 10))
            
            def save_edit():
                new_template = entry.get().strip()
                if new_template and new_template != current_template:
                    if new_template not in self.template_list.get(0, END):
                        self.template_list.delete(selection[0])
                        self.template_list.insert(selection[0], new_template)
                        self.log_message(f"模板已更新: {current_template} → {new_template}")
                        if self.save_config:
                            self.save_config()
                        dialog.destroy()
                    else:
                        messagebox.showwarning("提示", "模板已存在")
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

    def remove_selected_template(self):
        """删除选中的模板"""
        selection = self.template_list.curselection()
        if selection:
            template = self.template_list.get(selection[0])
            self.template_list.delete(selection[0])
            self.log_message(f"已移除模板: {template}")
            # 自动保存
            if self.save_config:
                self.save_config()

    def clear_templates(self):
        """清空模板"""
        if messagebox.askyesno("确认清空", "确定要清空所有模板吗？\n此操作无法撤销"):
            self.template_list.delete(0, END)
            self.log_message("已清空模板列表")
            self.status_bar("✨ 已清空模板列表")
            # 自动保存
            if self.save_config:
                self.save_config()

    def show_template_menu(self, event):
        """显示模板右键菜单"""
        if self.template_list.size() > 0:
            selection = self.template_list.curselection()
            if selection:  # 只在选中项目时显示菜单
                self.template_menu.post(event.x_root, event.y_root)

    def copy_template(self):
        """复制选中的模板到剪贴板"""
        selection = self.template_list.curselection()
        if selection:
            template = self.template_list.get(selection[0])
            self.clipboard_clear()
            self.clipboard_append(template)
            self.status_bar(f"已复制: {template}")

    def test_template(self, *args):
        """测试模板匹配"""
        text = self.test_entry.get().strip()
        if not text:
            self.log_message("请输入测试文本", "WARN")
            return
            
        # 获取选中的模板
        selection = self.template_list.curselection()
        if not selection:
            self.log_message("请先选择一个模板", "WARN")
            return
            
        template = self.template_list.get(selection[0])
        
        # 提取占位符
        placeholders = re.findall(r'\{@(\w+)\}', template)
        
        # 创建正则表达式
        pattern = re.escape(template)
        for ph in placeholders:
            pattern = pattern.replace(re.escape(f'{{@{ph}}}'), r'(.*?)')
        
        # 尝试匹配
        match = re.match(pattern, text)
        if match:
            # 清空结果区域
            self.result_text.delete('1.0', END)
            
            # 显示匹配结果
            for i, ph in enumerate(placeholders, 1):
                value = match.group(i)
                self.result_text.insert(END, f'{ph}: {value}\n')
                
            self.log_message("匹配成功")
            self.status_bar("✅ 匹配成功")
        else:
            self.result_text.delete('1.0', END)
            self.result_text.insert(END, "❌ 匹配失败")
            self.log_message("匹配失败", "WARN")
            self.status_bar("❌ 匹配失败")

    def get_data(self):
        """获取页面数据"""
        return {
            'templates': list(self.template_list.get(0, END))
        }
        
    def set_data(self, data):
        """设置页面数据"""
        self.template_list.delete(0, END)
        for template in data.get('templates', []):
            self.template_list.insert(END, template)
