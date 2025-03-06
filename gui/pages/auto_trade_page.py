from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QTextEdit, QSpinBox, QFrame)
from PySide6.QtCore import Qt
from core.auto_trade import TradeConfig
from gui.widgets.switch import Switch
from gui.styles import Styles
import json

class AutoTradePage(QWidget):
    def __init__(self, parent=None, save_config=None):
        super().__init__(parent)
        self.save_config = save_config
        self.trade_config = TradeConfig()
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        self.init_ui()

    def init_ui(self):
        # 控制区域
        control_frame = QFrame()
        control_frame.setProperty('class', 'card-frame')
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("自动交易控制")
        title_label.setProperty('class', 'card-title')
        self.main_layout.addWidget(title_label)
        
        # 自动交易开关
        switch_layout = QHBoxLayout()
        switch_layout.addWidget(QLabel("自动交易"))
        self.auto_trade_switch = Switch()
        self.auto_trade_switch.stateChanged.connect(self._on_switch_changed)
        switch_layout.addWidget(self.auto_trade_switch)
        switch_layout.addStretch()
        control_layout.addLayout(switch_layout)
        
        self.main_layout.addWidget(control_frame)

        # 配置区域
        config_frame = QFrame()
        config_frame.setProperty('class', 'card-frame')
        config_layout = QVBoxLayout(config_frame)
        config_layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        config_title = QLabel("交易参数设置")
        config_title.setProperty('class', 'card-title')
        self.main_layout.addWidget(config_title)
        
        # 超时配置
        timeout_layout = QHBoxLayout()
        
        # 组队超时配置
        party_timeout_layout = QHBoxLayout()
        party_timeout_layout.addWidget(QLabel("组队超时时间(毫秒):"))
        self.party_timeout_input = QSpinBox()
        self.party_timeout_input.setRange(1, 2147483647)  # 设置为最大整数范围
        self.party_timeout_input.setValue(30000)
        self.party_timeout_input.valueChanged.connect(self._on_config_changed)
        party_timeout_layout.addWidget(self.party_timeout_input)
        party_timeout_layout.addStretch()
        timeout_layout.addLayout(party_timeout_layout)
        
        # 交易请求超时配置
        trade_timeout_layout = QHBoxLayout()
        trade_timeout_layout.addWidget(QLabel("交易请求超时(毫秒):"))
        self.trade_timeout_input = QSpinBox()
        self.trade_timeout_input.setRange(1, 2147483647)  # 设置为最大整数范围
        self.trade_timeout_input.setValue(10000)
        self.trade_timeout_input.valueChanged.connect(self._on_config_changed)
        trade_timeout_layout.addWidget(self.trade_timeout_input)
        trade_timeout_layout.addStretch()
        timeout_layout.addLayout(trade_timeout_layout)
        
        config_layout.addLayout(timeout_layout)

        # 间隔配置
        interval_layout = QHBoxLayout()
        
        # 开仓取物间隔配置
        stash_interval_layout = QHBoxLayout()
        stash_interval_layout.addWidget(QLabel("开仓取物间隔(毫秒):"))
        self.stash_interval_input = QSpinBox()
        self.stash_interval_input.setRange(1, 2147483647)  # 设置为最大整数范围
        self.stash_interval_input.setValue(1000)
        self.stash_interval_input.valueChanged.connect(self._on_config_changed)
        stash_interval_layout.addWidget(self.stash_interval_input)
        stash_interval_layout.addStretch()
        interval_layout.addLayout(stash_interval_layout)
        
        # 交易发起间隔配置
        trade_interval_layout = QHBoxLayout()
        trade_interval_layout.addWidget(QLabel("交易发起间隔(毫秒):"))
        self.trade_interval_input = QSpinBox()
        self.trade_interval_input.setRange(1, 2147483647)  # 设置为最大整数范围
        self.trade_interval_input.setValue(1000)
        self.trade_interval_input.valueChanged.connect(self._on_config_changed)
        trade_interval_layout.addWidget(self.trade_interval_input)
        trade_interval_layout.addStretch()
        interval_layout.addLayout(trade_interval_layout)
        
        config_layout.addLayout(interval_layout)
        
        self.main_layout.addWidget(config_frame)

        # 当前交易状态显示
        status_frame = QFrame()
        status_frame.setProperty('class', 'card-frame')
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        status_title = QLabel("当前交易状态")
        status_title.setProperty('class', 'card-title')
        self.main_layout.addWidget(status_title)
        
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setFixedHeight(120)
        self.status_display.setStyleSheet(Styles().status_text_style)
        status_layout.addWidget(self.status_display)
        
        self.main_layout.addWidget(status_frame)

        # 交易历史记录
        history_frame = QFrame()
        history_frame.setProperty('class', 'card-frame')
        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        history_title = QLabel("交易历史记录")
        history_title.setProperty('class', 'card-title')
        self.main_layout.addWidget(history_title)
        
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setMinimumHeight(200)
        self.history_display.setStyleSheet(Styles().status_text_style)
        history_layout.addWidget(self.history_display)
        
        self.main_layout.addWidget(history_frame)

    def set_config_data(self, config: dict):
        """从配置文件加载设置"""
        if not config:
            return
            
        auto_trade_config = config.get('auto_trade', {})
        
        # 设置开关状态
        self.auto_trade_switch.setChecked(auto_trade_config.get('enabled', False))
        
        # 设置超时和间隔时间
        self.party_timeout_input.setValue(auto_trade_config.get('party_timeout_ms', 30000))
        self.trade_timeout_input.setValue(auto_trade_config.get('trade_timeout_ms', 10000))
        self.stash_interval_input.setValue(auto_trade_config.get('stash_interval_ms', 1000))
        self.trade_interval_input.setValue(auto_trade_config.get('trade_interval_ms', 1000))
        
        # 更新交易配置
        self._update_trade_config()

    def get_config_data(self) -> dict:
        """获取当前配置"""
        return {
            'auto_trade': {
                'enabled': self.auto_trade_switch.isChecked(),
                'party_timeout_ms': self.party_timeout_input.value(),
                'trade_timeout_ms': self.trade_timeout_input.value(),
                'stash_interval_ms': self.stash_interval_input.value(),
                'trade_interval_ms': self.trade_interval_input.value()
            }
        }

    def _update_trade_config(self):
        """更新交易配置"""
        self.trade_config = TradeConfig(
            party_timeout_ms=self.party_timeout_input.value(),
            trade_timeout_ms=self.trade_timeout_input.value(),
            stash_interval_ms=self.stash_interval_input.value(),
            trade_interval_ms=self.trade_interval_input.value()
        )

    def _on_switch_changed(self):
        """处理开关状态变化"""
        enabled = self.auto_trade_switch.isChecked()
        if self.save_config:
            self.save_config()
        self._update_trade_config()
        self.update_trade_status(
            "自动交易已启用" if enabled else "自动交易已禁用"
        )

    def _on_config_changed(self):
        """处理配置变化"""
        if self.save_config:
            self.save_config()
        self._update_trade_config()

    def get_trade_config(self) -> TradeConfig:
        """获取当前交易配置"""
        return self.trade_config

    def update_trade_status(self, status: str):
        """更新当前交易状态"""
        self.status_display.append(f"[{status}]")
        self.status_display.verticalScrollBar().setValue(
            self.status_display.verticalScrollBar().maximum()
        )

    def add_trade_history(self, record: str):
        """添加交易历史记录"""
        self.history_display.append(record)
        self.history_display.verticalScrollBar().setValue(
            self.history_display.verticalScrollBar().maximum()
        )
