from tkinter import *

class Switch(Canvas):
    def __init__(self, master, width=60, height=30, pad_x=3, pad_y=3, bg='white', fg='#07C160', *args, **kwargs):
        super().__init__(master, width=width, height=height, bg=bg, highlightthickness=0)
        self.width = width
        self.height = height
        self.pad_x = pad_x
        self.pad_y = pad_y
        self.switch_width = width - (pad_x * 2)
        self.switch_height = height - (pad_y * 2)
        self.fg = fg
        
        # 状态变量
        self.checked = BooleanVar(value=kwargs.get('default', True))
        self.checked.trace_add('write', self._update_state)
        
        # 动画相关
        self.animation_frames = 5  # 动画帧数
        self.animation_running = False
        self.current_x = 0  # 当前滑块x位置
        self.target_x = 0   # 目标x位置
        self.hover = False  # 鼠标悬停状态
        
        # 初始化布局
        self._init_layout()
        
        # 绑定事件
        self.bind('<Button-1>', self._toggle)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
    def _init_layout(self):
        """初始化开关布局和位置"""
        radius = self.switch_height // 2
        # 计算目标位置
        if self.checked.get():
            self.target_x = self.width - self.pad_x - (self.switch_height - 2)
        else:
            self.target_x = self.pad_x
        self.current_x = self.target_x
        self._draw()
        
    def _start_animation(self):
        """开始滑块动画"""
        if not self.animation_running:
            self.animation_running = True
            self._animate()
            
    def _animate(self):
        """执行动画帧"""
        if not self.animation_running:
            return
            
        # 计算下一帧位置
        dx = (self.target_x - self.current_x) / self.animation_frames
        self.current_x += dx
        
        # 检查是否到达目标
        if abs(self.current_x - self.target_x) < 1:
            self.current_x = self.target_x
            self.animation_running = False
        
        self._draw()
        
        # 继续动画
        if self.animation_running:
            self.after(16, self._animate)  # 约60fps
        
    def _draw(self):
        """绘制开关"""
        self.delete('all')  # 清除画布
        
        # 计算滑块中心位置
        radius = self.switch_height // 2
        radius2 = self.switch_height // 0.8
        
        # 计算背景颜色（根据滑块位置渐变）
        progress = (self.current_x - self.pad_x) / (self.width - self.pad_x * 2 - self.switch_height + 2)
        if progress > 0.5:
            fill = self.fg
        else:
            fill = '#e9e9ea'
        
        # 绘制背景（圆角矩形）
        self.create_rounded_rect(
            self.pad_x, 
            self.pad_y, 
            self.switch_width + self.pad_x,
            self.switch_height + self.pad_y,
            radius2,
            fill=fill
        )
        
        # 绘制滑块（白色圆形）
        thumb_radius = radius - 1 if not self.hover else radius
        self.create_circle(
            self.current_x + radius,
            self.height // 2,
            thumb_radius,
            fill='white',
            outline='#000016' if not self.hover else '#000026'  # 悬停时加深阴影
        )
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """绘制圆角矩形"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
        
    def create_circle(self, x, y, r, **kwargs):
        """绘制圆形"""
        return self.create_oval(x - r, y - r, x + r, y + r, **kwargs)
        
    def _toggle(self, event=None):
        """切换开关状态"""
        self.checked.set(not self.checked.get())
        
    def _update_state(self, *args):
        """状态变化时更新"""
        # 计算新的目标位置
        if self.checked.get():
            self.target_x = self.width - self.pad_x - (self.switch_height - 2)
        else:
            self.target_x = self.pad_x
            
        # 开始动画
        self._start_animation()
        
    def _on_enter(self, event=None):
        """鼠标进入时"""
        self.hover = True
        self._draw()
        
    def _on_leave(self, event=None):
        """鼠标离开时"""
        self.hover = False
        self._draw()
        
    def get(self):
        return self.checked.get()
        
    def set(self, value):
        self.checked.set(bool(value))
