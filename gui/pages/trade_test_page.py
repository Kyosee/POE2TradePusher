from .recognition_base_page import RecognitionBasePage
from core.process_modules.trade_monitor import TradeMonitorModule
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QComboBox, QLabel)
from PySide6.QtCore import QTimer, QThread, Signal

class MonitorThread(QThread):
    """监测线程，避免阻塞UI"""
    # 定义信号
    result_signal = Signal(bool, int, object)  # 成功标志，数量，预览图
    log_signal = Signal(str, str)  # 消息，级别
    status_signal = Signal(str)  # 状态消息
    
    def __init__(self, trade_monitor, currency_template):
        super().__init__()
        self.trade_monitor = trade_monitor
        self.currency_template = currency_template
        self.is_running = True
        
    def run(self):
        """线程运行函数"""
        try:
            while self.is_running and self.trade_monitor.is_monitoring():
                # 执行监测
                success, count, preview = self.trade_monitor.run(
                    username="测试用户",
                    currency_template=self.currency_template,
                    show_preview=True
                )
                
                # 发送结果信号
                self.result_signal.emit(success, count, preview)
                
                # 短暂休眠，避免过度占用CPU
                self.msleep(500)
                
        except Exception as e:
            self.log_signal.emit(f"监测线程出错: {str(e)}", "ERROR")
            self.status_signal.emit("❌ 监测线程异常")
    
    def stop(self):
        """停止线程"""
        self.is_running = False
        self.wait(1000)  # 等待线程结束，最多1秒

class TradeTestPage(RecognitionBasePage):
    """交易测试页面 - 监测交易窗口中的通货数量"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        super().__init__(master, callback_log, callback_status, main_window)
        self.trade_monitor = TradeMonitorModule()
        self.monitor_thread = None
        
        # 创建控制区域
        self._create_control_frame()
        
    def _create_control_frame(self):
        """创建控制区域"""
        # 创建新的控制框架
        control_frame = QFrame()
        control_frame.setProperty('class', 'card-frame')
        layout = QHBoxLayout(control_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("监测设置")
        title_label.setProperty('class', 'card-title')
        
        # 通货选择下拉框
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(['chaos', 'divine', 'exalted'])
        self.currency_combo.setFixedWidth(120)
        
        # 添加按钮容器
        btn_container = QFrame()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)
        
        # 开始/停止监测按钮
        self.monitor_btn = QPushButton("▶ 开始监测")
        self.monitor_btn.setProperty('class', 'normal-button')
        self.monitor_btn.clicked.connect(self._toggle_monitoring)
        btn_layout.addWidget(self.monitor_btn)
        
        # 刷新预览按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setProperty('class', 'normal-button')
        refresh_btn.clicked.connect(self._refresh_preview)
        btn_layout.addWidget(refresh_btn)
        
        # 添加所有组件到布局
        layout.addWidget(QLabel("通货类型:"))
        layout.addWidget(self.currency_combo)
        layout.addWidget(btn_container)
        layout.addStretch()
        
        # 将标题和控制框架添加到主布局的顶部
        self.main_layout.insertWidget(0, title_label)
        self.main_layout.insertWidget(1, control_frame)
        
    def _toggle_monitoring(self):
        """切换监测状态"""
        if not self.trade_monitor.is_monitoring():
            self._start_monitoring()
        else:
            self._stop_monitoring()
            
    def _start_monitoring(self):
        """开始监测"""
        # 更新UI状态
        self.monitor_btn.setText("⏹ 停止监测")
        self.monitor_btn.setProperty('class', 'control-stop-button')
        self.monitor_btn.style().unpolish(self.monitor_btn)
        self.monitor_btn.style().polish(self.monitor_btn)
        
        # 启动监测
        if self.trade_monitor.start_monitoring():
            # 创建并启动监测线程
            currency_template = self.currency_combo.currentText()
            self.monitor_thread = MonitorThread(self.trade_monitor, currency_template)
            
            # 连接信号
            self.monitor_thread.result_signal.connect(self._handle_monitor_result)
            self.monitor_thread.log_signal.connect(self._add_log)
            self.monitor_thread.status_signal.connect(self.update_status)
            
            # 启动线程
            self.monitor_thread.start()
            self._add_log("监测线程已启动", "INFO")
    
    def _stop_monitoring(self):
        """停止监测"""
        # 停止监测
        if self.trade_monitor.stop_monitoring():
            # 更新UI状态
            self.monitor_btn.setText("▶ 开始监测")
            self.monitor_btn.setProperty('class', 'control-button')
            self.monitor_btn.style().unpolish(self.monitor_btn)
            self.monitor_btn.style().polish(self.monitor_btn)
            
            # 停止监测线程
            if self.monitor_thread and self.monitor_thread.isRunning():
                self.monitor_thread.stop()
                self._add_log("监测线程已停止", "INFO")
    
    def _handle_monitor_result(self, success, count, preview):
        """处理监测结果"""
        if success:
            currency_template = self.currency_combo.currentText()
            self._add_log(f"✅ 检测到 {count} 个通货--{currency_template}")
            self.update_status("✅ 识别成功")
            
            # 更新预览图
            if preview:
                pixmap = self._pil_to_pixmap(preview)
                self.preview_label.setPixmap(pixmap)
        else:
            self._add_log("❌ 监测失败", "ERROR")
            self.update_status("❌ 识别失败")
    
    def _do_recognition(self):
        """执行单次识别（不使用递归）"""
        try:
            currency_template = self.currency_combo.currentText()
            success, count, preview = self.trade_monitor.run(
                username="测试用户",
                currency_template=currency_template,
                show_preview=True
            )
            
            self._handle_monitor_result(success, count, preview)
                
        except Exception as e:
            self._add_log(f"识别过程出错: {str(e)}", "ERROR")
            self.update_status("❌ 识别失败")
