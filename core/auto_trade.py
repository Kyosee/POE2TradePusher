import time
import logging
import re
import win32con
import win32api
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable, List
from datetime import datetime
import json
import os
import threading
import queue

from core.process_modules.game_command import GameCommandModule
from core.process_modules.open_stash import OpenStashModule
from core.process_modules.take_out_item import TakeOutItemModule

class TradeState(Enum):
    """交易状态枚举"""
    IDLE = "空闲"
    INVITING = "等待入组"
    JOINED = "已入组"
    STASH_OPENED = "仓库已打开"
    ITEMS_TAKEN = "物品已取出"
    TRADE_REQUESTED = "已发起交易"
    TRADE_ACCEPTED = "交易已接受"
    TRADE_COMPLETED = "交易完成"
    TRADE_CANCELLED = "交易取消"
    TRADE_FAILED = "交易失败"

@dataclass
class TradeConfig:
    """自动交易配置类"""
    party_timeout_ms: int = 30000
    stash_interval_ms: int = 1000
    trade_interval_ms: int = 1000
    trade_timeout_ms: int = 10000

class AutoTrade:
    def __init__(self):
        self.config = TradeConfig()
        self.enabled = False
        self.current_trade = None
        self.status_callback = None
        self.history_callback = None
        self.log_history = []
        self.trade_state = TradeState.IDLE
        
        # 当前交易信息
        self.current_user = None
        self.current_p1_num = None
        self.current_p2_num = None
        self.trade_start_time = None
        
        # 交易模式关键词模板缓存
        self.trade_templates = []
        
        # 初始化流程模块
        self.game_command = GameCommandModule()
        self.open_stash = OpenStashModule()
        self.take_out_item = TakeOutItemModule()

        self.logger = logging.getLogger("AutoTrade")
        
        # 添加Toast提示功能
        try:
            from gui.widgets.toast import show_toast, Toast
            self.has_toast = True
            self.show_toast = show_toast
            self.Toast = Toast
            # 保存原始error方法
            self._original_error = self.logger.error
            # 重写error方法
            self.logger.error = self._error_with_toast
        except ImportError:
            self.has_toast = False
            
        # 使用队列和专用线程处理交易请求
        self.trade_queue = queue.Queue()
        self.trade_thread = None
        self.trade_thread_running = False
        
        # 添加交易处理锁，确保一次只处理一个交易
        self.trade_lock = threading.Lock()
        
        # 从配置文件读取初始状态
        self._load_config_state()
            
    def _error_with_toast(self, msg, *args, **kwargs):
        """带Toast提示的错误日志方法"""
        # 调用原始的error方法记录日志
        self._original_error(msg, *args, **kwargs)
        
        # 如果Toast组件可用，显示Toast提示
        if self.has_toast:
            # 获取主窗口实例（如果存在）
            from PySide6.QtWidgets import QApplication
            parent = None
            if QApplication.instance() and QApplication.activeWindow():
                parent = QApplication.activeWindow()
            
            # 显示Toast提示
            self.show_toast(parent, "交易错误", str(msg), self.Toast.ERROR)

    def set_config(self, config: TradeConfig):
        """更新交易配置"""
        self.config = config

    def set_callbacks(self, 
                     status_callback: Callable[[str], None],
                     history_callback: Callable[[str], None]):
        """设置状态和历史记录回调函数"""
        self.status_callback = status_callback
        self.history_callback = history_callback

    def update_status(self, status: str):
        """更新交易状态"""
        if self.status_callback:
            self.status_callback(f"[{self.trade_state.value}] {status}")
        self.logger.info(f"Trade Status: {status}")

    def add_history(self, message: str):
        """添加交易历史记录"""
        record = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        if self.history_callback:
            self.history_callback(record)
        self.logger.info(f"Trade History: {record}")

    def add_log(self, log: str):
        """添加日志消息到历史记录"""
        try:
            self.log_history.append({
                'timestamp': time.time(),
                'message': log
            })
            # 只保留最近1分钟的日志
            cutoff_time = time.time() - 60
            self.log_history = [l for l in self.log_history 
                              if l['timestamp'] > cutoff_time]
            
            # 检查日志是否包含交易相关信息并立即处理
            self._process_trade_log(log)
            
            # 添加调试日志
            self.logger.debug(f"游戏日志已记录: {log[:50]}...")
        except Exception as e:
            # 确保日志处理异常不会影响监控线程
            self.logger.error(f"日志处理异常: {str(e)}")

    def handle_trade_message(self, message: str, template: str):
        """处理交易消息，将请求放入队列"""
        # 快速检查是否启用了自动交易
        if not self.enabled:
            self.logger.debug("自动交易已禁用，忽略交易消息")
            return
        
        # 将交易请求添加到队列
        self.trade_queue.put((message, template))
        self.logger.debug(f"交易请求已加入队列: {message[:30]}...")

    def _process_trade_request(self, message: str, template: str):
        """处理单个交易请求"""
        # 获取锁以确保同一时间只有一个交易进行
        with self.trade_lock:
            try:
                # 如果未启用或当前有交易正在进行，则忽略新的交易消息
                if not self.enabled or self.trade_state != TradeState.IDLE:
                    self.logger.info(f"忽略交易消息: {'自动交易已禁用' if not self.enabled else '当前有交易正在进行'}")
                    return
                
                # 更新交易模板
                self._load_trade_templates()
                    
                # 尝试使用所有交易模式的模板解析交易消息
                parsed_data = None
                
                # 先尝试使用传入的模板解析
                parsed_data = self._parse_trade_message(message, template)
                
                # 如果失败，尝试使用其他交易模板
                if not parsed_data:
                    for trade_template in self.trade_templates:
                        if trade_template != template:  # 避免重复尝试相同模板
                            parsed_data = self._parse_trade_message(message, trade_template)
                            if parsed_data:
                                break
                
                if not parsed_data:
                    self.logger.warning(f"无法解析交易消息: {message}")
                    return
                
                # 处理交易流程
                self._process_trade(parsed_data, message)
                    
            except Exception as e:
                self.update_status(f"交易过程出错: {str(e)}")
                self.logger.error(f"Trade error: {str(e)}", exc_info=True)
                self._handle_trade_fail(str(e))

    def _process_trade(self, parsed_data, message):
        """处理交易流程的核心逻辑，从解析数据开始"""
        try:
            self.trade_start_time = time.time()

            self.current_user = parsed_data.get("user")
            self.current_p1_num = parsed_data.get("p1_num")
            self.current_p2_num = parsed_data.get("p2_num")

            self.update_status(f"开始与用户 {self.current_user} 的自动交易")
            self.trade_state = TradeState.INVITING
            
            # 邀请用户组队
            self.game_command.run(command_text=f"/invite {self.current_user}")
            self.update_status(f"已发送组队邀请给 {self.current_user}")

            # 等待用户进入
            join_pattern = f"*{self.current_user} 進入了此區域。"
            if not self._wait_for_join(join_pattern, self.config.party_timeout_ms):
                self._handle_trade_fail("用户加入超时")
                return

            self.trade_state = TradeState.JOINED
            self.update_status(f"用户 {self.current_user} 已加入区域")
            
            # 打开仓库
            self.update_status("正在打开仓库")
            if not self.open_stash.run():
                self._handle_trade_fail("打开仓库失败")
                return
            time.sleep(self.config.stash_interval_ms / 1000)
            self.trade_state = TradeState.STASH_OPENED

            # 取出物品
            if self.current_p1_num and self.current_p2_num:
                self.update_status(f"正在取出物品位置: {self.current_p1_num}, {self.current_p2_num}")
                if not self.take_out_item.run(p1_num=int(self.current_p1_num), p2_num=int(self.current_p2_num)):
                    self._handle_trade_fail("取出物品失败")
                    return
                self.trade_state = TradeState.ITEMS_TAKEN
            else:
                self.logger.warning("未提供物品位置信息，跳过取出物品步骤")

            # 发起交易
            time.sleep(self.config.trade_interval_ms / 1000)
            self.press_esc()  # 先按ESC关闭可能打开的仓库
            time.sleep(0.2)
            
            self.game_command.run(command_text=f"/tradewith {self.current_user}")
            self.update_status(f"已向 {self.current_user} 发起交易请求")
            self.trade_state = TradeState.TRADE_REQUESTED

            # 等待交易完成或超时
            trade_request_time = time.time()
            while time.time() - trade_request_time < self.config.trade_timeout_ms / 1000:
                if self.trade_state in [TradeState.TRADE_COMPLETED, 
                                      TradeState.TRADE_CANCELLED, 
                                      TradeState.TRADE_FAILED]:
                    break
                time.sleep(0.1)

            if self.trade_state != TradeState.TRADE_COMPLETED:
                self._handle_trade_fail("交易请求超时")
                return

        except Exception as e:
            self.update_status(f"交易过程出错: {str(e)}")
            self.logger.error(f"Trade error: {str(e)}", exc_info=True)
            self._handle_trade_fail(str(e))

    def _handle_trade_fail(self, reason: str):
        """处理交易失败"""
        self.trade_state = TradeState.TRADE_FAILED
        if self.current_user:
            try:
                self.game_command.run(command_text=f"/kick {self.current_user}")
            except Exception as e:
                self.logger.error(f"踢出用户失败: {str(e)}")
                
        self.update_status(f"交易失败: {reason}")
        self.add_history(
            f"交易失败 - 用户: {self.current_user}, "
            f"物品: {self.current_p1_num},{self.current_p2_num}, "
            f"原因: {reason}"
        )
        self._reset_trade()

    def _reset_trade(self):
        """重置交易状态"""
        self.trade_state = TradeState.IDLE
        self.current_user = None
        self.current_p1_num = None
        self.current_p2_num = None
        self.trade_start_time = None
        self.update_status("等待新的交易请求")

    def _process_trade_log(self, log: str):
        """处理交易相关的游戏日志"""
        if not self.current_user:
            return
            
        # 检查用户是否已进入区域
        join_pattern = f".*{self.current_user} 進入了此區域。"
        if re.match(join_pattern, log):
            self.trade_state = TradeState.JOINED
            self.update_status(f"用户 {self.current_user} 已进入区域")
            return

        # 检查交易是否被接受
        accept_pattern = f".*{self.current_user} 已接受交易。"
        if re.match(accept_pattern, log):
            self.trade_state = TradeState.TRADE_ACCEPTED
            self.update_status("对方已接受交易")
            return

        # 检查交易是否完成
        complete_pattern = f".*與 {self.current_user} 的交易完成。"
        if re.match(complete_pattern, log):
            self.trade_state = TradeState.TRADE_COMPLETED
            duration = time.time() - self.trade_start_time
            self.update_status("交易完成")
            self.add_history(
                f"交易完成 - 用户: {self.current_user}, "
                f"物品: {self.current_p1_num},{self.current_p2_num}, "
                f"用时: {duration:.1f}秒"
            )
            self._reset_trade()
            return

        # 检查交易是否被取消
        cancel_pattern = f".*交易取消。"
        if re.match(cancel_pattern, log):
            self._handle_trade_fail("交易被取消")
            return

    def _parse_trade_message(self, message: str, template: str) -> Optional[dict]:
        """解析交易消息，提取关键信息"""
        try:
            # 将模板中的*替换为通配符
            template = template.replace('*', '.*?')
            # 处理正则表达式特殊字符转义
            template = template.replace('(', '\(')
            template = template.replace(')', '\)')
            
            # 替换占位符为捕获组
            placeholders = [
                '@user', '@item', '@price', '@currency', '@mode',
                '@tab', '@p1', '@p1_num', '@p2', '@p2_num'
            ]
            
            # 创建模式字符串
            pattern = template
            for ph in placeholders:
                pattern = pattern.replace('{' + ph + '}', f'(?P<{ph[1:]}>[^{{}}]+)')
            
            # 尝试匹配消息
            match = re.match(pattern, message)
            if match:
                return match.groupdict()
            return None

        except Exception as e:
            self.logger.error(f"Message parsing error: {str(e)}", exc_info=True)
            return None

    def _wait_for_join(self, pattern: str, timeout_ms: int) -> bool:
        """等待用户加入，检查日志中是否出现加入信息"""
        start_time = time.time()
        pattern = pattern.replace("*", ".*?")  # 将*转换为正则表达式的.*

        while time.time() - start_time < timeout_ms / 1000:
            # 检查最近的日志
            for log in reversed(self.log_history):
                if re.search(pattern, log['message']):
                    return True
            time.sleep(0.1)

        return False

    def press_esc(self):
        """模拟按下ESC键"""
        VK_ESCAPE = 0x1B
        # 按下ESC
        win32api.keybd_event(VK_ESCAPE, 0, 0, 0)
        time.sleep(0.1)  # 短暂延迟
        # 释放ESC
        win32api.keybd_event(VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)

    def handle_game_log(self, log: str):
        """处理游戏日志"""
        try:
            # 这里只记录日志，不再直接处理交易相关状态变化
            self.add_log(log)
        except Exception as e:
            # 确保即使有异常也不会传播到调用者
            self.logger.error(f"游戏日志处理异常: {str(e)}")

    def enable(self):
        """启用自动交易"""
        # 更新交易模板
        self._load_trade_templates()
        
        if not self.trade_templates:
            self.logger.warning("未找到交易模板，自动交易功能可能无法正常工作")
        else:
            self.logger.info(f"已加载 {len(self.trade_templates)} 个交易模板")
        
        self.enabled = True
        self.trade_state = TradeState.IDLE
        self.update_status("自动交易已启用")
        
        # 启动交易处理线程
        self._start_trade_thread()
        
        # 更新配置文件
        self._update_config_state(True)

    def disable(self):
        """禁用自动交易"""
        self.enabled = False
        
        # 停止交易处理线程
        self._stop_trade_thread()
        
        if self.current_user:
            self._handle_trade_fail("自动交易已禁用")
        else:
            self.trade_state = TradeState.IDLE
            self.update_status("自动交易已禁用")
            
        # 更新配置文件
        self._update_config_state(False)
            
    def _update_config_state(self, enabled):
        """更新配置文件中的自动交易状态"""
        config_path = 'config.json'
        if not os.path.exists(config_path):
            self.logger.warning("配置文件不存在，无法更新自动交易状态")
            return
            
        try:
            # 读取当前配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新自动交易状态
            if 'auto_trade' not in config:
                config['auto_trade'] = {}
            
            config['auto_trade']['enabled'] = enabled
            
            # 写入配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"已更新配置文件中的自动交易状态: {'启用' if enabled else '禁用'}")
            
        except Exception as e:
            self.logger.error(f"更新配置文件失败: {str(e)}")

    def _load_config_state(self):
        """从配置文件加载自动交易状态和配置"""
        config_path = 'config.json'
        if not os.path.exists(config_path):
            self.logger.warning("配置文件不存在，无法加载自动交易状态")
            return
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 读取自动交易配置
                auto_trade_config = config.get('auto_trade', {})
                
                # 更新启用状态
                self.enabled = auto_trade_config.get('enabled', False)
                
                # 更新配置参数
                self.config = TradeConfig(
                    party_timeout_ms=auto_trade_config.get('party_timeout_ms', 30000),
                    trade_timeout_ms=auto_trade_config.get('trade_timeout_ms', 10000),
                    stash_interval_ms=auto_trade_config.get('stash_interval_ms', 1000),
                    trade_interval_ms=auto_trade_config.get('trade_interval_ms', 1000)
                )
                
                # 加载交易模板
                self._load_trade_templates()
                
                self.logger.info(f"已从配置加载自动交易状态: {'启用' if self.enabled else '禁用'}")
                
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")

    def _load_trade_templates(self):
        """从配置文件加载交易模式的关键词模板"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.trade_templates = []
                
                # 从关键词中获取交易模式的模板
                for kw in config.get('keywords', []):
                    if kw.get('mode') == '交易模式':
                        self.trade_templates.append(kw.get('pattern'))
                
                if not self.trade_templates:
                    self.logger.warning("未找到交易模式关键词模板，自动交易功能可能无法正常工作")
        except Exception as e:
            self.logger.error(f"读取配置文件失败: {str(e)}")
            self.trade_templates = []

    def _start_trade_thread(self):
        """启动交易处理线程"""
        if self.trade_thread is not None and self.trade_thread.is_alive():
            return  # 线程已经在运行
            
        self.trade_thread_running = True
        self.trade_thread = threading.Thread(
            target=self._trade_worker,
            daemon=True
        )
        self.trade_thread.start()
        self.logger.info("交易处理线程已启动")
        
    def _stop_trade_thread(self):
        """停止交易处理线程"""
        self.trade_thread_running = False
        # 添加哨兵值确保线程能够退出
        if self.trade_thread and self.trade_thread.is_alive():
            self.trade_queue.put((None, None))
            self.trade_thread.join(timeout=2.0)
            self.logger.info("交易处理线程已停止")
    
    def _trade_worker(self):
        """交易处理工作线程"""
        self.logger.info("交易处理线程开始运行")
        while self.trade_thread_running:
            try:
                # 从队列获取交易请求，设置超时以便能够响应停止信号
                try:
                    message, template = self.trade_queue.get(timeout=1.0)
                    
                    # 检查是否是停止信号
                    if message is None and template is None:
                        break
                        
                    # 处理交易请求
                    self._process_trade_request(message, template)
                    
                except queue.Empty:
                    # 队列为空，继续等待
                    continue
                    
            except Exception as e:
                self.logger.error(f"交易处理线程异常: {str(e)}", exc_info=True)
                # 短暂暂停防止CPU占用过高
                time.sleep(1.0)
        
        self.logger.info("交易处理线程已结束")
