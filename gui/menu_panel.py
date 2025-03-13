from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton
from functools import partial

class MenuPanel(QFrame):
    """左侧菜单面板"""
    
    def __init__(self, main_window):
        """初始化菜单面板"""
        super().__init__()
        self.main_window = main_window
        self.setFixedWidth(200)
        self.setProperty('class', 'menu-frame')
        
        # 创建菜单布局
        self.menu_layout = QVBoxLayout(self)
        self.menu_layout.setContentsMargins(1, 1, 1, 1)
        self.menu_layout.setSpacing(1)
        
        # 初始化变量
        self.menu_buttons = []
        self.submenu_frames = {}
        self.current_menu = None
        self.current_submenu = None
        
        # 创建菜单按钮
        self.create_menu_buttons()
    
    def create_menu_buttons(self):
        """创建菜单按钮"""
        # 定义菜单项及其回调
        menu_items = [
            ('基本配置', self.show_basic_config, []),
            ('推送配置', self.show_push_manage, []),
            ('物品配置', self.show_item_config, []),
            ('账号管理', self.show_account_manage, []),
            ('数据统计', self.show_stats, []),
            ('自动交易', self.show_auto_trade, []),
            ('触发日志', self.show_log, []),
            ('识别测试', None, [
                ('仓库测试', self.show_stash_recognition),
                ('定位测试', self.show_grid_recognition),
                ('命令测试', self.show_command_test),
                ('Tab测试', self.show_tab_test),
                ('物品识别', self.show_trade_test)
            ])
        ]
        
        for text, command, submenus in menu_items:
            btn = QPushButton(text)
            btn.setProperty('class', 'menu-button')
            if command:
                btn.clicked.connect(command)
            else:
                btn.clicked.connect(partial(self._toggle_submenu, text))
            
            self.menu_layout.addWidget(btn)
            self.menu_buttons.append(btn)
            
            # 如果有子菜单，创建子菜单框架
            if submenus:
                submenu_frame = QFrame()
                submenu_frame.setProperty('class', 'submenu-frame')
                submenu_layout = QVBoxLayout(submenu_frame)
                submenu_layout.setContentsMargins(0, 0, 0, 0)
                submenu_layout.setSpacing(1)
                
                self.submenu_frames[text] = {
                    'frame': submenu_frame,
                    'visible': False,
                    'buttons': []
                }
                
                # 创建子菜单按钮
                for sub_text, sub_command in submenus:
                    sub_btn = QPushButton('  ' + sub_text)
                    sub_btn.setProperty('class', 'submenu-button')
                    sub_btn.clicked.connect(sub_command)
                    submenu_layout.addWidget(sub_btn)
                    self.submenu_frames[text]['buttons'].append(sub_btn)
                
                submenu_frame.hide()
                self.menu_layout.addWidget(submenu_frame)
        
        # 添加弹性空间
        self.menu_layout.addStretch()
        
        # 创建控制按钮区域
        control_frame = QFrame()
        control_frame.setProperty('class', 'control-frame')
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(1, 1, 1, 1)
        control_layout.setSpacing(1)
        
        # 启动按钮
        self.start_btn = QPushButton("▶ 开始监控")
        self.start_btn.setProperty('class', 'control-button')
        self.start_btn.clicked.connect(self.main_window.toggle_monitor)
        control_layout.addWidget(self.start_btn)
        
        # 保存按钮
        self.save_btn = QPushButton("💾 保存设置")
        self.save_btn.setProperty('class', 'control-save-button')
        self.save_btn.clicked.connect(self.main_window.save_config)
        control_layout.addWidget(self.save_btn)
        
        self.menu_layout.addWidget(control_frame)
    
    def set_monitor_active(self, active):
        """设置监控状态"""
        if active:
            self.start_btn.setText("⏹ 停止监控")
            self.start_btn.setProperty('class', 'control-stop-button')
        else:
            self.start_btn.setText("▶ 开始监控")
            self.start_btn.setProperty('class', 'control-button')
            
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
    
    def _toggle_submenu(self, menu_text):
        """切换子菜单的显示状态"""
        if menu_text in self.submenu_frames:
            submenu_info = self.submenu_frames[menu_text]
            submenu_frame = submenu_info['frame']
            
            submenu_info['visible'] = not submenu_info['visible']
            if submenu_info['visible']:
                submenu_frame.show()
            else:
                submenu_frame.hide()
    
    def _update_menu_state(self, selected_index, selected_submenu=None):
        """更新菜单按钮状态"""
        for i, btn in enumerate(self.menu_buttons):
            menu_text = btn.text()
            btn.setProperty('selected', i == selected_index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
            # 更新二级菜单状态
            if menu_text in self.submenu_frames:
                submenu_info = self.submenu_frames[menu_text]
                for sub_btn in submenu_info['buttons']:
                    sub_text = sub_btn.text().strip()
                    is_selected = (i == selected_index and sub_text == selected_submenu)
                    sub_btn.setProperty('selected', is_selected)
                    sub_btn.style().unpolish(sub_btn)
                    sub_btn.style().polish(sub_btn)
                    
                    if is_selected:
                        btn.setProperty('selected', True)
                        btn.style().unpolish(btn)
                        btn.style().polish(btn)
        
        # 更新当前选中状态
        self.current_menu = selected_index
        self.current_submenu = selected_submenu
    
    # 菜单项点击事件处理方法
    def show_basic_config(self):
        """显示基本配置页面"""
        self.main_window._show_basic_config()
        self._update_menu_state(0)
    
    def show_push_manage(self):
        """显示推送管理页面"""
        self.main_window._show_push_manage()
        self._update_menu_state(1)
    
    def show_item_config(self):
        """显示物品配置页面"""
        self.main_window._show_item_config()
        self._update_menu_state(2)
        
    def show_account_manage(self):
        """显示账号管理页面"""
        self.main_window._show_account_manage()
        self._update_menu_state(3)
    
    def show_stats(self):
        """显示数据统计页面"""
        self.main_window._show_stats()
        self._update_menu_state(4)
    
    def show_auto_trade(self):
        """显示自动交易页面"""
        self.main_window._show_auto_trade()
        self._update_menu_state(5)
    
    def show_log(self):
        """显示日志页面"""
        self.main_window._show_log()
        self._update_menu_state(6)
    
    def show_stash_recognition(self):
        """显示仓库识别页面"""
        self.main_window._show_stash_recognition()
        self._update_menu_state(7, '仓库测试')
    
    def show_grid_recognition(self):
        """显示仓位识别页面"""
        self.main_window._show_grid_recognition()
        self._update_menu_state(7, '定位测试')
    
    def show_command_test(self):
        """显示命令测试页面"""
        self.main_window._show_command_test()
        self._update_menu_state(7, '命令测试')
        
    def show_tab_test(self):
        """显示Tab测试页面"""
        self.main_window._show_tab_test()
        self._update_menu_state(7, 'Tab测试')
        
    def show_trade_test(self):
        """显示物品识别页面"""
        self.main_window._show_trade_test()
        self._update_menu_state(7, '物品识别')
