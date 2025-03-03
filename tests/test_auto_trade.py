import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_modules.game_command import GameCommandModule
from core.process_modules.open_stash import OpenStashModule
from core.process_modules.take_out_item import TakeOutItemModule
from core.auto_trade import AutoTrade, TradeConfig

def test_game_command():
    """测试游戏命令模块"""
    module = GameCommandModule()
    result = module.run(command_text="/help")
    print(f"游戏命令测试结果: {result}")

def test_open_stash():
    """测试打开仓库模块"""
    module = OpenStashModule()
    result = module.run()
    print(f"打开仓库测试结果: {result}")
    return result

def test_take_out_item():
    """测试取物品模块"""
    module = TakeOutItemModule()
    result = module.run(p1_num=1, p2_num=None)
    print(f"取物品测试结果: {result}")
    return result

def test_auto_trade():
    """测试自动交易流程"""
    trade = AutoTrade()
    
    # 设置回调函数
    def status_callback(status):
        print(f"状态: {status}")
    
    def history_callback(record):
        print(f"历史: {record}")
    
    trade.set_callbacks(status_callback, history_callback)
    
    # 设置配置
    config = TradeConfig(
        party_timeout_ms=5000,  # 测试时使用较短的超时时间
        stash_interval_ms=1000,
        trade_interval_ms=1000,
        trade_timeout_ms=5000
    )
    trade.set_config(config)
    
    # 启用自动交易
    trade.enable()
    
    # 模拟交易消息
    test_message = "來自 TestUser: 你好，我想購買 TestItem 標價 1 divine 在 normal (倉庫頁 \"Test\"; 位置: left 1, right 2)"
    test_template = "來自 {@user}: 你好，我想購買 {@item} 標價 {@price} {@currency} 在 {@mode} (倉庫頁 \"{@tab}\"; 位置: {@p1} {@p1_num}, {@p2} {@p2_num})"
    
    # 处理交易消息
    trade.handle_trade_message(test_message, test_template)
    
    # 等待一段时间观察结果
    time.sleep(10)
    
    # 禁用自动交易
    trade.disable()

if __name__ == "__main__":
    # 测试游戏命令
    print("\n=== 测试游戏命令 ===")
    test_game_command()
    time.sleep(2)
    
    # 测试打开仓库
    print("\n=== 测试打开仓库 ===")
    if test_open_stash():
        time.sleep(2)
        
        # 测试取物品
        print("\n=== 测试取物品 ===")
        test_take_out_item()
        time.sleep(2)
    
    # 测试完整交易流程
    print("\n=== 测试自动交易 ===")
    test_auto_trade()
