import win32gui
import win32con
import win32api
import win32clipboard
import json
from ..process_module import ProcessModule
from gui.utils import switch_to_window

class GameCommandModule(ProcessModule):
    """游戏命令模块 - 执行游戏命令"""
    
    def name(self) -> str:
        return "游戏命令"
        
    def description(self) -> str:
        return "执行游戏命令：回车-粘贴命令-回车"
        
    def run(self, **kwargs):
        command_text = kwargs.get('command_text')
        if not command_text:
            self.logger.error("未提供命令文本")
            return False
            
        try:
            # 从配置文件读取游戏窗口名称
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    window_name = config.get('game_window', 'Path of Exile 2')
            except Exception as e:
                self.logger.error(f"读取配置文件失败: {str(e)}")
                window_name = 'Path of Exile 2'
            hwnd = win32gui.FindWindow(None, window_name)
            if not hwnd:
                self.logger.error(f"未找到游戏窗口: {window_name}")
                return False
                
            # 确保窗口处于活动状态 - 使用通用切换窗口函数
            switch_result = switch_to_window(window_name)
            if not switch_result:
                self.logger.warning("切换到游戏窗口失败，尝试继续执行")
            
            # 模拟回车键
            self._press_enter()
            win32api.Sleep(50)
            
            # 设置剪贴板内容并粘贴
            self._set_clipboard_text(command_text)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, 0, 0)
            win32api.Sleep(50)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.Sleep(50)
            
            # 再次模拟回车键
            self._press_enter()
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {str(e)}")
            return False
            
    def _press_enter(self):
        """模拟按下回车键"""
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)  # 按下回车
        win32api.Sleep(50)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)  # 释放回车
            
    def _set_clipboard_text(self, text):
        """设置剪贴板文本内容"""
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
