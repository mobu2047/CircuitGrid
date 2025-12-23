"""
网格画布 - 显示和交互的核心区域

支持：
- 边和节点的选择
- 元件拖放
- 节点元件引脚连接
"""
import tkinter as tk
from typing import Optional, Tuple, Callable, Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.grid_model import GridModel
from registry.component_registry import get_edge_component, get_node_component
from views.component_renderer import ComponentRenderer


class GridCanvas(tk.Canvas):
    """
    网格画布
    
    显示 Grid 网格，处理鼠标交互
    """
    
    # 布局常量
    CELL_SIZE = 80
    NODE_RADIUS = 8
    EDGE_WIDTH = 3
    PADDING = 50
    PIN_RADIUS = 8  # 引脚圆点半径（增大以便点击）
    PIN_CLICK_RADIUS = 12  # 引脚点击检测半径（比显示半径大）
    
    # 颜色
    BG_COLOR = "#FAFAFA"
    GRID_COLOR = "#E8E8E8"
    NODE_COLOR = "#333333"
    EDGE_COLOR = "#666666"
    SELECT_COLOR = "#FF5722"
    JUNCTION_COLOR = "#000000"
    PIN_COLOR = "#2196F3"
    PIN_HIGHLIGHT = "#FF9800"
    DROP_HIGHLIGHT = "#4CAF50"
    
    def __init__(self, parent, model: GridModel, **kwargs):
        self.model = model
        
        width = (model.n - 1) * self.CELL_SIZE + 2 * self.PADDING
        height = (model.m - 1) * self.CELL_SIZE + 2 * self.PADDING
        
        super().__init__(parent, width=width, height=height,
                        bg=self.BG_COLOR, highlightthickness=0, **kwargs)
        
        # 选中状态
        self.selected_edge: Optional[Tuple[str, int, int]] = None
        self.selected_node: Optional[Tuple[int, int]] = None
        
        # 引脚连接状态
        self.pin_positions: Dict[Tuple[int, int], Dict[str, Tuple[float, float]]] = {}
        self.dragging_pin: Optional[Tuple[int, int, str]] = None  # (i, j, pin_name)
        self.pin_target: Optional[Tuple[int, int]] = None
        
        # 拖放状态
        self.drop_target: Optional[Tuple[str, int, int]] = None  # ('h'/'v', i, j) or None
        self.drop_component: Optional[Tuple[bool, int]] = None  # (is_edge, type_id)
        
        # 待放置元件（从元件库选择后，点击放置）
        self.pending_component: Optional[Tuple[bool, int]] = None  # (is_edge, type_id)
        self.on_component_placed: Optional[Callable] = None  # 放置完成回调
        
        # 回调函数
        self.on_edge_selected: Optional[Callable] = None
        self.on_node_selected: Optional[Callable] = None
        self.on_pin_connected: Optional[Callable] = None
        self.on_cancel: Optional[Callable] = None  # 取消操作回调
        
        # 绑定事件
        self.bind("<Button-1>", self._on_left_click)
        self.bind("<Button-3>", self._on_right_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Motion>", self._on_motion)
        
        # 监听模型变化
        self._observer_callback = self.redraw
        model.add_observer(self._observer_callback)
        
        self.redraw()
    
    def destroy(self):
        """销毁画布时移除 observer"""
        if hasattr(self, '_observer_callback'):
            self.model.remove_observer(self._observer_callback)
        super().destroy()
    
    def _grid_to_canvas(self, i: int, j: int) -> Tuple[float, float]:
        """Grid 坐标转画布坐标"""
        x = self.PADDING + j * self.CELL_SIZE
        y = self.PADDING + i * self.CELL_SIZE
        return x, y
    
    def _canvas_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """画布坐标转 Grid 坐标"""
        j = round((x - self.PADDING) / self.CELL_SIZE)
        i = round((y - self.PADDING) / self.CELL_SIZE)
        return i, j
    
    def _find_nearest_edge(self, x: float, y: float) -> Optional[Tuple[str, int, int]]:
        """找到最近的边（已存在的边）"""
        rel_x = x - self.PADDING
        rel_y = y - self.PADDING
        
        cell_x = rel_x / self.CELL_SIZE
        cell_y = rel_y / self.CELL_SIZE
        
        frac_x = cell_x - int(cell_x)
        frac_y = cell_y - int(cell_y)
        
        # 扩大检测范围，更容易选中边和元件
        COMPONENT_CLICK_TOLERANCE = 0.5  # 元件周围50%范围
        
        best_edge = None
        best_dist = float('inf')
        
        # 检查所有水平边
        for i in range(self.model.m):
            for j in range(self.model.n - 1):
                if self.model.has_hedge[i][j]:
                    # 边的中点
                    edge_x = (j + 0.5) * self.CELL_SIZE
                    edge_y = i * self.CELL_SIZE
                    
                    # 计算到边的距离
                    dist_x = abs(rel_x - edge_x)
                    dist_y = abs(rel_y - edge_y)
                    
                    # 如果在元件附近（考虑元件大小）
                    if dist_y < COMPONENT_CLICK_TOLERANCE * self.CELL_SIZE and dist_x < self.CELL_SIZE * 0.6:
                        dist = (dist_x**2 + dist_y**2)**0.5
                        if dist < best_dist:
                            best_dist = dist
                            best_edge = ('h', i, j)
        
        # 检查所有垂直边
        for i in range(self.model.m - 1):
            for j in range(self.model.n):
                if self.model.has_vedge[i][j]:
                    edge_x = j * self.CELL_SIZE
                    edge_y = (i + 0.5) * self.CELL_SIZE
                    
                    dist_x = abs(rel_x - edge_x)
                    dist_y = abs(rel_y - edge_y)
                    
                    if dist_x < COMPONENT_CLICK_TOLERANCE * self.CELL_SIZE and dist_y < self.CELL_SIZE * 0.6:
                        dist = (dist_x**2 + dist_y**2)**0.5
                        if dist < best_dist:
                            best_dist = dist
                            best_edge = ('v', i, j)
        
        # 如果找到边且距离合理
        if best_edge and best_dist < self.CELL_SIZE * 0.5:
            return best_edge
        
        return None
    
    def _find_nearest_node(self, x: float, y: float) -> Optional[Tuple[int, int]]:
        """找到最近的节点"""
        i, j = self._canvas_to_grid(x, y)
        node_x, node_y = self._grid_to_canvas(i, j)
        dist = ((x - node_x) ** 2 + (y - node_y) ** 2) ** 0.5
        
        if dist < self.NODE_RADIUS * 3 and 0 <= i < self.model.m and 0 <= j < self.model.n:
            return (i, j)
        return None
    
    def _find_pin_at(self, x: float, y: float) -> Optional[Tuple[int, int, str]]:
        """找到点击位置的引脚"""
        for (i, j), pins in self.pin_positions.items():
            for pin_name, (px, py) in pins.items():
                dist = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                if dist < self.PIN_CLICK_RADIUS:
                    return (i, j, pin_name)
        return None
    
    def _on_left_click(self, event):
        """左键点击"""
        x, y = event.x, event.y
        
        # 优先检查是否点击了引脚（引脚连线优先级最高）
        pin = self._find_pin_at(x, y)
        if pin:
            self.dragging_pin = pin
            self.pending_component = None  # 取消待放置元件
            return
        
        # 如果有待放置的元件，执行放置
        if self.pending_component:
            is_edge, type_id = self.pending_component
            if is_edge:
                # 边元件：放到最近的边位置
                target = self._find_nearest_edge_position(x, y)
                if target:
                    direction, i, j = target
                    if direction == 'h':
                        self.model.set_hedge_component(i, j, type_id)
                    else:
                        self.model.set_vedge_component(i, j, type_id)
                    if self.on_component_placed:
                        self.on_component_placed(is_edge, type_id, target)
            else:
                # 节点元件：放到最近的节点
                node = self._find_nearest_node_position(x, y)
                if node:
                    i, j = node
                    self.model.set_node_component(i, j, type_id)
                    if self.on_component_placed:
                        self.on_component_placed(is_edge, type_id, ('n', i, j))
            # 不清除 pending_component，允许连续放置
            return
        
        # 检测节点
        node = self._find_nearest_node(x, y)
        if node:
            self.selected_node = node
            self.selected_edge = None
            if self.on_node_selected:
                self.on_node_selected(*node)
            self.redraw()
            return
        
        # 检测边（_find_nearest_edge 只返回已存在的边）
        edge = self._find_nearest_edge(x, y)
        if edge:
            self.selected_edge = edge
            self.selected_node = None
            if self.on_edge_selected:
                self.on_edge_selected(*edge)
            self.redraw()
    
    def _on_right_click(self, event):
        """右键点击：取消放置模式 / 切换边/交叉点"""
        # 优先处理：取消待放置元件
        if self.pending_component is not None:
            self.pending_component = None
            self.config(cursor="")
            self.redraw()
            # 通知主窗口更新状态栏
            if self.on_cancel:
                self.on_cancel()
            return
        
        x, y = event.x, event.y
        
        node = self._find_nearest_node(x, y)
        if node:
            self.model.toggle_junction(*node)
            return
        
        edge = self._find_nearest_edge(x, y)
        if edge:
            direction, i, j = edge
            if direction == 'h':
                self.model.toggle_hedge(i, j)
            else:
                self.model.toggle_vedge(i, j)
    
    def _on_drag(self, event):
        """拖动事件"""
        x, y = event.x, event.y
        
        # 如果正在拖动引脚
        if self.dragging_pin:
            # 删除旧的拖拽线（通过标签）
            self.delete("pin_drag_line")
            self.delete("pin_target_highlight")
            
            # 更新目标节点
            self.pin_target = self._find_nearest_node(x, y)
            
            # 绘制新的拖拽线
            i, j, pin_name = self.dragging_pin
            if (i, j) in self.pin_positions and pin_name in self.pin_positions[(i, j)]:
                px, py = self.pin_positions[(i, j)][pin_name]
                
                if self.pin_target:
                    tx, ty = self._grid_to_canvas(*self.pin_target)
                    # 高亮目标节点
                    self.create_oval(tx - 12, ty - 12, tx + 12, ty + 12,
                                   outline=self.DROP_HIGHLIGHT, width=3,
                                   tags="pin_target_highlight")
                    # 连线到目标
                    self.create_line(px, py, tx, py, tx, ty,
                                   fill=self.PIN_HIGHLIGHT, width=2,
                                   tags="pin_drag_line")
                else:
                    # 连线到鼠标
                    self.create_line(px, py, x, py, x, y,
                                   fill=self.PIN_HIGHLIGHT, width=2, dash=(4, 2),
                                   tags="pin_drag_line")
            return
        
        # 如果有拖放的元件，更新预览位置
        if self.drop_component:
            is_edge, type_id = self.drop_component
            if is_edge:
                # 边元件：找最近的边位置
                self.drop_target = self._find_nearest_edge_position(x, y)
            else:
                # 节点元件：找最近的节点位置
                node = self._find_nearest_node_position(x, y)
                self.drop_target = ('n', node[0], node[1]) if node else None
            self.redraw()
    
    def _find_nearest_edge_position(self, x: float, y: float) -> Optional[Tuple[str, int, int]]:
        """找到最近的边位置（用于拖放，无论边是否存在）"""
        rel_x = x - self.PADDING
        rel_y = y - self.PADDING
        
        best_dist = float('inf')
        best_edge = None
        
        # 检查所有水平边位置
        for i in range(self.model.m):
            for j in range(self.model.n - 1):
                # 边的中点
                mx = (j + 0.5) * self.CELL_SIZE
                my = i * self.CELL_SIZE
                dist = ((rel_x - mx) ** 2 + (rel_y - my) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_edge = ('h', i, j)
        
        # 检查所有垂直边位置
        for i in range(self.model.m - 1):
            for j in range(self.model.n):
                mx = j * self.CELL_SIZE
                my = (i + 0.5) * self.CELL_SIZE
                dist = ((rel_x - mx) ** 2 + (rel_y - my) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_edge = ('v', i, j)
        
        return best_edge if best_dist < self.CELL_SIZE else None
    
    def _find_nearest_node_position(self, x: float, y: float) -> Optional[Tuple[int, int]]:
        """找到最近的节点位置（用于拖放）"""
        i, j = self._canvas_to_grid(x, y)
        if 0 <= i < self.model.m and 0 <= j < self.model.n:
            return (i, j)
        return None
    
    def _on_release(self, event):
        """释放鼠标"""
        x, y = event.x, event.y
        
        # 完成引脚连接
        if self.dragging_pin:
            if self.pin_target:
                i, j, pin_name = self.dragging_pin
                ti, tj = self.pin_target
                
                # 更新连接
                connections = self.model.node_comp_connections[i][j] or {}
                target_x = self.model.horizontal_dis[tj]
                target_y = self.model.vertical_dis[ti]
                connections[pin_name] = (target_x, target_y)
                self.model.node_comp_connections[i][j] = connections
                
                if self.on_pin_connected:
                    self.on_pin_connected(i, j, pin_name, ti, tj)
                
                self.model._notify_observers()
            
            # 清除拖拽线
            self.delete("pin_drag_line")
            self.delete("pin_target_highlight")
        
        # 完成元件拖放
        if self.drop_component and self.drop_target:
            is_edge, type_id = self.drop_component
            if is_edge and self.drop_target[0] in ('h', 'v'):
                direction, i, j = self.drop_target
                if direction == 'h':
                    self.model.set_hedge_component(i, j, type_id)
                else:
                    self.model.set_vedge_component(i, j, type_id)
            elif not is_edge and self.drop_target[0] == 'n':
                _, i, j = self.drop_target
                self.model.set_node_component(i, j, type_id)
        
        # 清除状态
        self.dragging_pin = None
        self.pin_target = None
        self.drop_target = None
        self.drop_component = None
        self.redraw()
    
    def _on_motion(self, event):
        """鼠标移动（用于高亮预览）"""
        pass  # 可以添加悬停高亮效果
    
    def start_drop(self, is_edge: bool, type_id: int):
        """开始拖放元件（从元件库调用）"""
        self.drop_component = (is_edge, type_id)
    
    def cancel_drop(self):
        """取消拖放"""
        self.drop_component = None
        self.drop_target = None
        self.redraw()
    
    # ============================================================
    # 绘制方法
    # ============================================================
    
    def redraw(self):
        """重绘画布"""
        # 保存拖拽引脚状态
        dragging_pin_saved = self.dragging_pin
        
        self.delete("all")
        self.pin_positions.clear()
        
        self._draw_grid_lines()
        self._draw_edges()
        self._draw_node_components()
        self._draw_nodes()
        self._draw_selection()
        self._draw_drop_preview()
        
        # 如果正在拖拽引脚，恢复状态（但拖拽线会在 _on_drag 中重新绘制）
        if dragging_pin_saved:
            self.dragging_pin = dragging_pin_saved
    
    def _draw_grid_lines(self):
        """绘制网格参考线"""
        for i in range(self.model.m):
            for j in range(self.model.n):
                x, y = self._grid_to_canvas(i, j)
                if j < self.model.n - 1:
                    x2, _ = self._grid_to_canvas(i, j + 1)
                    self.create_line(x, y, x2, y, fill=self.GRID_COLOR,
                                   width=1, dash=(2, 4))
                if i < self.model.m - 1:
                    _, y2 = self._grid_to_canvas(i + 1, j)
                    self.create_line(x, y, x, y2, fill=self.GRID_COLOR,
                                   width=1, dash=(2, 4))
    
    def _draw_edges(self):
        """绘制所有边"""
        for i in range(self.model.m):
            for j in range(self.model.n - 1):
                if self.model.has_hedge[i][j]:
                    self._draw_single_edge('h', i, j)
        
        for i in range(self.model.m - 1):
            for j in range(self.model.n):
                if self.model.has_vedge[i][j]:
                    self._draw_single_edge('v', i, j)
    
    def _draw_single_edge(self, direction: str, i: int, j: int):
        """绘制单条边（使用 ComponentRenderer）"""
        if direction == 'h':
            x1, y1 = self._grid_to_canvas(i, j)
            x2, y2 = self._grid_to_canvas(i, j + 1)
            comp_type = self.model.hcomp_type[i][j]
            label = self.model.hcomp_label[i][j]
            value = self.model.hcomp_value[i][j]
            value_unit = self.model.hcomp_value_unit[i][j]
            comp_direction = self.model.hcomp_direction[i][j]
        else:
            x1, y1 = self._grid_to_canvas(i, j)
            x2, y2 = self._grid_to_canvas(i + 1, j)
            comp_type = self.model.vcomp_type[i][j]
            label = self.model.vcomp_label[i][j]
            value = self.model.vcomp_value[i][j]
            value_unit = self.model.vcomp_value_unit[i][j]
            comp_direction = self.model.vcomp_direction[i][j]
        
        comp_config = get_edge_component(int(comp_type))
        color = comp_config.color if comp_config else self.EDGE_COLOR
        
        # 构建标签文本：包含标签、数值和单位
        label_text = ""
        if comp_config:
            # 单位前缀映射
            unit_prefixes = ["", "k", "m", "μ", "n", "p"]
            unit_prefix = unit_prefixes[value_unit] if value_unit < len(unit_prefixes) else ""
            
            # 构建完整标签
            parts = []
            if label:
                parts.append(f"{comp_config.label_prefix}{label}")
            if value > 0:
                value_str = f"{value}{unit_prefix}" if unit_prefix else str(value)
                if comp_config.unit:
                    parts.append(f"{value_str}{comp_config.unit}")
                else:
                    parts.append(value_str)
            
            label_text = " ".join(parts)
        
        ComponentRenderer.draw_edge_component(
            self, int(comp_type), x1, y1, x2, y2,
            color=color, scale=1.0, label=label_text, direction=int(comp_direction)
        )
    
    def _draw_node_components(self):
        """绘制节点元件"""
        for i in range(self.model.m):
            for j in range(self.model.n):
                node_type = self.model.node_comp_type[i][j]
                if node_type != 0:
                    x, y = self._grid_to_canvas(i, j)
                    orientation = self.model.node_comp_orientation[i][j]
                    label = self.model.node_comp_label[i][j]
                    
                    comp_config = get_node_component(int(node_type))
                    color = comp_config.color if comp_config else "#333"
                    label_text = f"{comp_config.label_prefix}{label}" if comp_config else ""
                    
                    # 绘制并获取引脚位置（传入 cell_size 使引脚对齐到相邻节点）
                    pins = ComponentRenderer.draw_node_component(
                        self, int(node_type), x, y, int(orientation),
                        color=color, scale=1.0, label=label_text,
                        cell_size=self.CELL_SIZE
                    )
                    
                    if pins:
                        self.pin_positions[(i, j)] = pins
                        self._draw_pins(i, j, pins)
                        self._draw_pin_connections(i, j, pins)
    
    def _draw_pins(self, i: int, j: int, pins: Dict[str, Tuple[float, float]]):
        """绘制引脚圆点（可拖动）"""
        for pin_name, (px, py) in pins.items():
            # 判断是否高亮
            is_dragging = (self.dragging_pin == (i, j, pin_name))
            color = self.PIN_HIGHLIGHT if is_dragging else self.PIN_COLOR
            
            r = self.PIN_RADIUS
            # 绘制引脚圆点（增大以便点击）
            self.create_oval(px - r, py - r, px + r, py + r,
                           fill=color, outline='white', width=2,
                           tags=f"pin_{i}_{j}_{pin_name}")
            
            # 绘制引脚名称标签（调试用，可选）
            # self.create_text(px + r + 5, py, text=pin_name[:1], 
            #                 fill=color, font=("Arial", 7), anchor='w')
    
    def _draw_pin_connections(self, i: int, j: int, pins: Dict[str, Tuple[float, float]]):
        """绘制引脚到目标节点的连线"""
        connections = self.model.node_comp_connections[i][j]
        if not connections:
            return
        
        for pin_name, (px, py) in pins.items():
            if pin_name in connections:
                target_coord = connections[pin_name]
                # 查找目标节点位置
                for ti in range(self.model.m):
                    for tj in range(self.model.n):
                        if (abs(self.model.horizontal_dis[tj] - target_coord[0]) < 0.1 and
                            abs(self.model.vertical_dis[ti] - target_coord[1]) < 0.1):
                            tx, ty = self._grid_to_canvas(ti, tj)
                            # 绘制正交连线
                            self.create_line(px, py, tx, py, tx, ty,
                                           fill='#999', width=1.5, dash=(3, 2))
                            break
    
    def _draw_pin_drag_line(self, x: float, y: float):
        """绘制引脚拖动时的连线"""
        if self.dragging_pin:
            i, j, pin_name = self.dragging_pin
            if (i, j) in self.pin_positions and pin_name in self.pin_positions[(i, j)]:
                px, py = self.pin_positions[(i, j)][pin_name]
                
                # 高亮目标节点
                if self.pin_target:
                    tx, ty = self._grid_to_canvas(*self.pin_target)
                    self.create_oval(tx - 12, ty - 12, tx + 12, ty + 12,
                                   outline=self.DROP_HIGHLIGHT, width=3)
                    # 连线到目标
                    self.create_line(px, py, tx, py, tx, ty,
                                   fill=self.PIN_HIGHLIGHT, width=2)
                else:
                    # 连线到鼠标
                    self.create_line(px, py, x, py, x, y,
                                   fill=self.PIN_HIGHLIGHT, width=2, dash=(4, 2))
    
    def _draw_nodes(self):
        """绘制所有节点"""
        for i in range(self.model.m):
            for j in range(self.model.n):
                # 跳过有节点元件的位置
                if self.model.node_comp_type[i][j] != 0:
                    continue
                
                x, y = self._grid_to_canvas(i, j)
                
                if self.model.junction_marker[i][j]:
                    r = self.NODE_RADIUS
                    self.create_oval(x - r, y - r, x + r, y + r,
                                   fill=self.JUNCTION_COLOR, outline="")
                else:
                    r = self.NODE_RADIUS - 2
                    self.create_oval(x - r, y - r, x + r, y + r,
                                   fill="white", outline=self.NODE_COLOR, width=2)
    
    def _draw_selection(self):
        """绘制选中高亮"""
        if self.selected_edge:
            direction, i, j = self.selected_edge
            if direction == 'h':
                x1, y1 = self._grid_to_canvas(i, j)
                x2, y2 = self._grid_to_canvas(i, j + 1)
            else:
                x1, y1 = self._grid_to_canvas(i, j)
                x2, y2 = self._grid_to_canvas(i + 1, j)
            
            pad = 10
            self.create_rectangle(
                min(x1, x2) - pad, min(y1, y2) - pad,
                max(x1, x2) + pad, max(y1, y2) + pad,
                outline=self.SELECT_COLOR, width=2, dash=(4, 2)
            )
        
        if self.selected_node:
            i, j = self.selected_node
            x, y = self._grid_to_canvas(i, j)
            r = self.NODE_RADIUS + 8
            self.create_oval(x - r, y - r, x + r, y + r,
                           outline=self.SELECT_COLOR, width=2, dash=(4, 2))
    
    def _draw_drop_preview(self):
        """绘制拖放预览"""
        if self.drop_target and self.drop_component:
            is_edge, type_id = self.drop_component
            
            if self.drop_target[0] in ('h', 'v'):
                direction, i, j = self.drop_target
                if direction == 'h':
                    x1, y1 = self._grid_to_canvas(i, j)
                    x2, y2 = self._grid_to_canvas(i, j + 1)
                else:
                    x1, y1 = self._grid_to_canvas(i, j)
                    x2, y2 = self._grid_to_canvas(i + 1, j)
                
                # 高亮边位置
                self.create_line(x1, y1, x2, y2, fill=self.DROP_HIGHLIGHT,
                               width=4, dash=(6, 3))
            
            elif self.drop_target[0] == 'n':
                _, i, j = self.drop_target
                x, y = self._grid_to_canvas(i, j)
                self.create_oval(x - 20, y - 20, x + 20, y + 20,
                               outline=self.DROP_HIGHLIGHT, width=3, dash=(4, 2))
    
    def update_size(self):
        """更新画布大小"""
        width = (self.model.n - 1) * self.CELL_SIZE + 2 * self.PADDING
        height = (self.model.m - 1) * self.CELL_SIZE + 2 * self.PADDING
        self.config(width=width, height=height)
        self.redraw()
