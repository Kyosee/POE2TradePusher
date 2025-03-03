import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap, QColor
from PySide6.QtCore import Qt, QSize

class TrayIcon:
    """系统托盘管理类"""
    
    def __init__(self, title="POE2 Trade Pusher", icon_path=None):
        """
        初始化系统托盘
        :param title: 托盘图标标题
        :param icon_path: 图标路径，默认为 assets/icon.ico
        """
        self.title = title
        self.icon_path = icon_path or os.path.join('assets', 'icon.ico')
        self.is_minimized = False
        self.tray_icon = None
        self.callbacks = {
            'on_toggle': None,
            'on_start': None,
            'on_stop': None,
            'on_quit': None
        }
        
    def setup(self):
        """初始化系统托盘"""
        try:
            # 创建系统托盘图标
            self.tray_icon = QSystemTrayIcon()
            self.tray_icon.setToolTip(self.title)
            
            # 加载图标
            icon = self._create_icon()
            self.tray_icon.setIcon(icon)
            
            # 创建右键菜单
            menu = QMenu()
            
            # 显示/隐藏选项
            toggle_action = menu.addAction("显示/隐藏")
            toggle_action.triggered.connect(self._on_toggle)
            menu.addSeparator()
            
            # 启动/停止监控选项
            start_action = menu.addAction("启动监控")
            start_action.triggered.connect(self._on_start)
            
            stop_action = menu.addAction("停止监控")
            stop_action.triggered.connect(self._on_stop)
            menu.addSeparator()
            
            # 退出选项
            quit_action = menu.addAction("退出")
            quit_action.triggered.connect(self._on_quit)
            
            # 设置右键菜单
            self.tray_icon.setContextMenu(menu)
            
            # 双击事件处理
            self.tray_icon.activated.connect(self._on_activated)
            
            # 显示托盘图标
            self.tray_icon.show()
            
            return True, "托盘初始化成功"
            
        except Exception as e:
            return False, f"托盘初始化失败: {str(e)}"
    
    def _create_icon(self):
        """创建托盘图标"""
        if os.path.exists(self.icon_path):
            return QIcon(self.icon_path)
        else:
            # 创建默认图标
            image = QImage(32, 32, QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制圆形背景
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#07C160'))
            painter.drawEllipse(2, 2, 28, 28)
            
            # 绘制文字
            painter.setPen(Qt.white)
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(image.rect(), Qt.AlignCenter, 'P2')
            
            painter.end()

            pixmap = QPixmap.fromImage(image)
            return QIcon(pixmap)
            
    def set_callback(self, event, callback):
        """
        设置回调函数
        :param event: 事件名称 (on_toggle/on_start/on_stop/on_quit)
        :param callback: 回调函数
        """
        self.callbacks[event] = callback
        
    def _on_toggle(self):
        """切换窗口显示状态"""
        if self.callbacks['on_toggle']:
            self.callbacks['on_toggle']()
            
    def _on_start(self):
        """启动监控"""
        if self.callbacks['on_start']:
            self.callbacks['on_start']()
            
    def _on_stop(self):
        """停止监控"""
        if self.callbacks['on_stop']:
            self.callbacks['on_stop']()
            
    def _on_quit(self):
        """退出应用程序"""
        if self.callbacks['on_quit']:
            self.callbacks['on_quit']()
            
    def _on_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_toggle()
            
    def stop(self):
        """停止托盘图标"""
        if self.tray_icon:
            self.tray_icon.hide()
            
    def set_visible(self, visible):
        """设置托盘图标可见性"""
        if self.tray_icon:
            if visible:
                self.tray_icon.show()
            else:
                self.tray_icon.hide()
