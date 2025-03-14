import traceback
from core.log_monitor import LogMonitor
from core.auto_trade import AutoTrade, TradeConfig

class MonitorManager:
    """负责管理监控和自动交易功能"""
    
    def __init__(self, config, log_callback, stats_page, auto_trade_page, update_status_callback):
        """初始化监控管理器"""
        self.config = config
        self.log_callback = log_callback
        self.stats_page = stats_page
        self.auto_trade_page = auto_trade_page
        self.update_status_callback = update_status_callback
        
        self.monitor = None
        self.auto_trade = AutoTrade()
        
        # 配置自动交易回调
        self.auto_trade.set_callbacks(
            self.auto_trade_page.update_trade_status,
            self.auto_trade_page.add_trade_history
        )
    
    def start_monitoring(self, push_config, auto_trade_config):
        """启动监控"""
        try:
            # 创建并初始化监控器
            self.monitor = LogMonitor(self.config, self.log_callback, self.stats_page)
            
            # 配置自动交易
            at_config = auto_trade_config.get('auto_trade', {})
            
            # 设置自动交易配置
            trade_config = TradeConfig(
                party_timeout_ms=at_config.get('party_timeout_ms', 30000),
                trade_timeout_ms=at_config.get('trade_timeout_ms', 10000),
                stash_interval_ms=at_config.get('stash_interval_ms', 1000),
                trade_interval_ms=at_config.get('trade_interval_ms', 1000)
            )
            self.auto_trade.set_config(trade_config)
            
            # 添加自动交易处理器
            self.monitor.add_handler(self.auto_trade)
            self.log_callback("已添加自动交易处理器", "SYSTEM")
            
            # 根据配置决定是否启用自动交易
            if at_config.get('enabled', False):
                self.auto_trade.enable()
                self.log_callback("自动交易已启用", "SYSTEM")
            else:
                self.auto_trade.disable()
                self.log_callback("自动交易已禁用", "SYSTEM")
            
            # 添加推送处理器
            handlers_added = self._setup_push_handlers(push_config)
            
            # 验证是否成功添加了推送处理器
            if handlers_added == 0:
                self.log_callback("没有可用的推送处理器", "ERROR")
                return False, None
            
            # 启动监控
            if self.monitor.start():
                encoding_info = self.monitor.file_utils.get_encoding_info()
                return True, encoding_info
            else:
                return False, None
                
        except Exception as e:
            self.log_callback(f"启动监控失败: {str(e)}", "ERROR")
            self.log_callback(traceback.format_exc(), "DEBUG")
            return False, None
    
    def stop_monitoring(self):
        """停止监控"""
        if self.monitor:
            self.monitor.stop()
            
        # 停止当前交易流程（如果有）
        if hasattr(self, 'auto_trade'):
            self.auto_trade.stop_current_trade()
            
    def _setup_push_handlers(self, push_config):
        """设置推送处理器"""
        handlers_added = 0
        
        # 推送平台映射
        pusher_mapping = {
            'wxpusher': ('core.push.wxpusher', 'WxPusher'),
            'email': ('core.push.email_pusher', 'EmailPusher'),
            'serverchan': ('core.push.serverchan', 'ServerChan'),
            'qmsgchan': ('core.push.qmsgchan', 'QmsgChan')
        }
        
        # 动态导入和初始化每个启用的推送平台
        for platform, config in push_config.items():
            if isinstance(config, dict) and config.get('enabled'):
                if platform not in pusher_mapping:
                    self.log_callback(f"未知的推送平台: {platform}", "ERROR")
                    continue
                    
                try:
                    # 动态导入推送类
                    module_path, class_name = pusher_mapping[platform]
                    module = __import__(module_path, fromlist=[class_name])
                    pusher_class = getattr(module, class_name)
                    
                    # 实例化并验证配置
                    pusher = pusher_class(self.config, self.log_callback)
                    success, msg = pusher.validate_config()
                    
                    if success:
                        self.monitor.add_push_handler(pusher)
                        handlers_added += 1
                        self.log_callback(f"已添加 {class_name} 推送处理器", "INFO")
                    else:
                        self.log_callback(f"{class_name} 配置验证失败: {msg}", "ERROR")
                        
                except Exception as e:
                    self.log_callback(f"初始化 {platform} 推送处理器失败: {str(e)}", "ERROR")
        
        return handlers_added
