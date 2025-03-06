class Styles:
    """GUI样式管理类"""
    
    def __init__(self):
        # 界面主题颜色
        self.wx_green = '#07C160'
        self.wx_bg = '#f0f0f0'
        self.wx_hover = '#06AD56'
        self.wx_text = '#2C2C2C'
        self.wx_border = '#E6E7E8'
        
        # iOS Switch颜色
        self.switch_off = '#e9e9ea'      # 关闭状态背景色
        self.switch_thumb = '#ffffff'     # 滑块颜色
        self.switch_shadow = '#00000026'  # 滑块阴影颜色
        
        # 日志颜色映射
        self.log_colors = {
            "INFO": "#000000",
            "DEBUG": "#808080",
            "WARNING": "#FF8C00",
            "ERROR": "#FF0000",
            "SYSTEM": "#0000FF",
            "SUCCESS": "#008000"
        }
        
        # 日志页面样式
        self.log_table_style = """
            QTableWidget {
                background-color: white;
                border: 1px solid #E6E7E8;
                border-radius: 2px;
                padding: 0px;
            }
            QTableWidget:focus {
                border: 1px solid #07C160;
            }
            QTableWidget::item:selected {
                background-color: #E6F7EF;
                color: #333333;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 4px;
                border: 1px solid #E6E7E8;
                font-weight: bold;
            }
        """

        self.log_pagination_frame_style = """
            QFrame {
                background-color: #F8F9FA;
                border: 1px solid #E6E7E8;
                border-radius: 2px;
            }
        """

        # 创建样式表
        self.stylesheet = self._create_stylesheet()
        
    def _create_stylesheet(self):
        """创建Qt样式表"""
        return f"""
        /* 全局样式 */
        QWidget {{
            font-family: "微软雅黑";
            font-size: 10pt;
            color: {self.wx_text};
        }}
        
        /* 主窗口背景 */
        QMainWindow {{
            background: {self.wx_bg};
        }}
        
        /* 内容区域样式 */
        QWidget[class="content-container"] {{
            background: white;
            border-left: 1px solid {self.wx_border};
        }}
        
        /* 页面容器样式 */
        QWidget[class="page-container"] {{
            background: white;
            margin: 0px;
            padding: 0px;
        }}
        
        /* 菜单框架样式 */
        QFrame[class="menu-frame"] {{
            background: {self.wx_bg};
            border: none;
        }}
        
        /* 内容框架样式 */
        QFrame[class="content-frame"] {{
            background: white;
            border: none;
            margin: 0px;
            padding: 0px;
        }}
        
        /* 卡片框架样式 */
        QFrame[class="card-frame"] {{
            background: white;
            border: 1px solid {self.wx_border};
            border-radius: 2px;
            margin-bottom: 6px;
        }}
        
        QFrame[class="card-frame"]:hover {{
            border: 1px solid #D0D0D0;
        }}
        
        /* 卡片标题样式 */
        QLabel[class="card-title"] {{
            font-size: 11pt;
            font-weight: bold;
            color: {self.wx_text};
            padding: 0px;
            margin: 6px 0px;
        }}
        
        /* 菜单按钮样式 */
        QPushButton[class="menu-button"] {{
            padding: 12px 20px;
            background: {self.wx_bg};
            color: {self.wx_text};
            border: none;
            text-align: left;
            border-right: 3px solid transparent;
        }}
        
        QPushButton[class="menu-button"]:hover {{
            background: white;
            color: {self.wx_green};
        }}
        
        QPushButton[class="menu-button"][selected="true"] {{
            background: white;
            color: {self.wx_green};
            border-right: 3px solid {self.wx_green};
        }}
        
        /* 子菜单按钮样式 */
        QPushButton[class="submenu-button"] {{
            padding: 12px 20px;
            background: {self.wx_bg};
            color: {self.wx_text};
            border: none;
            text-align: left;
            border-right: 3px solid transparent;
        }}
        
        QPushButton[class="submenu-button"]:hover {{
            background: white;
            color: {self.wx_green};
        }}
        
        QPushButton[class="submenu-button"][selected="true"] {{
            background: white;
            color: {self.wx_green};
            border-right: 3px solid {self.wx_green};
        }}
        
        /* 控制按钮样式 */
        QPushButton[class="control-button"] {{
            padding: 7px 20px;
            background: {self.wx_green};
            color: white;
            border: none;
            border-radius: 2px;
            min-width: 80px;
        }}
        
        QPushButton[class="control-button"]:hover {{
            background: {self.wx_hover};
        }}
        
        QPushButton[class="control-button"]:disabled {{
            background: #E0E0E0;
            color: #A8A8A8;
        }}
        
        /* 停止按钮样式 */
        QPushButton[class="control-stop-button"] {{
            padding: 7px 20px;
            background: #ff4d4f;
            color: white;
            border: none;
            border-radius: 2px;
            min-width: 80px;
        }}
        
        QPushButton[class="control-stop-button"]:hover {{
            background: #ff7875;
        }}
        
        QPushButton[class="control-stop-button"]:disabled {{
            background: #E0E0E0;
            color: #A8A8A8;
        }}
        
        /* 保存按钮样式 */
        QPushButton[class="control-save-button"] {{
            padding: 7px 20px;
            background: #1890ff;
            color: white;
            border: none;
            border-radius: 2px;
            min-width: 80px;
        }}
        
        QPushButton[class="control-save-button"]:hover {{
            background: #40a9ff;
        }}
        
        QPushButton[class="control-save-button"]:disabled {{
            background: #E0E0E0;
            color: #A8A8A8;
        }}
        
        /* 普通操作按钮样式 - 绿色 */
        QPushButton[class="normal-button"] {{
            padding: 7px 20px;
            background: {self.wx_green};
            color: white;
            border: none;
            border-radius: 2px;
            min-width: 80px;
        }}
        
        QPushButton[class="normal-button"]:hover {{
            background: {self.wx_hover};
        }}
        
        QPushButton[class="normal-button"]:disabled {{
            background: #E0E0E0;
            color: #A8A8A8;
        }}
        
        /* 危险操作按钮样式 - 红色 */
        QPushButton[class="danger-button"] {{
            padding: 7px 20px;
            background: #ff4d4f;
            color: white;
            border: none;
            border-radius: 2px;
            min-width: 80px;
        }}
        
        QPushButton[class="danger-button"]:hover {{
            background: #ff7875;
        }}
        
        QPushButton[class="danger-button"]:disabled {{
            background: #E0E0E0;
            color: #A8A8A8;
        }}
        
        /* 状态栏标签样式 */
        QLabel[class="status-label"] {{
            padding: 6px;
            background: {self.wx_bg};
            color: {self.wx_text};
        }}
        
        /* 输入框样式 */
        QLineEdit {{
            padding: 5px;
            background: white;
            border: 1px solid {self.wx_border};
            border-radius: 2px;
            selection-background-color: #E7F7EE;
            selection-color: {self.wx_text};
        }}
        
        QLineEdit:focus {{
            border: 1px solid {self.wx_green};
        }}
        
        /* 列表框样式 */
        QListWidget {{
            background: white;
            border: 1px solid {self.wx_border};
            border-radius: 2px;
        }}
        
        QListWidget::item:selected {{
            background: #E7F7EE;
            color: {self.wx_green};
        }}
        
        /* 下拉框样式 */
        QComboBox {{
            padding: 5px;
            background: white;
            border: 1px solid {self.wx_border};
            border-radius: 2px;
        }}
        
        QComboBox:focus {{
            border: 1px solid {self.wx_green};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        /* 数字输入框样式 */
        QSpinBox {{
            padding: 5px;
            background: white;
            border: 1px solid {self.wx_border};
            border-radius: 2px;
            min-width: 80px;
        }}
        
        QSpinBox:focus {{
            border: 1px solid {self.wx_green};
        }}
        
        QSpinBox::up-button, QSpinBox::down-button {{
            width: 20px;
            background: white;
            border: none;
        }}
        
        /* 滚动条样式 */
        QScrollBar:vertical {{
            border: none;
            background: #F0F0F0;
            width: 8px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background: #CDCDCD;
            min-height: 20px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: #BBBBBB;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        /* 文本框样式 */
        QTextEdit {{
            background: white;
            border: 1px solid {self.wx_border};
            border-radius: 2px;
            padding: 8px;
            selection-background-color: #E7F7EE;
            selection-color: {self.wx_text};
        }}
        
        QTextEdit:focus {{
            border: 1px solid {self.wx_green};
        }}
        
        /* 对话框样式 */
        QDialog {{
            background: white;
        }}
        
        /* 堆叠widget样式 */
        QStackedWidget {{
            border: none;
            padding: 0px;
            margin: 0px;
        }}
        """
        
    def setup(self, app):
        """应用样式表到应用程序"""
        app.setStyleSheet(self.stylesheet)
