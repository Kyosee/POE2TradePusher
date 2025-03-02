from tkinter import *
from tkinter import ttk, filedialog
import os
import re
from ..utils import LoggingMixin, ConfigMixin, show_message, ask_yes_no
from ..widgets.dialog import MessageDialog, InputDialog

class BasicConfigPage(ttk.Frame, LoggingMixin, ConfigMixin):
    """基本配置页面"""
    def __init__(self, master, log_callback, status_callback, callback_save=None):
        ttk.Frame.__init__(self, master, style='Content.TFrame')
        LoggingMixin.__init__(self, log_callback, status_callback)
        self.save_config = callback_save
        self.main_window = None  # 用于存储MainWindow引用
        
        # 创建各组件
        self._create_game_frame()
        self._create_file_frame()
        self._create_settings_frame()
        self._create_keywords_frame()
        self._setup_keyword_menu()
        
    def _create_game_frame(self):
        """创建游戏窗口配置区域"""
        self.game_frame = ttk.LabelFrame(self, text="游戏窗口配置")
        ttk.Label(self.game_frame, text="窗口名称:", style='Frame.TLabel').grid(row=0, column=0, padx=6)
        self.game_entry = ttk.Entry(self.game_frame, width=70)
        self.game_entry.insert(0, "Path of Exile")
        self.switch_btn = ttk.Button(self.game_frame, text="切换窗口", command=self._switch_to_game)
        
        # 布局游戏窗口配置区域
        self.game_frame.pack(fill=X, padx=12, pady=6)
        self.game_entry.grid(row=0, column=1, padx=6, sticky="ew")
        self.switch_btn.grid(row=0, column=2, padx=6)
        self.game_frame.columnconfigure(1, weight=1)
        
        # 绑定值变化事件
        self.game_entry.bind('<KeyRelease>', lambda e: self._on_settings_change())
        
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
        
        # 添加置顶开关
        ttk.Label(self.settings_frame, text="置顶本程序窗口:", style='Frame.TLabel').grid(row=1, column=0, padx=6, pady=(6,0))
        from gui.widgets.switch import Switch
        self.top_switch = Switch(self.settings_frame, width=50, height=30, default=False)
        self.top_switch.grid(row=1, column=1, padx=0, pady=(6,0))
        
        # 绑定置顶开关事件
        self.top_switch.checked.trace_add('write', self._on_top_switch_change)
        
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
        
    def _create_keywords_frame(self):
        """创建关键词管理区域"""
        self.keywords_frame = ttk.LabelFrame(self, text="关键词管理")
        
        # 输入框和按钮
        input_frame = ttk.Frame(self.keywords_frame, style='Frame.TLabel')
        
        # 模式选择下拉列表
        self.mode_var = StringVar(value="消息模式")
        self.mode_combo = ttk.Combobox(input_frame, textvariable=self.mode_var, 
                                     values=["消息模式", "交易模式"], 
                                     state="readonly", width=10,
                                     font=('微软雅黑', 10))
        self.mode_combo.configure(height=25)  # 调整下拉框高度
        style = ttk.Style()
        style.configure('Combobox', padding=6)  # 调整内边距
        self.mode_combo.bind('<<ComboboxSelected>>', lambda e: self.keyword_entry.focus())
        
        self.keyword_entry = ttk.Entry(input_frame, font=('微软雅黑', 10))
        self.add_btn = ttk.Button(input_frame, text="➕ 添加", command=self.add_keyword)
        self.clear_kw_btn = ttk.Button(input_frame, text="🔄 清空", command=self.clear_keywords)
        self.help_btn = ttk.Button(input_frame, text="❓ 帮助", 
                                 command=self.show_help,
                                 style='Control.Save.TButton')
        
        # 布局输入区域
        input_frame.pack(fill=X, padx=6, pady=3)
        self.mode_combo.pack(side=LEFT, padx=(0, 3))
        self.keyword_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 3))
        self.add_btn.pack(side=LEFT, padx=3)
        self.clear_kw_btn.pack(side=LEFT, padx=3)
        self.help_btn.pack(side=LEFT, padx=3)
        
        # 关键词列表
        list_frame = ttk.Frame(self.keywords_frame)
        list_frame.pack(fill=BOTH, expand=True, padx=6, pady=3)
        
        self.keyword_list = Listbox(list_frame, height=8, font=('微软雅黑', 10),
                                  selectmode=SINGLE, bg="white",
                                  relief='solid', borderwidth=1,
                                  activestyle='none')
        self.keyword_list.pack(side=LEFT, fill=BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
                                command=self.keyword_list.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.keyword_list.configure(yscrollcommand=scrollbar.set)
        
        # 布局关键词管理区域
        self.keywords_frame.pack(fill=BOTH, expand=True, padx=12, pady=6)

        # 测试区域
        test_frame = ttk.LabelFrame(self, text="关键词测试")
        test_frame.pack(fill=X, padx=12, pady=6)
        
        test_input_frame = ttk.Frame(test_frame, style='Frame.TLabel')
        test_input_frame.pack(fill=X, padx=6, pady=(6, 3))
        
        self.test_text = Text(test_input_frame, height=1,
                            font=('微软雅黑', 9),
                            relief='solid', borderwidth=1,
                            bg='white', padx=8, pady=8)
        self.test_text.pack(side=LEFT, fill=X, expand=True, padx=(0, 3))
        
        test_btn = ttk.Button(test_input_frame, text="测试", 
                            command=self.test_keyword)
        test_btn.pack(side=LEFT, padx=3)
        
        self.test_result = Text(test_frame, height=4,
                              font=('微软雅黑', 9),
                              relief='solid', borderwidth=1,
                              bg='white', padx=8, pady=8,
                              state='disabled')
        self.test_result.pack(fill=X, padx=6, pady=(3, 6))
        
        # 绑定事件
        self.keyword_list.bind('<Double-Button-1>', lambda e: self.edit_keyword())
        self.keyword_list.bind('<Button-3>', self.show_keyword_menu)
        self.keyword_list.bind('<<ListboxSelect>>', lambda e: self.on_keyword_select())
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
                                    
    def show_help(self):
        """显示帮助信息"""
        help_content = """消息模式：
填写 來自 则日志中匹配到包含 來自 的消息就会推送，支持多关键词匹配用"|"进行分隔，如：來自|我想購買 则只会匹配日志中同时包含这两个关键词的行进行推送

交易模式：
示例 *來自 {@user}: 你好，我想購買 {@item} 標價 {@price} {@currency} 在 {@mode} (倉庫頁 "{@tab}"; 位置: {@p1} {@p1_num}, {@p2} {@p2_num})
*代表会变化的任意内容（因为时间和客户端ID会变化）
@user 玩家昵称
@item 装备名称
@price 通货数量
@currency 通货单位
@mode 游戏模式
@tab 仓库页
@p1 位置1方向
@p1_num 位置1坐标
@p2 位置2方向
@p2_num 位置2坐标"""
        
        MessageDialog(self, "关键词帮助", help_content)
        
    def add_keyword(self, *args):
        """添加关键词"""
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            self.log_message("无法添加空关键词", "WARN")
            return
            
        mode = self.mode_var.get()
        formatted_keyword = f"[{mode}] {keyword}"
            
        if formatted_keyword in self.keyword_list.get(0, END):
            self.log_message(f"重复关键词: {keyword}", "WARN")
            return
            
        self.keyword_list.insert(END, formatted_keyword)
        self.keyword_entry.delete(0, END)
        self.log_message(f"已添加关键词: {formatted_keyword}")
        if self.save_config:
            self.save_config()
            
    def test_keyword(self):
        """测试关键词"""
        selection = self.keyword_list.curselection()
        if not selection:
            show_message("提示", "请先选择要测试的关键词", "warning")
            return
            
        keyword = self.keyword_list.get(selection[0])
        test_text = self.test_text.get('1.0', 'end-1c')
        
        if not test_text:
            show_message("提示", "请输入要测试的文本", "warning")
            return
            
        # 从关键词中提取模式
        if "[消息模式]" in keyword:
            mode = "消息模式"
            pattern = keyword.replace("[消息模式]", "").strip()
        else:
            mode = "交易模式"
            pattern = keyword.replace("[交易模式]", "").strip()
            
        # 启用文本框以更新内容
        self.test_result.config(state='normal')
        self.test_result.delete('1.0', END)
        
        if mode == "消息模式":
            # 消息模式测试
            keywords = pattern.split('|')
            if all(kw.strip() in test_text for kw in keywords):
                self.test_result.insert('1.0', f"匹配成功：{pattern}")
            else:
                self.test_result.insert('1.0', "[消息模式]不匹配")
        else:
            # 交易模式测试
            # 将模板中的*替换为通配符
            template = pattern.replace('*', '.*?')
            # 替换占位符为捕获组
            placeholders = [
                '@user', '@item', '@price', '@currency', '@mode',
                '@tab', '@p1', '@p1_num', '@p2', '@p2_num'
            ]
            template = template.replace('(', '\(')
            template = template.replace(')', '\)')
            for ph in placeholders:
                template = template.replace('{' + ph + '}', '(.+?)')
           
            match = re.match(template, test_text)
            if match:
                result = "匹配成功，解析结果：\n"
                for i, ph in enumerate(placeholders, 1):
                    if i <= len(match.groups()):
                        result += f"{ph[1:]}: {match.group(i)}\n"
                self.test_result.insert('1.0', result)
            else:
                self.test_result.insert('1.0', "[交易模式]不匹配")
                
        # 禁用文本框
        self.test_result.config(state='disabled')
        
    def edit_keyword(self):
        """编辑选中的关键词"""
        selection = self.keyword_list.curselection()
        if not selection:
            return
            
        current_keyword = self.keyword_list.get(selection[0])
        # 从关键词中提取模式和内容
        if "[消息模式]" in current_keyword:
            mode = "消息模式"
            pattern = current_keyword.replace("[消息模式]", "").strip()
        else:
            mode = "交易模式"
            pattern = current_keyword.replace("[交易模式]", "").strip()
            
        def save_edit(new_pattern):
            new_keyword = f"[{mode}] {new_pattern}"
            if new_pattern and new_keyword != current_keyword:
                if new_keyword not in self.keyword_list.get(0, END):
                    self.keyword_list.delete(selection[0])
                    self.keyword_list.insert(selection[0], new_keyword)
                    self.log_message(f"关键词已更新: {current_keyword} → {new_keyword}")
                    if self.save_config:
                        self.save_config()
                else:
                    show_message("提示", "关键词已存在", "warning")
                    
        # 使用InputDialog替代
        InputDialog(self, "编辑关键词", "请输入新的关键词：", pattern, save_edit)

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
        if ask_yes_no("确认清空", "确定要清空所有关键词吗？\n此操作无法撤销"):
            self.keyword_list.delete(0, END)
            self.log_message("已清空关键词列表")
            self.update_status("✨ 已清空关键词列表")
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
            self.update_status(f"已复制: {keyword}")
            
    def select_file(self):
        """选择文件"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_entry.delete(0, END)
            self.file_entry.insert(0, file_path)
            self.log_message(f"已选择日志文件: {file_path}")
            if self.save_config:
                self.save_config()
                
    def validate_config(self):
        """验证配置数据"""
        data = self.get_config_data()
        
        if not data.get('log_path'):
            return False, "请选择日志文件"
            
        if not data.get('keywords', []):
            return False, "请至少添加一个关键词"
            
        try:
            interval = int(data.get('interval', 0))
            if interval < 500 or interval > 5000:
                return False, "检测间隔必须在500-5000毫秒之间"
        except ValueError:
            return False, "无效的检测间隔值"
            
        try:
            push_interval = int(data.get('push_interval', 0))
            if push_interval < 0:
                return False, "推送间隔不能为负数"
        except ValueError:
            return False, "无效的推送间隔值"
            
        return True, None

    def _on_settings_change(self):
        """处理设置值变化"""
        if self.save_config:
            self.save_config()
            
    def _switch_to_game(self):
        """切换到游戏窗口"""
        from ..utils import switch_to_window
        window_name = self.game_entry.get().strip()
        if switch_to_window(window_name):
            self.log_message(f"已切换到游戏窗口: {window_name}")
        else:
            self.log_message(f"切换窗口失败: {window_name}", "ERROR")
            
    def get_config_data(self):
        """获取配置数据"""
        keywords = []
        for i in range(self.keyword_list.size()):
            kw = self.keyword_list.get(i)
            if "[消息模式]" in kw:
                mode = "消息模式"
                pattern = kw.replace("[消息模式]", "").strip()
            else:
                mode = "交易模式"
                pattern = kw.replace("[交易模式]", "").strip()
                
            keywords.append({
                "mode": mode,
                "pattern": pattern
            })
            
        return {
            'game_window': self.game_entry.get(),
            'log_path': self.file_entry.get(),
            'interval': int(self.interval_spin.get()),
            'push_interval': int(self.push_interval_entry.get() or 0),
            'keywords': keywords,
            'always_on_top': self.top_switch.get()
        }
        
    def set_config_data(self, data):
        """设置配置数据"""
        self.game_entry.delete(0, END)
        self.game_entry.insert(0, data.get('game_window', 'Path of Exile'))
        
        # 设置置顶开关状态并触发置顶效果
        always_on_top = data.get('always_on_top', False)
        self.top_switch.set(always_on_top)
        # 设置置顶状态
        if self.main_window:
            self.main_window.set_always_on_top(always_on_top)
        
        self.file_entry.delete(0, END)
        self.file_entry.insert(0, data.get('log_path', ''))
        
        self.interval_spin.set(data.get('interval', 1000))
        
        self.push_interval_entry.delete(0, END)
        self.push_interval_entry.insert(0, data.get('push_interval', 0))
        
        self.keyword_list.delete(0, END)
        for kw in data.get('keywords', []):
            # 兼容旧版数据格式
            if isinstance(kw, str):
                self.keyword_list.insert(END, f"[消息模式] {kw}")
            else:
                mode = kw.get('mode', '消息模式')
                pattern = kw.get('pattern', '')
                self.keyword_list.insert(END, f"[{mode}] {pattern}")
    
    def set_main_window(self, main_window):
        """设置MainWindow引用"""
        self.main_window = main_window

    def _on_top_switch_change(self, *args):
        """处理置顶开关状态变化"""
        if self.main_window:
            self.main_window.set_always_on_top(self.top_switch.get())
        if self.save_config:
            self.save_config()
