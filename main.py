import os
import re
import time
import json
import requests
import chardet
import threading
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext

class AdvancedLogMonitorPro:
    def __init__(self, root):
        self.root = root
        self.root.title("POE2 Trade Pusher")
        self.root.geometry("1000x800")
        self.config_file = "config.json"
        self.current_encoding = 'utf-8'
        self.fallback_encodings = ['gb18030', 'gbk', 'big5']
        self.last_position = 0
        self.last_size = 0
        self.last_timestamp = None
        self.monitoring = False
        self.config = {}
        self.stop_event = threading.Event()
        self.last_push_time = 0
        self.push_interval = 0  # 毫秒

        # 时间戳正则模式
        self.time_pattern = re.compile(r'^(\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})')
        
        self.setup_style()
        self.create_widgets()
        self.setup_layout()
        self.setup_bindings()
        self.load_config()

    def setup_style(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', padding=8, font=('微软雅黑', 10))
        self.style.configure('TLabel', font=('微软雅黑', 10))
        self.style.configure('TEntry', font=('Consolas', 10))
        self.style.map('TButton', 
            foreground=[('active', 'blue'), ('disabled', 'gray')],
            background=[('active', '!disabled', '#e1e1e1')]
        )

    def create_widgets(self):
        # 文件配置区域
        self.file_frame = ttk.LabelFrame(self.root, text="日志文件配置")
        self.file_entry = ttk.Entry(self.file_frame, width=70)
        self.browse_btn = ttk.Button(self.file_frame, text="浏览文件", command=self.select_file)

        # 监控设置
        self.settings_frame = ttk.LabelFrame(self.root, text="监控设置")
        self.interval_spin = ttk.Spinbox(self.settings_frame, from_=500, to=5000, 
                                       increment=100, width=8, font=('Consolas', 10))
        self.push_interval_entry = ttk.Entry(self.settings_frame, width=8, font=('Consolas', 10))

        # 关键词管理
        self.keywords_frame = ttk.LabelFrame(self.root, text="关键词管理")
        self.keyword_entry = ttk.Entry(self.keywords_frame, font=('微软雅黑', 10))
        self.add_btn = ttk.Button(self.keywords_frame, text="添加", command=self.add_keyword)
        self.clear_kw_btn = ttk.Button(self.keywords_frame, text="清空", command=self.clear_keywords)
        self.keyword_list = Listbox(self.keywords_frame, height=6, font=('微软雅黑', 10), 
                                 selectmode=SINGLE, bg="#f8f8f8")

        # WxPusher配置
        self.wxpusher_frame = ttk.LabelFrame(self.root, text="WxPusher配置")
        self.app_token_entry = ttk.Entry(self.wxpusher_frame, width=50, font=('Consolas', 10))
        self.uid_entry = ttk.Entry(self.wxpusher_frame, width=50, font=('Consolas', 10))

        # 触发日志
        self.log_frame = ttk.LabelFrame(self.root, text="触发日志")
        self.log_area = scrolledtext.ScrolledText(self.log_frame, wrap=WORD, state='disabled',
                                                 font=('微软雅黑', 10), height=20, bg="#fcfcfc")
        self.clear_log_btn = ttk.Button(self.log_frame, text="清空日志", command=self.clear_log)

        # 控制按钮
        self.control_frame = ttk.Frame(self.root)
        self.start_btn = ttk.Button(self.control_frame, text="▶ 开始监控", style='TButton', 
                                   command=self.toggle_monitor)
        self.save_btn = ttk.Button(self.control_frame, text="💾 保存配置", style='TButton',
                                  command=self.save_config)

    def setup_layout(self):
        # 文件配置布局
        self.file_frame.grid(row=0, column=0, padx=12, pady=6, sticky="ew")
        ttk.Label(self.file_frame, text="日志路径:").grid(row=0, column=0, padx=6)
        self.file_entry.grid(row=0, column=1, padx=6, sticky="ew")
        self.browse_btn.grid(row=0, column=2, padx=6)

        # 监控设置布局
        self.settings_frame.grid(row=1, column=0, padx=12, pady=6, sticky="ew")
        ttk.Label(self.settings_frame, text="检测间隔(ms):").grid(row=0, column=0, padx=6)
        self.interval_spin.grid(row=0, column=1, padx=6)
        ttk.Label(self.settings_frame, text="推送间隔(ms):").grid(row=0, column=2, padx=6)
        self.push_interval_entry.grid(row=0, column=3, padx=6)

        # 关键词管理布局
        self.keywords_frame.grid(row=2, column=0, padx=12, pady=6, sticky="ew")
        self.keyword_entry.grid(row=0, column=0, padx=6, pady=3, sticky="ew")
        self.add_btn.grid(row=0, column=1, padx=3)
        self.clear_kw_btn.grid(row=0, column=2, padx=3)
        self.keyword_list.grid(row=1, column=0, columnspan=3, padx=6, pady=3, sticky="ew")

        # WxPusher配置布局
        self.wxpusher_frame.grid(row=3, column=0, padx=12, pady=6, sticky="ew")
        ttk.Label(self.wxpusher_frame, text="App Token:").grid(row=0, column=0, padx=6, sticky="w")
        self.app_token_entry.grid(row=0, column=1, columnspan=2, padx=6, sticky="ew")
        ttk.Label(self.wxpusher_frame, text="用户UID:").grid(row=1, column=0, padx=6, sticky="w")
        self.uid_entry.grid(row=1, column=1, columnspan=2, padx=6, sticky="ew")

        # 触发日志布局
        self.log_frame.grid(row=4, column=0, padx=12, pady=6, sticky="nsew")
        self.log_area.pack(expand=True, fill="both", padx=6, pady=6)
        self.clear_log_btn.pack(side="right", padx=6, pady=6)

        # 控制按钮布局
        self.control_frame.grid(row=5, column=0, pady=12, sticky="ew")
        self.start_btn.pack(side="left", padx=6)
        self.save_btn.pack(side="right", padx=6)

        # 布局权重配置
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)
        self.file_frame.columnconfigure(1, weight=1)
        self.keywords_frame.columnconfigure(0, weight=1)
        self.wxpusher_frame.columnconfigure(1, weight=1)

    def setup_bindings(self):
        self.root.bind('<Control-s>', lambda e: self.save_config())

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    self.keyword_list.delete(0, END)
                    for kw in self.config.get('keywords', []):
                        self.keyword_list.insert(END, kw)
                    self.interval_spin.set(self.config.get('interval', 1000))
                    self.push_interval_entry.delete(0, END)
                    self.push_interval_entry.insert(0, self.config.get('push_interval', 0))
                    self.app_token_entry.delete(0, END)
                    self.app_token_entry.insert(0, self.config.get('app_token', ''))
                    self.uid_entry.delete(0, END)
                    self.uid_entry.insert(0, self.config.get('uid', ''))
                    self.file_entry.delete(0, END)
                    self.file_entry.insert(0, self.config.get('log_path', ''))
                self.log_message("配置加载完成")
        except Exception as e:
            self.log_message(f"配置加载失败: {str(e)}", "ERROR")

    def save_config(self):
        try:
            config = {
                'interval': int(self.interval_spin.get()),
                'push_interval': int(self.push_interval_entry.get() or 0),
                'app_token': self.app_token_entry.get(),
                'uid': self.uid_entry.get(),
                'keywords': list(self.keyword_list.get(0, END)),
                'log_path': self.file_entry.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.log_message("配置保存成功")
        except Exception as e:
            self.log_message(f"配置保存失败: {str(e)}", "ERROR")

    def log_message(self, message, level="INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        color_map = {
            "INFO": "#333333",
            "DEBUG": "#666666",
            "WARN": "#d35400",
            "ERROR": "#c0392b",
            "ALERT": "#8e44ad"
        }
        self.log_area.configure(state='normal')
        self.log_area.tag_configure(level, foreground=color_map.get(level, "#333333"))
        self.log_area.insert(END, f"[{timestamp}] [{level}] {message}\n", level)
        self.log_area.configure(state='disabled')
        self.log_area.see(END)

    def clear_log(self):
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, END)
        self.log_area.configure(state='disabled')

    def add_keyword(self):
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

    def remove_selected_keyword(self):
        selection = self.keyword_list.curselection()
        if selection:
            keyword = self.keyword_list.get(selection[0])
            self.keyword_list.delete(selection[0])
            self.log_message(f"已移除关键词: {keyword}")

    def clear_keywords(self):
        if messagebox.askyesno("确认清空", "确定要清空所有关键词吗？"):
            self.keyword_list.delete(0, END)
            self.log_message("已清空关键词列表")

    def select_file(self):
        """选择文件时初始化编码"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_entry.delete(0, END)
            self.file_entry.insert(0, file_path)
            self.last_position = os.path.getsize(file_path)
            self.last_timestamp = self.get_last_timestamp(file_path)
            try:
                self.last_size = os.path.getsize(file_path)
                if self.detect_encoding(file_path):
                    # 显示测试内容
                    with open(file_path, 'rb') as f:
                        f.seek(0)
                        sample = f.read(200)
                        decoded_sample = self.decode_content(sample)
                        self.log_message(f"编码测试样本: {decoded_sample[:50]}...")
            except Exception as e:
                self.log_message(f"文件初始化失败: {str(e)}", "ERROR")

    def toggle_monitor(self):
        if not self.monitoring:
            if not self.validate_settings():
                return
            # 初始化监控状态
            file_path = self.file_entry.get()
            if os.path.exists(file_path):
                self.last_position = os.path.getsize(file_path)  # 关键修复：从当前文件末尾开始
                self.last_timestamp = self.get_last_timestamp(file_path)
            self.monitoring = True
            self.stop_event.clear()
            self.start_btn.config(text="⏹ 停止监控")
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            self.log_message("监控已启动")
        else:
            self.monitoring = False
            self.stop_event.set()
            self.start_btn.config(text="▶ 开始监控")
            self.log_message("监控已停止")

    def validate_settings(self):
        required = [
            (self.file_entry.get(), "请选择日志文件"),
            (self.app_token_entry.get(), "请输入App Token"),
            (self.uid_entry.get(), "请输入用户UID"),
            (self.keyword_list.size() > 0, "请至少添加一个关键词")
        ]
        for value, msg in required:
            if not value:
                self.log_message(msg, "ERROR")
                return False
        return True

    def parse_timestamp(self, line):
        """解析日志时间戳"""
        match = self.time_pattern.match(line)
        if match:
            try:
                return datetime.strptime(match.group(), "%Y/%m/%d %H:%M:%S")
            except ValueError:
                pass
        return None

    def monitor_loop(self):
        """增强版监控循环"""
        self.push_interval = int(self.push_interval_entry.get() or 0)
        while self.monitoring and not self.stop_event.is_set():
            try:
                file_path = self.file_entry.get()
                if not os.path.exists(file_path):
                    self.log_message("日志文件不存在，停止监控", "ERROR")
                    self.toggle_monitor()
                    return

                current_size = os.path.getsize(file_path)
                
                # 处理文件截断
                if current_size < self.last_position:
                    self.log_message("检测到文件被截断，重置读取位置", "WARN")
                    self.last_position = 0
                    self.last_timestamp = None

                # 读取新增内容
                if self.last_position < current_size:
                    with open(file_path, 'rb') as f:
                        f.seek(self.last_position)
                        content = f.read()
                        bytes_read = len(content)
                        self.last_position = f.tell()
                        
                        try:
                            decoded = self.decode_content(content)
                        except UnicodeDecodeError as ude:
                            self.log_message(f"解码失败: {str(ude)}，尝试重新检测编码...", "WARN")
                            if self.detect_encoding(file_path):
                                decoded = self.decode_content(content)
                            else:
                                continue

                        # 按行处理
                        lines = decoded.replace('\r\n', '\n').split('\n')
                        valid_lines = []
                        
                        # 时间戳过滤
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            line_timestamp = self.parse_timestamp(line)
                            
                            # 首次运行记录所有有效行
                            if not self.last_timestamp:
                                if line_timestamp:
                                    self.last_timestamp = line_timestamp
                                valid_lines.append(line)
                                continue
                            
                            # 只处理新时间戳日志
                            if line_timestamp and line_timestamp > self.last_timestamp:
                                valid_lines.append(line)

                        # 更新最后时间戳
                        if valid_lines:
                            last_line = valid_lines[-1]
                            new_timestamp = self.parse_timestamp(last_line)
                            if new_timestamp:
                                self.last_timestamp = new_timestamp
                            elif self.last_timestamp:  # 没有时间戳时使用最后位置
                                self.last_timestamp = datetime.now()

                        # 处理有效日志
                        if valid_lines:
                            self.log_message(f"发现 {len(valid_lines)} 条新日志", "INFO")
                            self.process_lines(valid_lines)

                time.sleep(int(self.interval_spin.get()) / 1000)
            
            except Exception as e:
                if self.monitoring:
                    self.log_message(f"监控异常: {str(e)}", "ERROR")
                time.sleep(1)

    def detect_encoding(self, file_path):
        """增强的编码检测方法"""
        try:
            with open(file_path, 'rb') as f:
                rawdata = f.read(10000)
                
                # 使用中文优先策略
                result = chardet.detect(rawdata)
                if result['encoding'] and 'gb' in result['encoding'].lower():
                    self.current_encoding = result['encoding']
                else:
                    # 尝试所有备选编码
                    for enc in ['utf-8-sig', 'gb18030', 'gbk', 'big5'] + self.fallback_encodings:
                        try:
                            rawdata.decode(enc)
                            self.current_encoding = enc
                            break
                        except:
                            continue
                
                # 验证编码有效性
                test_str = rawdata[:100].decode(self.current_encoding, errors='replace')
                if '�' in test_str:
                    raise UnicodeDecodeError("检测到替换字符，编码可能不正确")
                
                self.log_message(f"最终使用编码: {self.current_encoding}")
                return True
        except Exception as e:
            self.log_message(f"编码检测失败: {str(e)}，使用备选编码", "ERROR")
            self.current_encoding = 'gb18030'  # 中文最通用编码
            return False

    def decode_content(self, content):
        """多重编码尝试解码"""
        try:
            return content.decode(self.current_encoding)
        except UnicodeDecodeError:
            for enc in self.fallback_encodings:
                try:
                    return content.decode(enc)
                except:
                    continue
            return content.decode(self.current_encoding, errors='replace')

    def process_lines(self, lines):
        """处理日志条目（带推送间隔控制）"""
        current_time = time.time() * 1000  # 毫秒
        for line in lines:
            if self.stop_event.is_set():
                break
            
            # 推送间隔检查
            if self.push_interval > 0 and (current_time - self.last_push_time) < self.push_interval:
                continue

            # 提取内容
            content = self.extract_content(line)
            
            # 关键词匹配
            for kw in self.keyword_list.get(0, END):
                if kw in line:
                    self.send_wxpush(kw, content)
                    self.last_push_time = time.time() * 1000  # 更新推送时间
                    break

    def extract_content(self, line):
        """增强的内容提取方法"""
        markers = ['@來自', '@来自']  # 支持简繁体
        for marker in markers:
            index = line.find(marker)
            if index != -1:
                # 提取冒号后的内容（如果存在）
                colon_index = line.find(':', index)
                if colon_index != -1:
                    return line[colon_index+1:].strip()
                # 如果没有冒号，直接取标记后的内容
                return line[index + len(marker):].strip()
        return line

    def select_file(self):
        """选择文件时初始化时间戳"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_entry.delete(0, END)
            self.file_entry.insert(0, file_path)
            self.last_position = os.path.getsize(file_path)
            self.last_timestamp = self.get_last_timestamp(file_path)
            try:
                self.last_size = os.path.getsize(file_path)
                with open(file_path, 'rb') as f:
                    rawdata = f.read(10000)
                    result = chardet.detect(rawdata)
                    self.current_encoding = result['encoding'] or 'utf-8'
                    self.log_message(f"文件编码检测为: {self.current_encoding}")
            except Exception as e:
                self.log_message(f"文件初始化失败: {str(e)}", "ERROR")

    def get_last_timestamp(self, file_path):
        """获取文件的最后有效时间戳"""
        try:
            with open(file_path, 'rb') as f:
                f.seek(-10240, os.SEEK_END)  # 读取最后10KB内容
                content = f.read().decode(self.current_encoding, errors='ignore')
                for line in reversed(content.splitlines()):
                    ts = self.parse_timestamp(line)
                    if ts:
                        return ts
        except:
            pass
        return None

    def send_wxpush(self, keyword, content):
        """发送微信推送"""
        message = f"🔔 日志报警 [{keyword}]\n{content}"
        self.log_message(f"推送内容: {message}", "ALERT")
        try:
            response = requests.post(
                "http://wxpusher.zjiecode.com/api/send/message",
                json={
                    "appToken": self.app_token_entry.get(),
                    "content": message,
                    "contentType": 1,
                    "uids": [self.uid_entry.get()]
                },
                timeout=10
            )
            result = response.json()
            if result["code"] != 1000:
                raise Exception(result["msg"])
            self.log_message("推送成功", "INFO")
        except Exception as e:
            self.log_message(f"推送失败: {str(e)}", "ERROR")

if __name__ == "__main__":
    root = Tk()
    app = AdvancedLogMonitorPro(root)
    root.mainloop()
