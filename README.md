# POE2 Trade Pusher

POE2交易信息监控推送工具，支持关键词监控、WxPusher推送和系统托盘操作。

## 功能特点

- 实时监控游戏日志文件
- 支持多关键词匹配
- 使用WxPusher推送到微信
- 系统托盘运行
- 可自定义检测间隔和推送间隔
- 支持日志导出和清理
- 界面简洁美观

## 安装说明

1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 复制配置文件模板：
```bash
cp config.json.template config.json
```

3. 编辑config.json，填入以下信息：
- app_token：WxPusher的APP Token
- uid：WxPusher的用户UID
- log_path：POE2日志文件路径
- keywords：需要监控的关键词列表
- interval：检测间隔（毫秒）
- push_interval：推送间隔（毫秒，0表示立即推送）

## 使用方法

### 开发环境运行

```bash
python main.py
```

### 打包发布

```bash
# 安装PyInstaller
pip install pyinstaller

# 使用spec文件打包
pyinstaller build.spec
```

打包后的文件在dist目录下。

## WxPusher配置说明

1. 访问 [WxPusher官网](https://wxpusher.zjiecode.com) 注册账号
2. 创建应用，获取APP Token
3. 关注WxPusher公众号，获取用户UID
4. 将获取的APP Token和UID填入配置文件

## 注意事项

- 首次运行时需要选择POE2的日志文件路径
- 至少需要添加一个关键词才能开始监控
- 推荐使用系统托盘模式运行，可以最小化到托盘
- 如需停止监控，可以点击停止按钮或从托盘菜单停止

## 开发说明

项目使用模块化设计，便于后续扩展：

- core/：核心功能模块
  - config.py：配置管理
  - file_utils.py：文件处理工具
  - log_monitor.py：日志监控核心
- gui/：界面相关模块
  - main_window.py：主窗口
  - tray_icon.py：系统托盘
  - styles.py：界面样式
- push/：推送模块
  - base.py：推送基类
  - wxpusher.py：WxPusher实现

如需添加新的推送平台，只需：
1. 在push/目录下创建新的推送类
2. 继承PushBase类并实现相关方法
3. 在配置文件中添加相应的配置项
4. 在主窗口中添加相应的配置界面

## 免责声明

本软件是一个开源的游戏辅助工具，仅用于提供游戏信息的监控和推送服务。使用本软件时请注意：

1. 本软件不会以任何方式修改游戏文件或游戏进程。
2. 本软件仅通过读取游戏日志文件来获取信息，不会注入游戏进程或使用其他可能违反游戏服务条款的方式。
3. 使用本软件的风险由用户自行承担，开发者不对因使用本软件而可能导致的任何损失或问题负责。
4. 本软件不保证能够捕获所有交易信息，也不保证推送服务的稳定性和及时性。

## 使用许可

1. 本软件采用MIT开源协议。
2. 严禁将本软件用于商业用途，包括但不限于：
   - 销售本软件或其修改版本
   - 将本软件集成到付费服务中
   - 使用本软件提供收费服务
3. 如需修改和分发本软件，必须保持开源并附带原有的免责声明和使用许可。
4. 在遵守上述条件的前提下，您可以自由地使用和修改本软件。
