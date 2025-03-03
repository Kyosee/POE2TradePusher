import time
import logging
import re
import win32con
import win32api
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable
from datetime import datetime

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
        
        # 初始化流程模块
        self.game_command = GameCommandModule()
        self.open_stash = OpenStashModule()
        self.take_out_item = TakeOutItemModule()

        self.logger = logging.getLogger("AutoTrade")

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
        self.log_history.append({
            'timestamp': time.time(),
            'message': log
        })
        # 只保留最近1分钟的日志
        cutoff_time = time.time() - 60
        self.log_history = [log for log in self.log_history 
                          if log['timestamp'] > cutoff_time]
        
        # 检查日志是否包含交易相关信息
        self._process_trade_log(log)

    def handle_trade_message(self, message: str, template: str):
        """处理交易消息，开始自动交易流程"""
        if not self.enabled or self.trade_state != TradeState.IDLE:
            return
        
        try:
            self.trade_start_time = time.time()

            # 解析交易消息
            parsed_data = self._parse_trade_message(message, template)
            if not parsed_data:
                self.update_status("交易消息解析失败")
                return

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
            
            # 打开仓库
            self.update_status("正在打开仓库")
            if not self.open_stash.run():
                self._handle_trade_fail("打开仓库失败")
                return
            time.sleep(self.config.stash_interval_ms / 1000)
            self.trade_state = TradeState.STASH_OPENED

            # 取出物品
            if self.current_p1_num:
                self.update_status(f"正在取出物品 {self.current_p1_num}")
                if not self.take_out_item.run(p1_num=self.current_p1_num, p2_num=self.current_p2_num):
                    self._handle_trade_fail("取出物品失败")
                    return
            self.trade_state = TradeState.ITEMS_TAKEN

            # 发起交易
            time.sleep(self.config.trade_interval_ms / 1000)
            self.press_esc()
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
            self.game_command.run(command_text=f"/kick {self.current_user}")
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
            # 将模板转换为正则表达式
            pattern = template
            # 替换占位符为正则捕获组
            pattern = pattern.replace("{@user}", "(?P<user>[^\s]+)")
            pattern = pattern.replace("{@p1_num}", "(?P<p1_num>\d+)")
            pattern = pattern.replace("{@p2_num}", "(?P<p2_num>\d+)")
            # 将其他特殊字符转义
            pattern = re.escape(pattern).replace("\{@user\}", "(?P<user>[^\s]+)")
            pattern = pattern.replace("\{@p1_num\}", "(?P<p1_num>\d+)")
            pattern = pattern.replace("\{@p2_num\}", "(?P<p2_num>\d+)")

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
        pattern = pattern.replace("*", ".*")  # 将*转换为正则表达式的.*

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
        self.add_log(log)

    def enable(self):
        """启用自动交易"""
        self.enabled = True
        self.trade_state = TradeState.IDLE
        self.update_status("自动交易已启用")

    def disable(self):
        """禁用自动交易"""
        self.enabled = False
        if self.current_user:
            self._handle_trade_fail("自动交易已禁用")
        else:
            self.trade_state = TradeState.IDLE
            self.update_status("自动交易已禁用")
