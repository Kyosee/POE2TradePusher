import os
import threading
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import pystray

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
            # 加载或创建图标
            image = self._create_icon()
            
            # 创建托盘菜单
            menu = pystray.Menu(lambda: (
                pystray.MenuItem("显示/隐藏", self._on_toggle, default=True),
                pystray.MenuItem("启动监控", self._on_start),
                pystray.MenuItem("停止监控", self._on_stop),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self._on_quit)
            ))
            
            # 创建托盘图标
            self.tray_icon = pystray.Icon(
                "POE2TradePusher",
                image,
                self.title,
                menu
            )
            
            # 在单独的线程中运行托盘图标
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            return True, "托盘初始化成功"
            
        except Exception as e:
            return False, f"托盘初始化失败: {str(e)}"
    
    def _create_icon(self):
        """创建托盘图标"""
        if os.path.exists(self.icon_path):
            image = PIL.Image.open(self.icon_path)
            image = image.resize((32, 32), PIL.Image.Resampling.LANCZOS)
            return image
        else:
            # 创建默认图标
            image = PIL.Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            draw = PIL.ImageDraw.Draw(image)
            draw.ellipse((2, 2, 30, 30), fill='#07C160')
            
            # 加载字体
            try:
                font = PIL.ImageFont.truetype("arial", 12)
            except:
                font = PIL.ImageFont.load_default()
                
            # 添加文字
            draw.text((8, 8), "P2", fill='white', font=font)
            return image
            
    def set_callback(self, event, callback):
        """
        设置回调函数
        :param event: 事件名称 (on_toggle/on_start/on_stop/on_quit)
        :param callback: 回调函数
        """
        self.callbacks[event] = callback
        
    def _on_toggle(self, icon, item):
        """切换窗口显示状态"""
        if self.callbacks['on_toggle']:
            self.callbacks['on_toggle']()
            
    def _on_start(self, icon, item):
        """启动监控"""
        if self.callbacks['on_start']:
            self.callbacks['on_start']()
            
    def _on_stop(self, icon, item):
        """停止监控"""
        if self.callbacks['on_stop']:
            self.callbacks['on_stop']()
            
    def _on_quit(self, icon, item):
        """退出应用程序"""
        if self.callbacks['on_quit']:
            self.callbacks['on_quit']()
            
    def stop(self):
        """停止托盘图标"""
        if self.tray_icon:
            self.tray_icon.stop()
            
    def set_visible(self, visible):
        """设置托盘图标可见性"""
        if self.tray_icon:
            self.tray_icon.visible = visible
