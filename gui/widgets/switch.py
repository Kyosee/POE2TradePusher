from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve, QPointF, QSize, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

class Switch(QWidget):
    # 信号定义
    stateChanged = Signal(bool)
    
    def __init__(self, parent=None, width=50, height=30):
        super().__init__(parent)
        
        # 初始化position属性
        self._position = 0.0  # 使用0.0-1.0表示位置，避免具体像素值
        
        # 基本属性 - 使用实例变量而非类变量
        self._width = width
        self._height = height
        self._thumb_radius = (height - 4) // 2
        self._margin = 2
        
        # 颜色定义 - iOS7风格
        self._track_on_color = QColor('#34C759')   # 绿色开启状态
        self._track_off_color = QColor('#E9E9EA')  # 灰色关闭状态
        self._thumb_color = QColor('white')        # 白色滑块
        self._border_color = QColor('#D1D1D6')     # 边框颜色
        
        # 状态变量
        self._checked = False
        self._hover = False
        self._pressed = False
        
        # 动画相关 - 使用浮点数表示位置，避免整数舍入误差
        self._animation = QPropertyAnimation(self, b"position")
        self._animation.setDuration(150)  # 动画持续时间
        self._animation.setEasingCurve(QEasingCurve.OutQuad)  # 缓动曲线
        
        # 设置固定大小
        self.setFixedSize(width, height)
        
        # 允许鼠标追踪以实现悬停效果
        self.setMouseTracking(True)
    
    def _getPosition(self):
        """获取当前位置值（0.0-1.0）"""
        return self._position
    
    def _setPosition(self, pos):
        """设置当前位置值（0.0-1.0）"""
        self._position = pos
        self.update()
    
    # 定义position属性用于动画
    position = Property(float, _getPosition, _setPosition)
    
    def _start_animation(self):
        """开始滑块动画"""
        start_pos = 0.0 if not self._checked else 1.0
        end_pos = 1.0 if self._checked else 0.0
        
        self._animation.setStartValue(start_pos)
        self._animation.setEndValue(end_pos)
        self._animation.start()
    
    def paintEvent(self, event):
        """绘制开关"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 使用当前位置值（0.0-1.0）作为进度
        progress = self._position
        
        # 计算轨道颜色（平滑渐变）
        track_color = QColor(
            int(self._track_off_color.red() * (1 - progress) + self._track_on_color.red() * progress),
            int(self._track_off_color.green() * (1 - progress) + self._track_on_color.green() * progress),
            int(self._track_off_color.blue() * (1 - progress) + self._track_on_color.blue() * progress)
        )
        
        # 绘制轨道（圆角矩形）
        track_rect = QRectF(0, 0, self._width, self._height)
        track_radius = self._height / 2
        
        # 绘制轨道背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, track_radius, track_radius)
        
        # 计算滑块位置 - 基于百分比位置
        available_width = self._width - 2 * self._margin - 2 * self._thumb_radius
        x_pos = self._margin + progress * available_width
        y_pos = self._margin
        
        # 绘制滑块
        painter.setPen(QPen(QColor(220, 220, 220, 50), 1))
        painter.setBrush(QBrush(self._thumb_color))
        painter.drawEllipse(
            x_pos,
            y_pos,
            self._thumb_radius * 2,
            self._thumb_radius * 2
        )
    
    def mousePressEvent(self, event):
        """鼠标点击事件处理"""
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件处理"""
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            self.setChecked(not self._checked)
            self.update()
    
    def enterEvent(self, event):
        """鼠标进入事件处理"""
        self._hover = True
        self.update()
    
    def leaveEvent(self, event):
        """鼠标离开事件处理"""
        self._hover = False
        self._pressed = False
        self.update()
    
    def isChecked(self):
        """获取开关状态"""
        return self._checked
    
    def setChecked(self, checked):
        """设置开关状态"""
        if self._checked != checked:
            self._checked = checked
            self._start_animation()
            self.stateChanged.emit(checked)
            self.update()
    
    # 属性定义
    checked = Property(bool, isChecked, setChecked)
    
    def get(self):
        """获取状态（兼容旧接口）"""
        return self.isChecked()
    
    def set(self, value):
        """设置状态（兼容旧接口）"""
        self.setChecked(bool(value))
    
    def sizeHint(self):
        """提供组件的建议大小"""
        return QSize(self._width, self._height)
