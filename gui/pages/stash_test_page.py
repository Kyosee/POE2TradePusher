from .recognition_base_page import RecognitionBasePage
from PIL import ImageTk
from core.process_modules.open_stash import OpenStashModule

class StashTestPage(RecognitionBasePage):
    """仓库测试页面 - 识别仓库并执行点击操作"""
    def __init__(self, master, callback_log, callback_status, main_window=None):
        super().__init__(master, callback_log, callback_status, main_window)
        self.open_stash_module = OpenStashModule()
        
    def _do_recognition(self):
        """执行仓库识别和点击"""
        try:
            # 执行打开仓库模块
            result = self.open_stash_module.run()
            if result:
                self._add_log("✅ 仓库打开成功")
                self.update_status("✅ 识别成功")
            else:
                self._add_log("❌ 仓库打开失败", "ERROR")
                self.update_status("❌ 识别失败")
                
        except Exception as e:
            self._add_log(f"识别过程出错: {str(e)}", "ERROR")
            self.update_status("❌ 识别失败")
