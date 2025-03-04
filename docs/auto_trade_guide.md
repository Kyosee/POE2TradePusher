# 自动交易功能使用说明

## 1. 环境准备

### 1.1 确保依赖安装
```bash
pip install -r requirements.txt
```

### 1.2 配置文件设置
编辑 config.json，确保以下配置正确：
```json
{
  "game_window": "Path of Exile 2",
  "auto_trade": {
    "enabled": false,
    "party_timeout_ms": 30000,
    "stash_interval_ms": 1000,
    "trade_interval_ms": 1000,
    "trade_timeout_ms": 10000
  }
}
```

## 2. 功能测试

### 2.1 运行前检查
1. 确保游戏已经启动
2. 确保角色在藏身处
3. 确保仓库已经整理好
4. 确保配置文件中的游戏窗口名称正确

### 2.2 模块测试
按以下顺序进行测试：

1. 测试游戏命令：
```python
from tests.test_auto_trade import test_game_command
test_game_command()
```

2. 测试仓库打开：
```python
from tests.test_auto_trade import test_open_stash
test_open_stash()
```

3. 测试物品取出：
```python
from tests.test_auto_trade import test_take_out_item
test_take_out_item()
```

4. 测试完整交易流程：
```python
from tests.test_auto_trade import test_auto_trade
test_auto_trade()
```

## 3. 功能说明

### 3.1 自动交易流程
1. 收到交易消息并解析
2. 邀请用户组队
3. 等待用户进入区域
4. 打开仓库取出物品
5. 发起交易请求
6. 等待交易完成

### 3.2 参数说明
- party_timeout_ms: 等待组队超时时间
- stash_interval_ms: 开仓取物间隔时间
- trade_interval_ms: 交易发起间隔时间
- trade_timeout_ms: 交易请求超时时间

### 3.3 错误处理
- 组队超时：自动踢出玩家
- 取物失败：取消交易并记录错误
- 交易超时：自动取消交易

## 4. 常见问题

### 4.1 游戏窗口无法找到
- 检查游戏是否运行
- 确认配置文件中的窗口名称正确
- 尝试以管理员身份运行程序

### 4.2 仓库操作失败
- 确保角色在藏身处
- 检查仓库标识图是否清晰可见
- 确认物品位置编号正确

### 4.3 交易超时
- 检查网络连接
- 调整超时时间设置
- 确认对方在线并响应

## 5. 调试建议

### 5.1 日志查看
- 检查控制台输出
- 查看状态更新信息
- 分析交易历史记录

### 5.2 参数调优
- 根据实际情况调整超时时间
- 适当增加操作间隔时间
- 优化交易模板匹配规则

### 5.3 安全建议
- 使用测试账号进行功能验证
- 从小额交易开始测试
- 定期检查交易历史记录
