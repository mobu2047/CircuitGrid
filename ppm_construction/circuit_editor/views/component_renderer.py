"""
元件渲染器 - 在 Canvas 上绘制元件符号

每种元件类型注册一个绘制函数，支持扩展
"""
import tkinter as tk
from typing import Callable, Dict, Tuple
import math


class ComponentRenderer:
    """
    元件渲染器
    
    使用注册表模式，每种元件类型注册一个绘制函数
    """
    
    # 绘制函数注册表: {type_id: draw_function}
    _edge_renderers: Dict[int, Callable] = {}
    _node_renderers: Dict[int, Callable] = {}
    
    @classmethod
    def register_edge(cls, type_id: int):
        """装饰器：注册边上元件绘制函数"""
        def decorator(func: Callable):
            cls._edge_renderers[type_id] = func
            return func
        return decorator
    
    @classmethod
    def register_node(cls, type_id: int):
        """装饰器：注册节点元件绘制函数"""
        def decorator(func: Callable):
            cls._node_renderers[type_id] = func
            return func
        return decorator
    
    @classmethod
    def draw_edge_component(cls, canvas: tk.Canvas, type_id: int,
                           x1: float, y1: float, x2: float, y2: float,
                           color: str = "#333333", scale: float = 1.0,
                           label: str = "", direction: int = 0) -> None:
        """
        绘制边上元件
        
        Args:
            canvas: Tkinter Canvas
            type_id: 元件类型 ID
            x1, y1: 起点坐标
            x2, y2: 终点坐标
            color: 颜色
            scale: 缩放比例
            label: 标签文字
            direction: 方向 (0=Forward, 1=Reverse)
        """
        renderer = cls._edge_renderers.get(type_id, cls._draw_default_edge)
        renderer(canvas, x1, y1, x2, y2, color, scale, label, direction)
    
    @classmethod
    def draw_node_component(cls, canvas: tk.Canvas, type_id: int,
                           x: float, y: float, orientation: int = 1,
                           color: str = "#333333", scale: float = 1.0,
                           label: str = "", cell_size: float = 80) -> Dict[str, Tuple[float, float]]:
        """
        绘制节点元件
        
        Args:
            canvas: Tkinter Canvas
            type_id: 元件类型 ID
            x, y: 中心坐标
            orientation: 朝向 (0=up, 1=right, 2=down, 3=left)
            color: 颜色
            scale: 缩放比例
            label: 标签文字
            cell_size: 网格单元大小（用于计算引脚长度）
            
        Returns:
            引脚位置字典 {'pin_name': (x, y), ...}
        """
        renderer = cls._node_renderers.get(type_id, cls._draw_default_node)
        return renderer(canvas, x, y, orientation, color, scale, label, cell_size)
    
    @staticmethod
    def _draw_default_edge(canvas, x1, y1, x2, y2, color, scale, label, direction=0):
        """默认边绘制"""
        canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
    
    @staticmethod
    def _draw_default_node(canvas, x, y, orientation, color, scale, label, cell_size=80):
        """默认节点绘制"""
        r = 10 * scale
        canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, width=2)
        return {}
    
    @classmethod
    def draw_preview(cls, canvas: tk.Canvas, type_id: int, is_edge: bool,
                    x: float, y: float, size: float = 60) -> None:
        """
        绘制元件预览（用于元件库）
        
        Args:
            canvas: Canvas
            type_id: 元件类型
            is_edge: 是否是边上元件
            x, y: 中心位置
            size: 预览大小
        """
        if is_edge:
            # 水平绘制边元件
            x1, y1 = x - size/2 + 10, y
            x2, y2 = x + size/2 - 10, y
            cls.draw_edge_component(canvas, type_id, x1, y1, x2, y2, 
                                   color="#333333", scale=0.8)
        else:
            # 绘制节点元件（使用较小的 cell_size 使预览紧凑）
            cls.draw_node_component(canvas, type_id, x, y, orientation=1,
                                   color="#333333", scale=0.8, cell_size=40)


# ============================================================
# 注册边上元件绘制函数
# ============================================================

@ComponentRenderer.register_edge(0)  # TYPE_SHORT
def draw_short(canvas, x1, y1, x2, y2, color, scale, label, direction=0):
    """短路线"""
    canvas.create_line(x1, y1, x2, y2, fill=color, width=2*scale)


@ComponentRenderer.register_edge(1)  # TYPE_VOLTAGE_SOURCE
def draw_voltage_source(canvas, x1, y1, x2, y2, color, scale, label, direction=0):
    """
    电压源 - 正负标记在圆圈内部
    
    direction=0: 正极朝向起点(x1,y1)，负极朝向终点(x2,y2)
    direction=1: 正极朝向终点(x2,y2)，负极朝向起点(x1,y1)
    """
    mx, my = (x1+x2)/2, (y1+y2)/2
    r = 12 * scale
    
    # 判断边是水平还是垂直
    is_horizontal = abs(x2-x1) > abs(y2-y1)
    
    if is_horizontal:
        # 水平边：连线水平
        canvas.create_line(x1, y1, mx-r, my, fill=color, width=2*scale)
        canvas.create_line(mx+r, my, x2, y2, fill=color, width=2*scale)
        # 圆圈
        canvas.create_oval(mx-r, my-r, mx+r, my+r, outline=color, width=2*scale)
        
        # 正负极标记在圆内，根据 direction 决定位置
        # direction=0: + 在左半圆, - 在右半圆
        # direction=1: + 在右半圆, - 在左半圆
        plus_x = mx - r/2 if direction == 0 else mx + r/2
        minus_x = mx + r/2 if direction == 0 else mx - r/2
        
        # + 号
        canvas.create_line(plus_x-3, my, plus_x+3, my, fill=color, width=1.5*scale)
        canvas.create_line(plus_x, my-3, plus_x, my+3, fill=color, width=1.5*scale)
        # - 号
        canvas.create_line(minus_x-3, my, minus_x+3, my, fill=color, width=1.5*scale)
        
        # 标签在上方
        if label:
            canvas.create_text(mx, my-r-8, text=label, fill=color, font=("Arial", 9))
    else:
        # 垂直边：连线垂直
        canvas.create_line(x1, y1, mx, my-r, fill=color, width=2*scale)
        canvas.create_line(mx, my+r, x2, y2, fill=color, width=2*scale)
        # 圆圈
        canvas.create_oval(mx-r, my-r, mx+r, my+r, outline=color, width=2*scale)
        
        # 正负极标记在圆内，根据 direction 决定位置
        # direction=0: + 在上半圆, - 在下半圆
        # direction=1: + 在下半圆, - 在上半圆
        plus_y = my - r/2 if direction == 0 else my + r/2
        minus_y = my + r/2 if direction == 0 else my - r/2
        
        # + 号
        canvas.create_line(mx-3, plus_y, mx+3, plus_y, fill=color, width=1.5*scale)
        canvas.create_line(mx, plus_y-3, mx, plus_y+3, fill=color, width=1.5*scale)
        # - 号
        canvas.create_line(mx-3, minus_y, mx+3, minus_y, fill=color, width=1.5*scale)
        
        # 标签在右侧
        if label:
            canvas.create_text(mx+r+10, my, text=label, fill=color, font=("Arial", 9), anchor='w')


@ComponentRenderer.register_edge(2)  # TYPE_CURRENT_SOURCE
def draw_current_source(canvas, x1, y1, x2, y2, color, scale, label, direction=0):
    """
    电流源 - 箭头指示电流方向
    
    direction=0: 电流从起点(x1,y1)流向终点(x2,y2)
    direction=1: 电流从终点(x2,y2)流向起点(x1,y1)
    """
    mx, my = (x1+x2)/2, (y1+y2)/2
    r = 12 * scale
    
    # 判断边是水平还是垂直
    is_horizontal = abs(x2-x1) > abs(y2-y1)
    
    if is_horizontal:
        # 水平边：连线水平
        canvas.create_line(x1, y1, mx-r, my, fill=color, width=2*scale)
        canvas.create_line(mx+r, my, x2, y2, fill=color, width=2*scale)
        canvas.create_oval(mx-r, my-r, mx+r, my+r, outline=color, width=2*scale)
        
        # 箭头方向根据 direction 决定
        # direction=0: 箭头指向 x2（右）, direction=1: 箭头指向 x1（左）
        if (x2 > x1 and direction == 0) or (x2 < x1 and direction == 1):
            # 箭头指向右
            canvas.create_line(mx-6, my, mx+6, my, fill=color, width=2*scale, arrow=tk.LAST)
        else:
            # 箭头指向左
            canvas.create_line(mx+6, my, mx-6, my, fill=color, width=2*scale, arrow=tk.LAST)
        
        if label:
            canvas.create_text(mx, my-r-10, text=label, fill=color, font=("Arial", 9))
    else:
        # 垂直边：连线垂直
        canvas.create_line(x1, y1, mx, my-r, fill=color, width=2*scale)
        canvas.create_line(mx, my+r, x2, y2, fill=color, width=2*scale)
        canvas.create_oval(mx-r, my-r, mx+r, my+r, outline=color, width=2*scale)
        
        # 箭头方向根据 direction 决定
        # direction=0: 箭头指向 y2（下）, direction=1: 箭头指向 y1（上）
        if (y2 > y1 and direction == 0) or (y2 < y1 and direction == 1):
            # 箭头指向下
            canvas.create_line(mx, my-6, mx, my+6, fill=color, width=2*scale, arrow=tk.LAST)
        else:
            # 箭头指向上
            canvas.create_line(mx, my+6, mx, my-6, fill=color, width=2*scale, arrow=tk.LAST)
        
        if label:
            canvas.create_text(mx+r+10, my, text=label, fill=color, font=("Arial", 9), anchor='w')


@ComponentRenderer.register_edge(3)  # TYPE_RESISTOR
def draw_resistor(canvas, x1, y1, x2, y2, color, scale, label, direction=0):
    """电阻"""
    mx, my = (x1+x2)/2, (y1+y2)/2
    
    # 判断方向
    is_horizontal = abs(x2-x1) > abs(y2-y1)
    
    if is_horizontal:
        w, h = 24 * scale, 8 * scale
        # 连接线
        canvas.create_line(x1, y1, mx-w/2, my, fill=color, width=2*scale)
        canvas.create_line(mx+w/2, my, x2, y2, fill=color, width=2*scale)
        # 矩形
        canvas.create_rectangle(mx-w/2, my-h/2, mx+w/2, my+h/2, 
                               outline=color, width=2*scale)
    else:
        w, h = 8 * scale, 24 * scale
        canvas.create_line(x1, y1, mx, my-h/2, fill=color, width=2*scale)
        canvas.create_line(mx, my+h/2, x2, y2, fill=color, width=2*scale)
        canvas.create_rectangle(mx-w/2, my-h/2, mx+w/2, my+h/2,
                               outline=color, width=2*scale)
    
    if label:
        offset = h/2 + 10 if is_horizontal else w/2 + 15
        canvas.create_text(mx + (0 if is_horizontal else offset), 
                          my - (offset if is_horizontal else 0),
                          text=label, fill=color, font=("Arial", 9))


@ComponentRenderer.register_edge(4)  # TYPE_CAPACITOR
def draw_capacitor(canvas, x1, y1, x2, y2, color, scale, label, direction=0):
    """电容"""
    mx, my = (x1+x2)/2, (y1+y2)/2
    gap = 4 * scale
    plate_len = 14 * scale
    
    is_horizontal = abs(x2-x1) > abs(y2-y1)
    
    if is_horizontal:
        # 连接线
        canvas.create_line(x1, y1, mx-gap, my, fill=color, width=2*scale)
        canvas.create_line(mx+gap, my, x2, y2, fill=color, width=2*scale)
        # 极板
        canvas.create_line(mx-gap, my-plate_len, mx-gap, my+plate_len, 
                          fill=color, width=2*scale)
        canvas.create_line(mx+gap, my-plate_len, mx+gap, my+plate_len,
                          fill=color, width=2*scale)
    else:
        canvas.create_line(x1, y1, mx, my-gap, fill=color, width=2*scale)
        canvas.create_line(mx, my+gap, x2, y2, fill=color, width=2*scale)
        canvas.create_line(mx-plate_len, my-gap, mx+plate_len, my-gap,
                          fill=color, width=2*scale)
        canvas.create_line(mx-plate_len, my+gap, mx+plate_len, my+gap,
                          fill=color, width=2*scale)
    
    if label:
        canvas.create_text(mx, my-plate_len-8, text=label, fill=color, font=("Arial", 9))


@ComponentRenderer.register_edge(5)  # TYPE_INDUCTOR
def draw_inductor(canvas, x1, y1, x2, y2, color, scale, label, direction=0):
    """电感 - 使用大角度圆弧线圈（所有半圆在同一侧，黑色）"""
    mx, my = (x1+x2)/2, (y1+y2)/2
    
    # 使用黑色
    inductor_color = "#000000"
    
    is_horizontal = abs(x2-x1) > abs(y2-y1)
    num_loops = 4
    loop_r = 8 * scale  # 增大半径，使圆弧更饱满
    loop_spacing = loop_r * 1.8  # 调整间距，使整体协调
    arc_extent = 200  # 增大角度（从180度增加到200度），使圆弧更美观
    
    if is_horizontal:
        total_w = loop_spacing * (num_loops - 1) + loop_r * 2
        start_x = mx - total_w/2
        
        canvas.create_line(x1, y1, start_x, my, fill=inductor_color, width=2*scale)
        canvas.create_line(start_x + total_w, my, x2, y2, fill=inductor_color, width=2*scale)
        
        # 所有圆弧都在上方（同一侧），使用更大的角度
        for i in range(num_loops):
            cx = start_x + loop_r + i * loop_spacing
            # 上半圆弧，角度更大
            canvas.create_arc(cx-loop_r, my-loop_r, cx+loop_r, my,
                            start=-10, extent=arc_extent, style=tk.ARC,
                            outline=inductor_color, width=2*scale)
    else:
        total_h = loop_spacing * (num_loops - 1) + loop_r * 2
        start_y = my - total_h/2
        
        canvas.create_line(x1, y1, mx, start_y, fill=inductor_color, width=2*scale)
        canvas.create_line(mx, start_y + total_h, x2, y2, fill=inductor_color, width=2*scale)
        
        # 所有圆弧都在右侧（同一侧），使用更大的角度
        for i in range(num_loops):
            cy = start_y + loop_r + i * loop_spacing
            # 右半圆弧，角度更大
            canvas.create_arc(mx, cy-loop_r, mx+loop_r, cy+loop_r,
                            start=260, extent=arc_extent, style=tk.ARC,
                            outline=inductor_color, width=2*scale)
    
    if label:
        canvas.create_text(mx, my-loop_r-12, text=label, fill=color, font=("Arial", 9))


@ComponentRenderer.register_edge(6)  # TYPE_OPEN
def draw_open(canvas, x1, y1, x2, y2, color, scale, label, direction=0):
    """断路"""
    mx, my = (x1+x2)/2, (y1+y2)/2
    gap = 8 * scale
    
    is_horizontal = abs(x2-x1) > abs(y2-y1)
    
    if is_horizontal:
        canvas.create_line(x1, y1, mx-gap, my, fill=color, width=2*scale)
        canvas.create_line(mx+gap, my, x2, y2, fill=color, width=2*scale)
    else:
        canvas.create_line(x1, y1, mx, my-gap, fill=color, width=2*scale)
        canvas.create_line(mx, my+gap, x2, y2, fill=color, width=2*scale)


# ============================================================
# 注册节点元件绘制函数
# ============================================================

@ComponentRenderer.register_node(1)  # NODE_TYPE_TRANSISTOR_NPN
def draw_npn(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """
    NPN 三极管 - 引脚延伸到相邻网格节点
    
    orientation: 基极指向的方向 (0=up, 1=right, 2=down, 3=left)
    """
    # 尺寸参数
    body_r = 15 * scale
    lead_len = cell_size / 2  # 引脚延伸到相邻节点（半个格子距离）
    
    # 根据朝向计算旋转（与 LaTeX 相反：左右方向相反，上下方向相反）
    # LaTeX: 0=up(90°), 1=right(0°), 2=down(-90°), 3=left(180°)
    # Tkinter: 0=up(-90°), 1=right(180°), 2=down(90°), 3=left(0°)
    angles = {0: -90, 1: 180, 2: 90, 3: 0}
    angle = math.radians(angles.get(orientation, 0))
    
    def rotate(px, py):
        """绕中心旋转点"""
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        return x + px*cos_a - py*sin_a, y + px*sin_a + py*cos_a
    
    # 基极（指向 orientation 方向）- 延伸到相邻节点
    bx1, by1 = rotate(lead_len, 0)  # 基极末端（相邻节点位置）
    bx2, by2 = rotate(body_r, 0)    # 基极连接点
    canvas.create_line(bx1, by1, bx2, by2, fill=color, width=2*scale)
    
    # 主体竖线
    lx1, ly1 = rotate(body_r, -body_r*0.7)
    lx2, ly2 = rotate(body_r, body_r*0.7)
    canvas.create_line(lx1, ly1, lx2, ly2, fill=color, width=3*scale)
    
    # 集电极和发射极位置：与 CircuitTikZ 标准一致
    # CircuitTikZ 中 npn 节点标准：C 在上，E 在下
    # 工具中也应该：C 在上（负y方向），E 在下（正y方向）
    # 这样工具和 LaTeX 渲染就完全一致了
    cx1, cy1 = rotate(body_r, -body_r*0.4)  # C在上
    cx2, cy2 = rotate(-body_r*0.3, -body_r*0.8)
    cx3, cy3 = rotate(0, -lead_len)  # 集电极在上方（负y方向）
    ex1, ey1 = rotate(body_r, body_r*0.4)  # E在下
    ex2, ey2 = rotate(-body_r*0.3, body_r*0.8)
    ex3, ey3 = rotate(0, lead_len)  # 发射极在下方（正y方向）
    
    canvas.create_line(cx1, cy1, cx2, cy2, fill=color, width=2*scale)
    canvas.create_line(cx2, cy2, cx3, cy3, fill=color, width=2*scale)
    canvas.create_line(ex1, ey1, ex2, ey2, fill=color, width=2*scale)
    canvas.create_line(ex2, ey2, ex3, ey3, fill=color, width=2*scale)
    
    # 箭头（在发射极上，指向外）- E 在下方
    canvas.create_line(ex1, ey1, ex2, ey2, fill=color, width=2*scale, arrow=tk.LAST, arrowshape=(8, 10, 4))
    
    # 标签
    if label:
        lx, ly = rotate(body_r + 15, -body_r)
        canvas.create_text(lx, ly, text=label, fill=color, font=("Arial", 9), anchor='w')
    
    # #region agent log
    try:
        import json
        with open(r"c:\Users\tiany\Desktop\MAPS-master\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"component_renderer.py:431","message":"NPN draw_npn return","data":{"orientation":orientation,"base":(bx1,by1),"collector":(cx3,cy3),"emitter":(ex3,ey3)},"timestamp":int(__import__("time").time()*1000)}) + "\n")
    except: pass
    # #endregion
    
    # 返回引脚位置（末端坐标，对应相邻节点）
    return {
        'base': (bx1, by1),
        'collector': (cx3, cy3),
        'emitter': (ex3, ey3)
    }


@ComponentRenderer.register_node(2)  # NODE_TYPE_TRANSISTOR_PNP
def draw_pnp(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """
    PNP 三极管 - 引脚延伸到相邻网格节点（与 NPN 类似，箭头方向相反）
    """
    body_r = 15 * scale
    lead_len = cell_size / 2
    
    # 与 LaTeX 相反：左右方向相反，上下方向相反
    angles = {0: -90, 1: 180, 2: 90, 3: 0}
    angle = math.radians(angles.get(orientation, 0))
    
    def rotate(px, py):
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        return x + px*cos_a - py*sin_a, y + px*sin_a + py*cos_a
    
    # 基极（指向 orientation 方向）
    bx1, by1 = rotate(lead_len, 0)
    bx2, by2 = rotate(body_r, 0)
    canvas.create_line(bx1, by1, bx2, by2, fill=color, width=2*scale)
    
    # 主体竖线
    lx1, ly1 = rotate(body_r, -body_r*0.7)
    lx2, ly2 = rotate(body_r, body_r*0.7)
    canvas.create_line(lx1, ly1, lx2, ly2, fill=color, width=3*scale)
    
    # 此代码用于绘制PNP型三极管的集电极（C）和发射极（E）的可视化连接线端点坐标。
    # 其中：
    #   - 集电极端（C，collector）始终位于器件的“上方”。
    #   - 发射极端（E，emitter）始终位于器件的“下方”。
    # 相关坐标计算通过 rotate() 方法按当前方向旋转和偏移。
    # 这样即保证三极管无论旋转到哪个方向，C/E端都能与相邻网格节点中心自动对齐，便于连线和逻辑统一。
    cx1, cy1 = rotate(body_r, -body_r*0.4)         # 集电极线的起点（靠近主体）
    cx2, cy2 = rotate(-body_r*0.3, -body_r*0.8)    # 集电极线的拐角
    cx3, cy3 = rotate(0, -lead_len)                # 集电极末端（上方远点，连到节点）
    ex1, ey1 = rotate(body_r, body_r*0.4)          # 发射极线的起点（靠近主体）
    ex2, ey2 = rotate(-body_r*0.3, body_r*0.8)     # 发射极线的拐角
    ex3, ey3 = rotate(0, lead_len)                 # 发射极末端（下方远点，连到节点）
    
    canvas.create_line(cx1, cy1, cx2, cy2, fill=color, width=2*scale)
    canvas.create_line(cx2, cy2, cx3, cy3, fill=color, width=2*scale)
    # 箭头在发射极上，指向内
    canvas.create_line(ex2, ey2, ex1, ey1, fill=color, width=2*scale, arrow=tk.LAST, arrowshape=(8, 10, 4))
    canvas.create_line(ex2, ey2, ex3, ey3, fill=color, width=2*scale)
    
    # 标签
    if label:
        lx, ly = rotate(body_r + 15, -body_r)
        canvas.create_text(lx, ly, text=label, fill=color, font=("Arial", 9), anchor='w')
    
    # #region agent log
    try:
        import json
        with open(r"c:\Users\tiany\Desktop\MAPS-master\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"F","location":"component_renderer.py:477","message":"PNP draw_pnp return","data":{"orientation":orientation,"base":(bx1,by1),"collector":(cx3,cy3),"emitter":(ex3,ey3)},"timestamp":int(__import__("time").time()*1000)}) + "\n")
    except: pass
    # #endregion
    
    return {
        'base': (bx1, by1),
        'collector': (cx3, cy3),
        'emitter': (ex3, ey3)
    }


@ComponentRenderer.register_node(3)  # NODE_TYPE_DIODE
def draw_diode(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """二极管"""
    size = 12 * scale
    lead_len = 15 * scale
    
    # 与 LaTeX 相反：左右方向相反，上下方向相反
    angles = {0: -90, 1: 180, 2: 90, 3: 0}
    angle = math.radians(angles.get(orientation, 0))
    
    def rotate(px, py):
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        return x + px*cos_a - py*sin_a, y + px*sin_a + py*cos_a
    
    # 阳极引线
    ax1, ay1 = rotate(-size - lead_len, 0)
    ax2, ay2 = rotate(-size, 0)
    canvas.create_line(ax1, ay1, ax2, ay2, fill=color, width=2*scale)
    
    # 三角形
    canvas.create_polygon(
        *rotate(-size, -size),
        *rotate(-size, size),
        *rotate(size, 0),
        outline=color, fill='', width=2*scale
    )
    
    # 阴极竖线
    canvas.create_line(*rotate(size, -size), *rotate(size, size),
                      fill=color, width=2*scale)
    
    # 阴极引线
    cx1, cy1 = rotate(size, 0)
    cx2, cy2 = rotate(size + lead_len, 0)
    canvas.create_line(cx1, cy1, cx2, cy2, fill=color, width=2*scale)
    
    if label:
        canvas.create_text(x, y-size-10, text=label, fill=color, font=("Arial", 9))
    
    return {
        'anode': (ax1, ay1),
        'cathode': (cx2, cy2)
    }


@ComponentRenderer.register_node(4)  # NODE_TYPE_OPAMP
def draw_opamp(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """运算放大器"""
    w = 30 * scale
    h = 40 * scale
    lead_len = 15 * scale
    
    # 与 LaTeX 相反：左右方向相反，上下方向相反
    angles = {0: -90, 1: 180, 2: 90, 3: 0}
    angle = math.radians(angles.get(orientation, 0))
    
    def rotate(px, py):
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        return x + px*cos_a - py*sin_a, y + px*sin_a + py*cos_a
    
    # 三角形主体
    canvas.create_polygon(
        *rotate(-w, -h/2),
        *rotate(-w, h/2),
        *rotate(w, 0),
        outline=color, fill='white', width=2*scale
    )
    
    # + 输入（上）
    px1, py1 = rotate(-w - lead_len, -h/4)
    px2, py2 = rotate(-w, -h/4)
    canvas.create_line(px1, py1, px2, py2, fill=color, width=2*scale)
    canvas.create_text(*rotate(-w+8, -h/4), text="+", fill=color, font=("Arial", 10, "bold"))
    
    # - 输入（下）
    mx1, my1 = rotate(-w - lead_len, h/4)
    mx2, my2 = rotate(-w, h/4)
    canvas.create_line(mx1, my1, mx2, my2, fill=color, width=2*scale)
    canvas.create_text(*rotate(-w+8, h/4), text="−", fill=color, font=("Arial", 10, "bold"))
    
    # 输出
    ox1, oy1 = rotate(w, 0)
    ox2, oy2 = rotate(w + lead_len, 0)
    canvas.create_line(ox1, oy1, ox2, oy2, fill=color, width=2*scale)
    
    if label:
        canvas.create_text(x, y-h/2-10, text=label, fill=color, font=("Arial", 9))
    
    return {
        'in+': (px1, py1),
        'in-': (mx1, my1),
        'out': (ox2, oy2)
    }


@ComponentRenderer.register_node(5)  # NODE_TYPE_MOSFET
def draw_mosfet(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """MOSFET - 类似三极管但符号不同"""
    # 使用类似三极管的绘制，但符号为 MOSFET
    body_r = 15 * scale
    lead_len = cell_size / 2
    
    angles = {0: -90, 1: 180, 2: 90, 3: 0}
    angle = math.radians(angles.get(orientation, 0))
    
    def rotate(px, py):
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        return x + px*cos_a - py*sin_a, y + px*sin_a + py*cos_a
    
    # 栅极（Gate）- 指向 orientation 方向
    gx1, gy1 = rotate(lead_len, 0)
    gx2, gy2 = rotate(body_r, 0)
    canvas.create_line(gx1, gy1, gx2, gy2, fill=color, width=2*scale)
    
    # 主体（类似三极管但不同）
    # 漏极和源极位置：根据用户反馈修复
    # - MOSFET right/left: 上下镜像翻转 -> 需要不翻转（D在上，S在下）
    # - MOSFET up/down: 左右接口方向正确，但是上下镜像翻转 -> 需要不翻转（D在上，S在下）
    # 所有方向都使用标准位置：D在上，S在下
    dx1, dy1 = rotate(body_r, -body_r*0.4)  # D在上
    dx2, dy2 = rotate(-body_r*0.3, -body_r*0.8)
    dx3, dy3 = rotate(0, -lead_len)  # 漏极在上方
    sx1, sy1 = rotate(body_r, body_r*0.4)  # S在下
    sx2, sy2 = rotate(-body_r*0.3, body_r*0.8)
    sx3, sy3 = rotate(0, lead_len)  # 源极在下方
    
    canvas.create_line(dx1, dy1, dx2, dy2, fill=color, width=2*scale)
    canvas.create_line(dx2, dy2, dx3, dy3, fill=color, width=2*scale)
    # 箭头在源极上，指向外（类似 NPN）
    canvas.create_line(sx1, sy1, sx2, sy2, fill=color, width=2*scale, arrow=tk.LAST, arrowshape=(8, 10, 4))
    canvas.create_line(sx2, sy2, sx3, sy3, fill=color, width=2*scale)
    
    # 主体竖线
    lx1, ly1 = rotate(body_r, -body_r*0.7)
    lx2, ly2 = rotate(body_r, body_r*0.7)
    canvas.create_line(lx1, ly1, lx2, ly2, fill=color, width=3*scale)
    
    # 标签
    if label:
        lx, ly = rotate(body_r + 15, -body_r)
        canvas.create_text(lx, ly, text=label, fill=color, font=("Arial", 9), anchor='w')
    
    # #region agent log
    try:
        import json
        with open(r"c:\Users\tiany\Desktop\MAPS-master\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"component_renderer.py:624","message":"MOSFET draw_mosfet return","data":{"orientation":orientation,"gate":(gx1,gy1),"drain":(dx3,dy3),"source":(sx3,sy3)},"timestamp":int(__import__("time").time()*1000)}) + "\n")
    except: pass
    # #endregion
    
    return {
        'gate': (gx1, gy1),
        'drain': (dx3, dy3),
        'source': (sx3, sy3)
    }


@ComponentRenderer.register_node(6)  # NODE_TYPE_MOSFET_P
def draw_mosfet_p(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """P 沟道 MOSFET - 与 N 沟道类似，但符号不同（箭头方向相反）"""
    body_r = 15 * scale
    lead_len = cell_size / 2
    
    angles = {0: -90, 1: 180, 2: 90, 3: 0}
    angle = math.radians(angles.get(orientation, 0))
    
    def rotate(px, py):
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        return x + px*cos_a - py*sin_a, y + px*sin_a + py*cos_a
    
    # 栅极（Gate）- 指向 orientation 方向
    gx1, gy1 = rotate(lead_len, 0)
    gx2, gy2 = rotate(body_r, 0)
    canvas.create_line(gx1, gy1, gx2, gy2, fill=color, width=2*scale)
    
    # 主体（类似三极管但不同）
    # P 沟道 MOSFET：D在上，S在下（与 N 沟道相同）
    dx1, dy1 = rotate(body_r, -body_r*0.4)  # D在上
    dx2, dy2 = rotate(-body_r*0.3, -body_r*0.8)
    dx3, dy3 = rotate(0, -lead_len)  # 漏极在上方
    sx1, sy1 = rotate(body_r, body_r*0.4)  # S在下
    sx2, sy2 = rotate(-body_r*0.3, body_r*0.8)
    sx3, sy3 = rotate(0, lead_len)  # 源极在下方
    
    canvas.create_line(dx1, dy1, dx2, dy2, fill=color, width=2*scale)
    canvas.create_line(dx2, dy2, dx3, dy3, fill=color, width=2*scale)
    # 箭头在源极上，指向内（类似 PNP）
    canvas.create_line(sx2, sy2, sx1, sy1, fill=color, width=2*scale, arrow=tk.LAST, arrowshape=(8, 10, 4))
    canvas.create_line(sx2, sy2, sx3, sy3, fill=color, width=2*scale)
    
    # 主体竖线
    lx1, ly1 = rotate(body_r, -body_r*0.7)
    lx2, ly2 = rotate(body_r, body_r*0.7)
    canvas.create_line(lx1, ly1, lx2, ly2, fill=color, width=3*scale)
    
    # P 沟道 MOSFET 的特殊标记：在源极上添加一个小圆圈（表示 P 沟道）
    # 在源极连接点附近绘制一个小圆圈
    circle_x, circle_y = rotate(body_r*0.5, body_r*0.3)
    canvas.create_oval(circle_x - 3*scale, circle_y - 3*scale, 
                       circle_x + 3*scale, circle_y + 3*scale, 
                       outline=color, width=1*scale)
    
    # 标签
    if label:
        lx, ly = rotate(body_r + 15, -body_r)
        canvas.create_text(lx, ly, text=label, fill=color, font=("Arial", 9), anchor='w')
    
    return {
        'gate': (gx1, gy1),
        'drain': (dx3, dy3),
        'source': (sx3, sy3)
    }


@ComponentRenderer.register_node(7)  # NODE_TYPE_GND
def draw_gnd(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """接地符号"""
    # 接地符号：水平线 + 垂直递减的短线
    h_len = 20 * scale
    v_len = 15 * scale
    
    # 水平线
    canvas.create_line(x - h_len, y, x + h_len, y, fill=color, width=3*scale)
    
    # 垂直递减的短线
    for i in range(3):
        w = h_len * (1 - i * 0.3)
        y_pos = y + v_len * (i + 1)
        canvas.create_line(x - w, y_pos, x + w, y_pos, fill=color, width=2*scale)
    
    if label:
        canvas.create_text(x, y - v_len - 10, text=label, fill=color, font=("Arial", 9))
    
    return {'gnd': (x, y + v_len * 4)}


@ComponentRenderer.register_node(8)  # NODE_TYPE_VCC
def draw_vcc(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """VCC 电源符号 - 实心圆点"""
    r = 8 * scale
    # 实心圆点
    canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, fill=color, width=2*scale)
    
    # 标签
    if label:
        canvas.create_text(x, y-r-15, text=label, fill=color, font=("Arial", 9))
    
    return {'vcc': (x, y)}


@ComponentRenderer.register_node(9)  # NODE_TYPE_VDD
def draw_vdd(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """VDD 电源符号 - 实心圆点"""
    r = 8 * scale
    # 实心圆点
    canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, fill=color, width=2*scale)
    
    # 标签
    if label:
        canvas.create_text(x, y-r-15, text=label, fill=color, font=("Arial", 9))
    
    return {'vdd': (x, y)}


@ComponentRenderer.register_node(10)  # NODE_TYPE_VSS
def draw_vss(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """VSS 电源符号 - 实心圆点"""
    r = 8 * scale
    # 实心圆点
    canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, fill=color, width=2*scale)
    
    # 标签
    if label:
        canvas.create_text(x, y+r+15, text=label, fill=color, font=("Arial", 9))
    
    return {'vss': (x, y)}


@ComponentRenderer.register_node(11)  # NODE_TYPE_VEE
def draw_vee(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """VEE 电源符号 - 实心圆点"""
    r = 8 * scale
    # 实心圆点
    canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, fill=color, width=2*scale)
    
    # 标签
    if label:
        canvas.create_text(x, y+r+15, text=label, fill=color, font=("Arial", 9))
    
    return {'vee': (x, y)}


@ComponentRenderer.register_node(12)  # NODE_TYPE_VBB
def draw_vbb(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """VBB 电源符号 - 实心圆点"""
    r = 8 * scale
    # 实心圆点
    canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, fill=color, width=2*scale)
    
    # 标签
    if label:
        canvas.create_text(x, y-r-15, text=label, fill=color, font=("Arial", 9))
    
    return {'vbb': (x, y)}


@ComponentRenderer.register_node(13)  # NODE_TYPE_VIN
def draw_vin(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """输入端口 VIN - 空心圆点"""
    r = 8 * scale
    # 空心圆点
    canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, fill="white", width=2*scale)
    
    # 标签
    if label:
        canvas.create_text(x, y-r-15, text=label, fill=color, font=("Arial", 9))
    
    return {'vin': (x, y)}


@ComponentRenderer.register_node(14)  # NODE_TYPE_VOUT
def draw_vout(canvas, x, y, orientation, color, scale, label, cell_size=80):
    """输出端口 VOUT - 空心圆点"""
    r = 8 * scale
    # 空心圆点
    canvas.create_oval(x-r, y-r, x+r, y+r, outline=color, fill="white", width=2*scale)
    
    # 标签
    if label:
        canvas.create_text(x, y-r-15, text=label, fill=color, font=("Arial", 9))
    
    return {'vout': (x, y)}
