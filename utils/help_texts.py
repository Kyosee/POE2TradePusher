"""
帮助文本模块
统一管理应用程序中的各种帮助和说明文本
"""

# 关键词帮助文本
KEYWORD_HELP = """关键词使用帮助：

1. 消息模式：
   - 简单文本匹配，支持使用 | 符号进行分隔，表示多个关键词同时匹配
   - 例如：购买|你好，表示同时包含"购买"和"你好"的消息会被匹配

2. 交易模式 (限制只能有一个):
   - 使用模板格式，支持提取交易信息
   - 使用 {@xxx} 表示占位符，可被自动提取
   - 支持的占位符：
     {@user} - 用户名
     {@item} - 物品名称
     {@price} - 价格数量
     {@currency} - 货币类型
     {@mode} - 交易模式
     {@tab} - 仓库页名称
     {@p1}/{@p2} - 位置坐标
     {@p1_num}/{@p2_num} - 位置数字

注意：交易模式的关键词模板必须完全匹配游戏中的交易消息格式。
"""

# WxPusher帮助文本
WXPUSHER_HELP = (
    "WxPusher配置说明：\n\n"
    "1. 访问 http://wxpusher.zjiecode.com 注册登录\n\n"
    "2. 创建应用：\n"
    "   - 进入应用管理页面\n"
    "   - 点击「新建应用」\n"
    "   - 填写应用名称等信息\n"
    "   - 创建后可获取 App Token\n\n"
    "3. 获取用户UID：\n"
    "   - 使用微信扫码关注公众号\n"
    "   - 进入用户管理页面\n"
    "   - 可以看到你的用户UID\n\n"
    "4. 填写配置：\n"
    "   - 将获取到的 App Token 和 UID 填入对应输入框\n"
    "   - 点击测试按钮验证配置是否正确"
)

# Server酱帮助文本
SERVERCHAN_HELP = (
    "Server酱配置说明：\n\n"
    "1. 访问 https://sct.ftqq.com/ 注册登录\n\n"
    "2. 获取SendKey：\n"
    "   - 登录后在「Key&API」页面\n"
    "   - 复制SendKey\n\n"
    "3. 填写配置：\n"
    "   - 将获取到的SendKey填入输入框\n"
    "   - 点击测试按钮验证配置是否正确"
)

# Qmsg酱帮助文本
QMSG_HELP = (
    "Qmsg酱配置说明：\n\n"
    "1. 访问 https://qmsg.zendee.cn/ 注册登录\n\n"
    "2. 获取Key：\n"
    "   - 登录后在管理台创建QQ机器人\n"
    "   - 获取机器人Key\n\n"
    "3. 配置接收QQ：\n"
    "   - 输入需要接收消息的QQ号\n"
    "   - 确保该QQ已经添加了Qmsg酱机器人为好友\n\n"
    "4. 填写配置：\n"
    "   - 将获取到的Key和接收QQ填入对应输入框\n"
    "   - 点击测试按钮验证配置是否正确"
)

# 邮箱帮助文本
EMAIL_HELP = (
    "邮箱配置说明（以QQ邮箱为例）：\n\n"
    "1. SMTP服务器和端口：\n"
    "   - SMTP服务器：smtp.qq.com\n"
    "   - SMTP端口：465（SSL）\n\n"
    "2. 获取授权码：\n"
    "   - 登录QQ邮箱网页版\n"
    "   - 打开「设置」-「账户」\n"
    "   - 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」\n"
    "   - 开启「POP3/SMTP服务」\n"
    "   - 按提示操作获取授权码\n\n"
    "3. 填写配置：\n"
    "   - 发件人邮箱：你的QQ邮箱\n"
    "   - 密码/授权码：上一步获取的授权码\n"
    "   - 收件人邮箱：接收通知的邮箱地址\n\n"
    "4. 点击测试按钮验证配置是否正确"
)

# 主程序帮助文本
MAIN_HELP = """
POE2交易推送工具使用说明：

1. 基本设置：
   - 配置游戏窗口名称（默认为"Path of Exile"）
   - 指定游戏日志文件路径
   - 设置监控间隔和推送间隔

2. 添加关键词：
   - 消息模式：简单匹配文本内容
   - 交易模式：解析交易信息并提取详细数据

3. 配置推送方式：
   - 微信推送(WxPusher)
   - 邮箱推送
   - Server酱推送
   - Qmsg酱推送
   
4. 开始监控：
   - 点击"开始监控"按钮
   - 程序将自动检测匹配的交易信息
   - 根据配置发送推送通知
"""

# 常见问题帮助文本
FAQ_HELP = """
常见问题：

1. 监控运行但没有收到推送
   - 检查日志文件路径是否正确
   - 确认关键词设置是否匹配游戏内消息格式
   - 验证是否有至少一种推送方式配置正确并已测试通过

2. 推送频率过高
   - 增加推送间隔时间
   - 精确设置交易模式关键词

3. WxPusher无法接收消息
   - 确认是否已关注相应公众号
   - 验证UID和App Token是否正确

4. 程序启动失败
   - 确保安装了所有依赖
   - 检查配置文件格式是否正确
"""
