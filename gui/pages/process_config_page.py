from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QSpinBox, QTextEdit, QFrame)
from PySide6.QtCore import Qt
from ..utils import LoggingMixin, ConfigMixin, show_message
from ..widgets.dialog import MessageDialog

class ProcessConfigPage(QWidget, LoggingMixin, ConfigMixin):
    """流程配置页面"""
    def __init__(self, master, log_callback, status_callback, callback_save=None):
        super().__init__(master)
        LoggingMixin.__init__(self, log_callback, status_callback)
        self.init_config()
        self.save_config = callback_save
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 6, 12, 6)
        self.main_layout.setSpacing(6)
        
        # 创建界面组件
        self._create_process_frame()
        
    def _create_process_frame(self):
        """创建流程配置区域"""
        # 创建处理间隔配置框架
        interval_frame = QFrame()
        interval_frame.setProperty('class', 'card-frame')
        interval_layout = QHBoxLayout(interval_frame)
        interval_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("处理间隔配置")
        title_label.setProperty('class', 'card-title')
        
        interval_label = QLabel("处理间隔(ms):")
        self.process_interval_spin = QSpinBox()
        self.process_interval_spin.setRange(100, 1000)
        self.process_interval_spin.setSingleStep(100)
        self.process_interval_spin.setValue(200)
        self.process_interval_spin.valueChanged.connect(self._on_settings_change)
        
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.process_interval_spin)
        interval_layout.addStretch()
        
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(interval_frame)
        
        # 创建按键设置框架
        key_frame = QFrame()
        key_frame.setProperty('class', 'card-frame')
        key_layout = QVBoxLayout(key_frame)
        key_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("按键设置")
        title_label.setProperty('class', 'card-title')
        
        # 鼠标延迟设置
        mouse_layout = QHBoxLayout()
        mouse_label = QLabel("鼠标移动后延时(ms):")
        self.mouse_delay_spin = QSpinBox()
        self.mouse_delay_spin.setRange(0, 500)
        self.mouse_delay_spin.setSingleStep(50)
        self.mouse_delay_spin.setValue(100)
        self.mouse_delay_spin.valueChanged.connect(self._on_settings_change)
        
        mouse_layout.addWidget(mouse_label)
        mouse_layout.addWidget(self.mouse_delay_spin)
        mouse_layout.addStretch()
        key_layout.addLayout(mouse_layout)
        
        # 按键延迟设置
        key_delay_layout = QHBoxLayout()
        key_label = QLabel("按键延时(ms):")
        self.key_delay_spin = QSpinBox()
        self.key_delay_spin.setRange(0, 500)
        self.key_delay_spin.setSingleStep(50)
        self.key_delay_spin.setValue(50)
        self.key_delay_spin.valueChanged.connect(self._on_settings_change)
        
        key_delay_layout.addWidget(key_label)
        key_delay_layout.addWidget(self.key_delay_spin)
        key_delay_layout.addStretch()
        key_layout.addLayout(key_delay_layout)
        
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(key_frame)
        
        # 创建按键序列框架
        sequence_frame = QFrame()
        sequence_frame.setProperty('class', 'card-frame')
        sequence_layout = QVBoxLayout(sequence_frame)
        sequence_layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("按键序列")
        title_label.setProperty('class', 'card-title')
        
        # 添加按键序列说明
        help_text = """按键序列说明：
1. 每行一个操作，格式为：动作 参数
2. 支持的动作：
   - MOVE x y: 移动鼠标到指定坐标
   - CLICK: 点击鼠标左键
   - KEY key: 模拟按下指定按键
   - DELAY ms: 等待指定毫秒数
3. 示例：
   MOVE 100 200
   CLICK
   KEY enter
   DELAY 500"""
        
        self.help_text = QTextEdit()
        self.help_text.setPlainText(help_text)
        self.help_text.setReadOnly(True)
        self.help_text.setFixedHeight(150)
        self.help_text.setStyleSheet("""
            QTextEdit {
                background-color: #F8F9FA;
                border: none;
                padding: 8px;
                font-family: Consolas;
                font-size: 9pt;
            }
        """)
        sequence_layout.addWidget(self.help_text)
        
        # 添加序列编辑区
        self.sequence_text = QTextEdit()
        self.sequence_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #E6E7E8;
                border-radius: 2px;
                padding: 8px;
                font-family: Consolas;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 1px solid #07C160;
            }
        """)
        self.sequence_text.textChanged.connect(self._on_settings_change)
        sequence_layout.addWidget(self.sequence_text)
        
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(sequence_frame)
            
    def _on_settings_change(self):
        """处理设置变化"""
        if self.save_config:
            self.save_config()
            
    def validate_config(self):
        """验证配置"""
        data = self.get_config_data()
        
        try:
            interval = data.get('process_interval', 0)
            if interval < 100 or interval > 1000:
                return False, "处理间隔必须在100-1000毫秒之间"
        except ValueError:
            return False, "无效的处理间隔值"
            
        try:
            mouse_delay = data.get('mouse_delay', 0)
            if mouse_delay < 0 or mouse_delay > 500:
                return False, "鼠标移动延时必须在0-500毫秒之间"
        except ValueError:
            return False, "无效的鼠标移动延时值"
            
        try:
            key_delay = data.get('key_delay', 0)
            if key_delay < 0 or key_delay > 500:
                return False, "按键延时必须在0-500毫秒之间"
        except ValueError:
            return False, "无效的按键延时值"
            
        if not data.get('sequence', '').strip():
            return False, "请添加至少一个按键序列操作"
            
        return True, None
        
    def get_config_data(self):
        """获取配置数据"""
        return {
            'process_interval': self.process_interval_spin.value(),
            'mouse_delay': self.mouse_delay_spin.value(),
            'key_delay': self.key_delay_spin.value(),
            'sequence': self.sequence_text.toPlainText().strip()
        }
        
    def set_config_data(self, data):
        """设置配置数据"""
        self.process_interval_spin.setValue(data.get('process_interval', 200))
        self.mouse_delay_spin.setValue(data.get('mouse_delay', 100))
        self.key_delay_spin.setValue(data.get('key_delay', 50))
        self.sequence_text.setPlainText(data.get('sequence', ''))
