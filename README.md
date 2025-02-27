# POE2 Trade Pusher

POE2 Trade Pusher 是一个用于《流放之路2》(Path of Exile 2) 的交易通知推送工具。它可以监控游戏日志文件，自动识别交易信息，并将其推送到指定的消息平台。

## 功能特点

- 实时监控游戏日志文件
- 自定义关键词匹配
- 可配置的检测和推送间隔
- 支持多种编码格式
- 使用 WxPusher 进行消息推送
- 界面简洁直观

## 打包说明

使用 PyInstaller 进行打包：

```bash
# 安装打包工具
pip install pyinstaller

# 打包命令
pyinstaller --noconsole --icon=assets/icon.ico --add-data "config.json;." --name POE2TradePusher main.py
```

打包后的文件将在 `dist/POE2TradePusher` 目录下生成。

## 使用说明

1. 下载并运行打包好的 exe 文件
2. 配置 config.json 文件，包括：
   - 日志文件路径
   - 检测间隔
   - 推送间隔
   - WxPusher 的 App Token 和 UID
   - 关键词列表
3. 启动程序后，点击"开始监控"即可

## 配置说明

config.json 文件格式如下：

```json
{
  "interval": 1000,
  "push_interval": 0,
  "app_token": "你的WxPusher App Token",
  "uid": "你的WxPusher UID",
  "keywords": ["关键词1", "关键词2"],
  "log_path": "游戏日志文件路径"
}
```

## 免责声明

1. 本工具仅用于识别和推送游戏内的交易信息，不会对游戏进行任何修改或干预。
2. 使用本工具导致的任何问题，作者不承担任何责任。
3. 本工具不会收集或传输任何个人信息，仅处理用户指定的日志文件内容。
4. 使用本工具时请遵守游戏相关协议和规则。

## 使用限制

1. 本工具仅供个人学习和研究使用。
2. 严禁用于商业用途。
3. 禁止对本工具进行二次打包、销售或用于其他商业行为。
4. 禁止将本工具用于任何非法用途。

## 版权声明

Copyright © 2025 POE2 Trade Pusher

保留所有权利。未经作者明确授权，禁止：
1. 进行商业化使用
2. 修改后再发布
3. 将本工具用于商业目的
4. 删除或修改本工具的版权信息

使用本工具即表示您同意遵守以上声明。
