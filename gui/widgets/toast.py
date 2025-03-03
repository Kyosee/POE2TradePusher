from PySide6.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, 
                               QFrame, QGraphicsOpacityEffect, QApplication)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QFontMetrics

class Toast(QFrame):
    """Bootstrap风格的Toast提示组件"""
    
    # 定义Toast类型
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning" 
    ERROR = "error"
    
    def __init__(self, parent=None, duration=3000):
        """
        初始化Toast提示组件
        
        Args:
            parent: 父窗口
            duration: 显示持续时间(毫秒)，设为0则不自动消失
        """
        super().__init__(parent)
        
        # 初始化不透明度属性 - 修复：确保在任何动画开始前初始化
        self._opacity = 1
        
        # 不设置任何窗口标志，让它作为普通widget工作
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 修复：更新样式表，确保标签文本可见
        self.setStyleSheet("""
            QFrame#toast {
                background-color: #ffffff;
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 6px;
                padding: 8px;
            }
            QLabel {
                background: transparent;
            }
            QLabel[class="toast-title"] {
                font-size: 16px;
                font-weight: bold;
                color: #212529;
            }
            QLabel[class="toast-message"] {
                font-size: 14px;
                color: #6c757d;
            }
            QFrame#toast.toast-info {
                background-color: #cff4fc;
                border-left: 5px solid #0dcaf0;
            }
            QFrame#toast.toast-success {
                background-color: #d1e7dd;
                border-left: 5px solid #198754;
            }
            QFrame#toast.toast-warning {
                background-color: #fff3cd;
                border-left: 5px solid #ffc107;
            }
            QFrame#toast.toast-error {
                background-color: #f8d7da;
                border-left: 5px solid #dc3545;
            }
            /* 为错误提示设置特殊文字颜色 */
            QFrame#toast.toast-error QLabel.toast-title {
                color: #b02a37;
            }
            QFrame#toast.toast-error QLabel.toast-message {
                color: #b02a37;
            }
        """)
        
        # 修复：设置固定的ObjectName，用于样式定位
        self.setObjectName("toast")
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(5)
        
        # 标题布局
        self.title_layout = QHBoxLayout()
        
        # 标题文本
        self.title_label = QLabel()
        self.title_label.setProperty("class", "toast-title")  # 修复：使用setProperty代替setObjectName
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_layout.addWidget(self.title_label, 1)
        
        # 添加标题布局
        self.layout.addLayout(self.title_layout)
        
        # 消息文本
        self.message_label = QLabel()
        self.message_label.setProperty("class", "toast-message")  # 修复：使用setProperty代替setObjectName
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.message_label.setWordWrap(True)
        self.layout.addWidget(self.message_label)
        
        # 设置固定宽度
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
        
        # 设置不透明度效果
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(self._opacity)
        self.setGraphicsEffect(self._opacity_effect)
        
        # 设置计时器和动画
        self._setup_timer_and_animations(duration)
        self.duration = duration
        
    def _setup_timer_and_animations(self, duration):
        """设置定时器和动画效果"""
        # 自动消失定时器
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_animation)
        
        # 显示动画
        self._show_animation = QPropertyAnimation(self, b"opacity")
        self._show_animation.setDuration(300)
        self._show_animation.setStartValue(0)
        self._show_animation.setEndValue(1)
        self._show_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 隐藏动画
        self._hide_animation = QPropertyAnimation(self, b"opacity")
        self._hide_animation.setDuration(300)
        self._hide_animation.setStartValue(1)
        self._hide_animation.setEndValue(0)
        self._hide_animation.setEasingCurve(QEasingCurve.InCubic)
        self._hide_animation.finished.connect(self.close)
        
        # 设置显示时长
        if duration > 0:
            self._timer.setInterval(duration)
        
    def get_opacity(self):
        """获取不透明度"""
        return self._opacity
    
    def set_opacity(self, opacity):
        """设置不透明度"""
        self._opacity = opacity
        self._opacity_effect.setOpacity(opacity)
        
    # 定义不透明度属性，用于动画
    opacity = Property(float, get_opacity, set_opacity)
    
    # 修复：添加自定义绘制事件，确保背景色正确显示
    def paintEvent(self, event):
        """自定义绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(self.palette().color(self.backgroundRole())))
        super().paintEvent(event)
        
    def show_toast(self, title, message, toast_type=INFO):
        """
        显示Toast提示
        
        Args:
            title: 提示标题
            message: 提示消息
            toast_type: 提示类型(INFO, SUCCESS, WARNING, ERROR)
        """
        # 设置标题和消息
        self.title_label.setText(title)
        self.message_label.setText(message)
        
        # 设置样式类
        self.setProperty('class', f'toast-{toast_type}')
        self.style().unpolish(self)
        self.style().polish(self)
        
        # 确保文本标签可见
        self.title_label.show()
        self.message_label.show()
        
        # 调整宽度以适应内容
        self._adjust_width()
        
        # 显示、提升到顶层并开始动画
        self.show()
        self.raise_()
        self._show_animation.start()
        
        # 强制刷新显示
        self.update()
        
        # 如果设置了显示时长，启动定时器
        if self.duration > 0:
            self._timer.start()
            
    def hide_animation(self):
        """开始隐藏动画"""
        self._hide_animation.start()
            
    def _adjust_width(self):
        """根据内容调整宽度"""
        # 计算标题和消息文本的最大宽度
        title_font = self.title_label.font()
        title_metrics = QFontMetrics(title_font)
        title_width = title_metrics.horizontalAdvance(self.title_label.text()) + 60  # 增加额外留白
        
        message_font = self.message_label.font()
        message_metrics = QFontMetrics(message_font)
        
        # 按行计算消息宽度
        message_lines = self.message_label.text().split('\n')
        message_width = max([message_metrics.horizontalAdvance(line) for line in message_lines]) + 60
        
        # 取标题和消息的最大宽度
        content_width = max(title_width, message_width)
        
        # 限制宽度范围并设置最小高度
        width = min(max(content_width, 300), 400)
        self.setFixedWidth(width)
        
        # 确保有足够的高度显示内容
        message_height = message_metrics.lineSpacing() * max(1, len(message_lines))
        min_height = 60 + message_height  # 标题和边距的基础高度 + 消息高度
        self.setMinimumHeight(min_height)

class ToastManager:
    """Toast提示管理器，用于管理多个Toast提示的显示"""
    
    _instance = None
    _toast_queue = []
    _current_toast = None
    _vertical_offset = 10
    _max_visible_toasts = 4  # 最大同时显示的Toast数量
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = ToastManager()
        return cls._instance
    
    def show_toast(self, parent, title, message, toast_type=Toast.INFO, duration=3000):
        """
        显示Toast提示
        
        Args:
            parent: 父窗口
            title: 提示标题
            message: 提示消息
            toast_type: 提示类型
            duration: 显示时长，单位毫秒
        """
        # 修复：寻找顶层窗口，确保Toast显示在程序主窗口内
        main_window = self._find_main_window(parent)
        
        if not main_window:
            # 如果找不到主窗口，则使用提供的parent
            main_window = parent
            
        # 限制队列长度，如果已达到最大显示数量，删除最早的Toast
        if len(self._toast_queue) >= self._max_visible_toasts:
            oldest_toast = self._toast_queue[0]
            oldest_toast._hide_animation.start()  # 开始隐藏动画
        
        # 创建新的Toast，使用主窗口作为父窗口
        toast = Toast(main_window, duration)
        toast.show_toast(title, message, toast_type)
        
        # 记录当前toast
        self._toast_queue.append(toast)
        
        # 安排所有Toast的显示位置
        self._arrange_toasts()
        
        # 连接关闭信号，移除队列中的Toast
        toast._hide_animation.finished.connect(lambda: self._remove_toast(toast))
    
    def _find_main_window(self, widget):
        """
        查找主窗口
        
        从给定的小部件开始，向上追溯找到顶层窗口
        """
        if widget is None:
            # 如果未提供小部件，尝试获取活动窗口
            widget = QApplication.activeWindow()
            
        if widget is None:
            # 如果仍然没有窗口，返回None
            return None
            
        # 查找顶层窗口
        parent = widget
        while parent.parent() is not None:
            parent = parent.parent().window()
            
        return parent
        
    def _remove_toast(self, toast):
        """从队列中移除Toast"""
        if toast in self._toast_queue:
            self._toast_queue.remove(toast)
            self._arrange_toasts()
    
    def _arrange_toasts(self):
        """重新排列所有Toast的位置"""
        vertical_position = self._vertical_offset
        
        # 检查父窗口可用高度
        max_height = 0
        parent = None
        
        # 确定父窗口的高度限制
        if self._toast_queue and self._toast_queue[0].parent():
            parent = self._toast_queue[0].parent()
            max_height = parent.height() - 40  # 留出底部空间
        
        # 如果没有父窗口或队列为空，直接返回
        if not parent or not self._toast_queue:
            return
            
        # 确保所有Toast使用同一个父窗口并保持可见
        for toast in self._toast_queue:
            if toast.parent() != parent:
                toast.setParent(parent)
                toast.show()
                toast.raise_()
        
        # 重新排列所有Toast
        for i, toast in enumerate(self._toast_queue):
            # 计算预期高度
            expected_height = vertical_position + toast.height()
            
            # 如果预期高度超过父窗口高度，且不是第一个Toast，则隐藏旧的Toast
            if expected_height > max_height and i > 0:
                # 最多显示_max_visible_toasts个Toast，超出的自动隐藏
                for old_toast in self._toast_queue[:i]:
                    if not old_toast._hide_animation.state():  # 如果动画未在播放
                        old_toast._hide_animation.start()
                continue
            
            # 计算位置，始终固定在右上角依次向下排列
            parent_rect = parent.rect()
            # 固定在父窗口内部的右上角
            x = parent_rect.width() - toast.width() - 10  # 距右边界10px
            y = vertical_position
            
            # 设置位置 (相对于父窗口)
            toast.move(x, y)
            
            vertical_position += toast.height() + 10  # 每个Toast之间留出10px间隙

# 创建全局Toast管理器实例
toast_manager = ToastManager.get_instance()

def show_toast(parent, title, message, toast_type=Toast.INFO, duration=3000):
    """
    显示Toast提示的便捷函数
    
    Args:
        parent: 父窗口
        title: 提示标题
        message: 提示消息
        toast_type: 提示类型(Toast.INFO, Toast.SUCCESS, Toast.WARNING, Toast.ERROR)
        duration: 显示时长，单位毫秒
    """
    toast_manager.show_toast(parent, title, message, toast_type, duration)
