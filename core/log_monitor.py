import os
import time
import threading
import traceback
import re
from datetime import datetime
from .file_utils import FileUtils

class LogMonitor:
    """日志监控核心类"""
    def __init__(self, config, log_callback=None, stats_page=None):
        self.config = config
        self.push_handlers = []  # 推送处理器列表
        self.handlers = []  # 其他处理器列表(如自动交易处理器)
        self.log_callback = log_callback or (lambda msg, level: None)
        self.stats_page = stats_page
        
        # 文件监控相关参数
        self.file_utils = FileUtils(self.log_callback)
        self.last_position = 0
        self.last_timestamp = None
        self.monitoring = False
        self.stop_event = threading.Event()
        self.last_push_time = 0
        self.buffer_size = 8192
        
        # 临时触发器相关
        self.temp_triggers = {}  # 临时触发器字典 {trigger_id: {pattern, callback, timeout_ms, created_at}}
        self.trigger_id_counter = 0  # 触发器ID计数器
        self.triggers_lock = threading.Lock()  # 触发器操作锁
        
        # 交易统计数据
        self.trade_stats = {
            'total_trades': 0,  # 总交易消息数
            'currency_stats': {}  # 通货统计 {currency: total_amount}
        }
        
    def get_trade_stats(self):
        """获取交易统计数据"""
        return self.trade_stats
        
    def start(self):
        """开始监控"""
        if not self._validate_settings():
            return False
            
        try:
            # 初始化监控状态
            file_path = self.config.get('log_path')
            if os.path.exists(file_path):
                # 检查并转换文件编码
                success, is_utf8, msg = self.file_utils.detect_encoding(file_path)
                if not success:
                    self.log_callback(msg, "ERROR")
                    return False
                if not is_utf8:
                    success, msg = self.file_utils.convert_to_utf8(file_path)
                    if not success:
                        self.log_callback(msg, "ERROR")
                        return False
                    self.log_callback(msg, "FILE")
                
                self.last_position = os.path.getsize(file_path)
                self.last_timestamp = self.file_utils.get_last_timestamp(file_path)
                
            # 更新状态
            self.monitoring = True
            self.stop_event.clear()
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            self.log_callback("监控已启动", "SYSTEM")
            return True
            
        except Exception as e:
            self.log_callback(f"启动监控失败: {str(e)}", "ERROR")
            self.monitoring = False
            return False
            
    def stop(self):
        """停止监控"""
        self.monitoring = False
        self.stop_event.set()
        self.log_callback("监控已停止", "SYSTEM")
        
    def add_push_handler(self, handler):
        """添加推送处理器"""
        if handler:
            self.push_handlers.append(handler)
            self.log_callback("已添加推送处理器", "SYSTEM")
            
    def add_handler(self, handler):
        """添加其他处理器（如自动交易处理器）"""
        if handler:
            # 如果是AutoTrade处理器，设置log_monitor引用
            if hasattr(handler, 'set_log_monitor'):
                handler.set_log_monitor(self)
            self.handlers.append(handler)
            self.log_callback("已添加处理器", "SYSTEM")
            
    def _send_push_message(self, title, content):
        """发送推送消息到所有处理器"""
        results = []
        for handler in self.push_handlers:
            try:
                result, msg = handler.send(title, content)
                results.append(result)
                if not result:
                    self.log_callback(f"推送消息失败: {msg}", "ERROR")
            except Exception as e:
                self.log_callback(f"推送消息失败: {str(e)}", "ERROR")
                results.append(False)
        return any(results)  # 至少有一个推送成功就返回True
            
    def _validate_settings(self):
        """验证设置完整性"""
        required = [
            (self.config.get('log_path'), "请选择日志文件"),
            (len(self.push_handlers) > 0, "未配置推送处理器"),
            (len(self.config.get('keywords', [])) > 0, "请至少添加一个关键词")
        ]
        
        for value, msg in required:
            if not value:
                self.log_callback(msg, "ERROR")
                return False
                
        return True
        
    def _monitor_loop(self):
        """监控日志文件循环"""
        interval = self.config.get('interval', 1000)
        push_interval = self.config.get('push_interval', 0)
        self.log_callback(f"检测间隔: {interval}ms, 推送间隔: {push_interval}ms", "SYSTEM")
        
        while self.monitoring and not self.stop_event.is_set():
            try:
                self._process_log_file()
                time.sleep(interval / 1000)
            except Exception as e:
                if self.monitoring:
                    self.log_callback(f"监控异常: {str(e)}", "ERROR")
                    self.log_callback(traceback.format_exc(), "DEBUG")
                time.sleep(1)
                
    def _process_log_file(self):
        """处理日志文件更新"""
        file_path = self.config.get('log_path')
        
        # 检查文件存在
        if not os.path.exists(file_path):
            self.log_callback("日志文件不存在，停止监控", "ERROR")
            self.stop()
            return

        current_size = os.path.getsize(file_path)
        
        # 处理文件截断
        if current_size < self.last_position:
            self.log_callback("检测到文件被截断，重置读取位置", "FILE")
            self.last_position = 0
            self.last_timestamp = None

        # 读取新增内容
        if self.last_position < current_size:
            with open(file_path, 'rb') as f:
                f.seek(self.last_position)
                content = f.read()
                self.last_position = f.tell()
                
                # 解码内容
                try:
                    decoded = self.file_utils.decode_content(content)
                except UnicodeDecodeError as ude:
                    self.log_callback(f"解码失败: {str(ude)}，尝试重新检测编码...", "FILE")
                    success, _, msg = self.file_utils.detect_encoding(file_path)
                    if success:
                        decoded = self.file_utils.decode_content(content)
                    else:
                        self.log_callback(msg, "ERROR")
                        return

                # 处理日志行
                self._process_log_lines(decoded)
                
    def _process_log_lines(self, content):
        """处理日志内容"""
        # 分割
        lines = content.replace('\r\n', '\n').split('\n')
        valid_lines = []
        
        # 时间戳过滤
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_timestamp = self.file_utils.parse_timestamp(line)
            
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
            new_timestamp = self.file_utils.parse_timestamp(last_line)
            if new_timestamp:
                self.last_timestamp = new_timestamp
            elif self.last_timestamp:  # 没有时间戳时使用最后位置
                self.last_timestamp = datetime.now()

        # 处理有效日志
        if valid_lines:
            self.log_callback(f"发现 {len(valid_lines)} 条新日志", "FILE")
            self._process_lines(valid_lines)
            
    def _process_lines(self, lines):
        """处理日志条目（带推送间隔控制）"""
        current_time = time.time() * 1000  # 毫秒
        push_interval = self.config.get('push_interval', 0)
        
        # 首先确保所有日志都发送到处理器，与推送无关
        for line in lines:
            if self.stop_event.is_set():
                break
            
            # 处理临时触发器
            self._process_temp_triggers(line)
            
            # 更新所有处理器的日志 - 使用线程池异步处理以避免阻塞
            for handler in self.handlers:
                try:
                    if hasattr(handler, 'handle_game_log'):
                        # 使用线程池来异步处理游戏日志，避免阻塞主监控线程
                        threading.Thread(
                            target=self._safe_handle_game_log,
                            args=(handler, line),
                            daemon=True
                        ).start()
                except Exception as handler_error:
                    # 捕获处理器异常，防止影响主循环
                    self.log_callback(f"处理器处理日志异常: {str(handler_error)}", "ERROR")

        # 推送间隔检查
        if push_interval > 0 and (current_time - self.last_push_time) < push_interval:
            # 只跳过推送，不影响日志处理
            return
            
        # 处理推送和关键词匹配
        for line in lines:
            if self.stop_event.is_set():
                break
                
            # 关键词匹配（支持多关键词组合）
            for kw in self.config.get('keywords', []):
                if self.stop_event.is_set():
                    break
                    
                try:
                    pattern = kw.get('pattern', '')
                    mode = kw.get('mode', '消息模式')
                    
                    # 消息模式匹配
                    if mode == '消息模式' and self._match_message_mode(pattern, line):
                        # 记录消息模式匹配日志
                        log_msg = (
                            f"[消息模式]关键词触发\n"
                            f"触发内容: {line}\n"
                            f"触发模板: {pattern}"
                        )
                        self.log_callback(log_msg, "INFO")
                        
                        self._send_push_message(pattern, line)
                        self.last_push_time = time.time() * 1000
                    
                    # 交易模式匹配
                    elif mode == '交易模式':
                        match_result = self._match_trade_mode(pattern, line)
                        if match_result:
                            # 记录交易模式匹配日志
                            log_msg = (
                                f"[交易模式]关键词触发\n"
                                f"触发内容: {line}\n"
                                f"触发模板: {pattern}\n"
                                f"解析信息:\n" + 
                                "\n".join(f"  {k}: {v}" for k, v in match_result.items())
                            )
                            self.log_callback(log_msg, "TRADE")
                            
                            # 触发自动交易处理器 - 使用专用线程处理，避免阻塞监控线程
                            for handler in self.handlers:
                                if hasattr(handler, 'handle_trade_message'):
                                    threading.Thread(
                                        target=self._safe_handle_trade,
                                        args=(handler, line, pattern),
                                        daemon=True
                                    ).start()

                            self._send_push_message(pattern, line)
                            self.last_push_time = time.time() * 1000
                            
                            # 更新交易统计
                            if self.stats_page:
                                try:
                                    self.stats_page.increment_message_count()
                                    self.log_callback(f"交易计数已更新", "SYSTEM")
                                except Exception as stats_error:
                                    self.log_callback(f"更新统计数据异常: {str(stats_error)}", "ERROR")
                            
                            # 提取通货数量和单位
                            try:
                                currency = match_result.get('currency')
                                amount = float(match_result.get('price', 0))
                                if currency and amount > 0 and self.stats_page:
                                    self.stats_page.update_currency_stats(currency, amount)
                                    self.log_callback(f"更新通货统计: {currency} {amount}", "PRICE")
                            except (ValueError, Exception) as price_error:
                                self.log_callback(f"处理价格数据异常: {str(price_error)}", "ERROR")
                except Exception as kw_error:
                    # 捕获关键词处理过程中的异常，防止影响整个循环
                    self.log_callback(f"关键词匹配处理异常: {str(kw_error)}", "ERROR")
    
    def _safe_handle_game_log(self, handler, log):
        """安全地处理游戏日志"""
        try:
            handler.handle_game_log(log)
        except Exception as e:
            self.log_callback(f"处理器处理日志异常: {str(e)}", "ERROR")
    
    def _safe_handle_trade(self, handler, message, pattern):
        """安全地处理交易消息"""
        try:
            handler.handle_trade_message(message, pattern)
        except Exception as e:
            self.log_callback(f"处理器处理交易异常: {str(e)}", "ERROR")
            
    def _match_message_mode(self, pattern, content):
        """消息模式匹配"""
        if '|' in pattern:
            # 多关键词组合模式
            keywords = [k.strip() for k in pattern.split('|')]
            return all(keyword in content for keyword in keywords)
        else:
            # 单关键词模式
            return pattern in content
            
    def _match_trade_mode(self, pattern, content):
        """交易模式匹配，返回提取的变量值"""
        # 转换模板为正则表达式
        template = pattern.replace('*', '.*?')
        template = template.replace('(', '\(')
        template = template.replace(')', '\)')
        # 定义占位符列表
        placeholders = [
            '@user', '@item', '@price', '@currency', '@mode',
            '@tab', '@p1', '@p1_num', '@p2', '@p2_num'
        ]
        
        # 替换占位符为命名捕获组
        for ph in placeholders:
            template = template.replace('{' + ph + '}', f'(?P<{ph[1:]}>[^{{}}]+)')
            
        # 执行匹配
        match = re.match(template, content)
        if match:
            return match.groupdict()
        return None
        
    def add_temp_trigger(self, pattern, callback, timeout_ms=30000):
        """添加临时触发器
        
        Args:
            pattern: 匹配模式（正则表达式）
            callback: 回调函数，接收匹配的日志行作为参数
            timeout_ms: 超时时间（毫秒），默认30秒
            
        Returns:
            str: 触发器ID，用于后续移除
        """
        with self.triggers_lock:
            trigger_id = f"trigger_{self.trigger_id_counter}"
            self.trigger_id_counter += 1
            
            self.temp_triggers[trigger_id] = {
                'pattern': pattern,
                'callback': callback,
                'timeout_ms': timeout_ms,
                'created_at': time.time() * 1000  # 毫秒时间戳
            }
            
            self.log_callback(f"添加临时触发器: {trigger_id}, 模式: {pattern}, 超时: {timeout_ms}ms", "SYSTEM")
            return trigger_id
            
    def remove_temp_trigger(self, trigger_id):
        """移除临时触发器
        
        Args:
            trigger_id: 触发器ID
            
        Returns:
            bool: 是否成功移除
        """
        with self.triggers_lock:
            if trigger_id in self.temp_triggers:
                del self.temp_triggers[trigger_id]
                self.log_callback(f"已移除临时触发器: {trigger_id}", "SYSTEM")
                return True
            return False
            
    def _process_temp_triggers(self, log_line):
        """处理临时触发器
        
        Args:
            log_line: 日志行
        """
        current_time = time.time() * 1000  # 毫秒
        expired_triggers = []
        triggered_ids = []
        
        # 使用锁保护触发器字典的访问
        with self.triggers_lock:
            # 检查是否有触发器已过期
            for trigger_id, trigger_info in self.temp_triggers.items():
                created_at = trigger_info['created_at']
                timeout_ms = trigger_info['timeout_ms']
                
                # 检查是否超时
                if current_time - created_at > timeout_ms:
                    expired_triggers.append(trigger_id)
                    continue
                    
                # 检查是否匹配
                pattern = trigger_info['pattern']
                if re.search(pattern, log_line):
                    # 调用回调函数
                    try:
                        trigger_info['callback'](log_line)
                        self.log_callback(f"触发器 {trigger_id} 匹配成功: {log_line[:50]}...", "SYSTEM")
                        triggered_ids.append(trigger_id)
                    except Exception as e:
                        self.log_callback(f"触发器回调执行异常: {str(e)}", "ERROR")
            
            # 移除已触发的触发器
            for trigger_id in triggered_ids:
                if trigger_id in self.temp_triggers:
                    del self.temp_triggers[trigger_id]
                    
            # 移除过期的触发器
            for trigger_id in expired_triggers:
                if trigger_id in self.temp_triggers:
                    self.log_callback(f"触发器 {trigger_id} 已超时", "SYSTEM")
                    del self.temp_triggers[trigger_id]
