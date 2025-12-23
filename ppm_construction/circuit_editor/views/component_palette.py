"""
元件库面板 - 显示所有可用元件，支持拖放
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from registry.component_registry import (
    get_all_edge_components,
    get_all_node_components,
    ComponentConfig
)
from views.component_renderer import ComponentRenderer


class ComponentPalette(ttk.Frame):
    """
    元件库面板
    
    显示所有可用元件，点击选择或拖放到画布
    """
    
    ITEM_WIDTH = 80
    ITEM_HEIGHT = 60
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 当前选中的元件
        self.selected_component: Optional[Tuple[bool, int]] = None  # (is_edge, type_id)
        
        # 拖放回调
        self.on_drag_start: Optional[Callable] = None
        self.on_component_selected: Optional[Callable] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 标题
        title = ttk.Label(self, text="Component Library", font=("Arial", 11, "bold"))
        title.pack(pady=(5, 10))
        
        # 创建带滚动条的画布
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, width=self.ITEM_WIDTH + 20, 
                               bg='#F5F5F5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', 
                                  command=self.canvas.yview)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        
        # 内部 Frame
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')
        
        # 绘制元件
        self._draw_components()
        
        # 更新滚动区域
        self.inner_frame.bind('<Configure>', 
                             lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        
        # 鼠标滚轮
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
    
    def _draw_components(self):
        """绘制所有元件"""
        row = 0
        
        # === 边上元件 ===
        edge_label = ttk.Label(self.inner_frame, text="Edge Components", 
                              font=("Arial", 9, "bold"), foreground='#666')
        edge_label.grid(row=row, column=0, pady=(5, 2), sticky='w', padx=5)
        row += 1
        
        for comp in get_all_edge_components():
            if comp.type_id == 6:  # 跳过 Open
                continue
            item = ComponentItem(self.inner_frame, comp, is_edge=True,
                                width=self.ITEM_WIDTH, height=self.ITEM_HEIGHT)
            item.grid(row=row, column=0, padx=5, pady=3)
            item.bind_select(lambda c=comp: self._on_select(True, c))
            # 拖拽功能已禁用，只使用点击选择
            row += 1
        
        # 分隔线
        sep = ttk.Separator(self.inner_frame, orient='horizontal')
        sep.grid(row=row, column=0, sticky='ew', pady=10, padx=5)
        row += 1
        
        # === 节点元件 ===
        node_label = ttk.Label(self.inner_frame, text="Node Components",
                              font=("Arial", 9, "bold"), foreground='#666')
        node_label.grid(row=row, column=0, pady=(5, 2), sticky='w', padx=5)
        row += 1
        
        for comp in get_all_node_components():
            if comp.type_id == 0:  # 跳过 None
                continue
            item = ComponentItem(self.inner_frame, comp, is_edge=False,
                                width=self.ITEM_WIDTH, height=self.ITEM_HEIGHT)
            item.grid(row=row, column=0, padx=5, pady=3)
            item.bind_select(lambda c=comp: self._on_select(False, c))
            # 拖拽功能已禁用，只使用点击选择
            row += 1
    
    def _on_select(self, is_edge: bool, comp: ComponentConfig):
        """选中元件"""
        self.selected_component = (is_edge, comp.type_id)
        if self.on_component_selected:
            self.on_component_selected(is_edge, comp)
    
    def _on_drag(self, event, is_edge: bool, comp: ComponentConfig):
        """开始拖动"""
        if self.on_drag_start:
            self.on_drag_start(event, is_edge, comp)
    
    def _on_mousewheel(self, event):
        """鼠标滚轮"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def get_selected(self) -> Optional[Tuple[bool, int]]:
        """获取当前选中的元件"""
        return self.selected_component


class ComponentItem(ttk.Frame):
    """
    单个元件项
    
    显示元件预览和名称
    """
    
    def __init__(self, parent, comp: ComponentConfig, is_edge: bool,
                 width: int = 80, height: int = 60, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.comp = comp
        self.is_edge = is_edge
        self.width = width
        self.height = height
        
        self._create_widget()
    
    def _create_widget(self):
        """创建控件"""
        # 预览画布
        self.preview_canvas = tk.Canvas(self, width=self.width, height=self.height - 15,
                                        bg='white', highlightthickness=1,
                                        highlightbackground='#DDD')
        self.preview_canvas.pack()
        
        # 名称标签
        name_label = ttk.Label(self, text=self.comp.short_name or self.comp.display_name[:8],
                              font=("Arial", 8))
        name_label.pack()
        
        # 绘制预览
        self._draw_preview()
        
        # 鼠标悬停效果
        self.preview_canvas.bind('<Enter>', self._on_enter)
        self.preview_canvas.bind('<Leave>', self._on_leave)
    
    def _draw_preview(self):
        """绘制元件预览"""
        cx = self.width / 2
        cy = (self.height - 15) / 2
        
        ComponentRenderer.draw_preview(
            self.preview_canvas, 
            self.comp.type_id, 
            self.is_edge,
            cx, cy, 
            size=min(self.width, self.height - 15) - 10
        )
    
    def _on_enter(self, event):
        """鼠标进入"""
        self.preview_canvas.configure(highlightbackground='#2196F3')
    
    def _on_leave(self, event):
        """鼠标离开"""
        self.preview_canvas.configure(highlightbackground='#DDD')
    
    def bind_select(self, callback: Callable):
        """绑定选择事件"""
        self.preview_canvas.bind('<Button-1>', lambda e: callback())
    
    def bind_drag(self, callback: Callable):
        """绑定拖动事件"""
        self.preview_canvas.bind('<B1-Motion>', callback)


class DragGhost(tk.Toplevel):
    """
    拖动时的幽灵窗口
    
    跟随鼠标显示正在拖动的元件
    """
    
    def __init__(self, comp: ComponentConfig, is_edge: bool):
        super().__init__()
        
        self.overrideredirect(True)  # 无边框
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.8)  # 半透明
        
        # 创建预览
        size = 60
        canvas = tk.Canvas(self, width=size, height=size, bg='white',
                          highlightthickness=1, highlightbackground='#2196F3')
        canvas.pack()
        
        ComponentRenderer.draw_preview(canvas, comp.type_id, is_edge,
                                       size/2, size/2, size - 10)
        
        # 初始隐藏
        self.withdraw()
    
    def show_at(self, x: int, y: int):
        """显示在指定位置"""
        self.geometry(f"+{x-30}+{y-30}")
        self.deiconify()
    
    def hide(self):
        """隐藏"""
        self.withdraw()
