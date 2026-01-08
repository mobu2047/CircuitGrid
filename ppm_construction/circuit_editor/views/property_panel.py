"""
属性面板 - 编辑选中元件的属性
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple, Callable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.grid_model import GridModel
from registry.component_registry import (
    get_all_edge_components, 
    get_all_node_components,
    get_edge_component,
    get_node_component,
    ComponentConfig
)


class PropertyPanel(ttk.Frame):
    """
    属性面板
    
    显示和编辑选中边/节点的属性
    """
    
    UNITS = ["", "k", "m", "μ", "n", "p"]
    ORIENTATIONS = ["Down", "Right", "Up", "Left"]
    
    def __init__(self, parent, model: GridModel, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.model = model
        self.current_edge: Optional[Tuple[str, int, int]] = None
        self.current_node: Optional[Tuple[int, int]] = None
        
        self._create_widgets()
        self._clear_panel()
    
    def _create_widgets(self):
        """创建控件"""
        # 标题
        self.title_label = ttk.Label(self, text="Properties", 
                                     font=("Arial", 12, "bold"))
        self.title_label.pack(pady=(10, 5))
        
        # 位置信息
        self.pos_label = ttk.Label(self, text="No selection")
        self.pos_label.pack(pady=5)
        
        ttk.Separator(self, orient='horizontal').pack(fill='x', pady=10)
        
        # === 边属性区域 ===
        self.edge_frame = ttk.LabelFrame(self, text="Edge Component")
        self.edge_frame.pack(fill='x', padx=10, pady=5)
        
        # 元件类型
        ttk.Label(self.edge_frame, text="Type:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.edge_type_var = tk.StringVar()
        self.edge_type_combo = ttk.Combobox(self.edge_frame, textvariable=self.edge_type_var,
                                            state='readonly', width=15)
        self.edge_type_combo['values'] = [c.display_name for c in get_all_edge_components()]
        self.edge_type_combo.grid(row=0, column=1, padx=5, pady=2)
        self.edge_type_combo.bind('<<ComboboxSelected>>', self._on_edge_type_changed)
        
        # 标签编号
        ttk.Label(self.edge_frame, text="Label:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.edge_label_var = tk.StringVar(value="0")
        self.edge_label_entry = ttk.Entry(self.edge_frame, textvariable=self.edge_label_var, width=8)
        self.edge_label_entry.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        self.edge_label_entry.bind('<FocusOut>', self._on_edge_label_changed)
        self.edge_label_entry.bind('<Return>', self._on_edge_label_changed)
        
        # 数值
        ttk.Label(self.edge_frame, text="Value:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        value_frame = ttk.Frame(self.edge_frame)
        value_frame.grid(row=2, column=1, sticky='w', padx=5, pady=2)
        
        self.edge_value_var = tk.StringVar(value="0")
        self.edge_value_entry = ttk.Entry(value_frame, textvariable=self.edge_value_var, width=6)
        self.edge_value_entry.pack(side='left')
        self.edge_value_entry.bind('<FocusOut>', self._on_edge_value_changed)
        self.edge_value_entry.bind('<Return>', self._on_edge_value_changed)
        
        self.edge_unit_var = tk.StringVar(value="")
        self.edge_unit_combo = ttk.Combobox(value_frame, textvariable=self.edge_unit_var,
                                            state='readonly', width=4)
        self.edge_unit_combo['values'] = self.UNITS
        self.edge_unit_combo.pack(side='left', padx=2)
        self.edge_unit_combo.bind('<<ComboboxSelected>>', self._on_edge_unit_changed)
        
        # 方向（用于电源、二极管等有方向的元件）
        ttk.Label(self.edge_frame, text="Direction:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.edge_direction_var = tk.StringVar(value="Forward")
        self.edge_direction_combo = ttk.Combobox(self.edge_frame, textvariable=self.edge_direction_var,
                                                 state='readonly', width=10)
        self.edge_direction_combo['values'] = ["Forward", "Reverse"]
        self.edge_direction_combo.grid(row=3, column=1, sticky='w', padx=5, pady=2)
        self.edge_direction_combo.bind('<<ComboboxSelected>>', self._on_edge_direction_changed)
        
        # 删除边按钮
        self.delete_edge_btn = ttk.Button(self.edge_frame, text="Delete Edge", 
                                          command=self._delete_edge)
        self.delete_edge_btn.grid(row=4, column=0, columnspan=2, pady=10)
        
        # === 节点属性区域 ===
        self.node_frame = ttk.LabelFrame(self, text="Node Component")
        self.node_frame.pack(fill='x', padx=10, pady=5)
        
        # 节点元件类型
        ttk.Label(self.node_frame, text="Type:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.node_type_var = tk.StringVar()
        self.node_type_combo = ttk.Combobox(self.node_frame, textvariable=self.node_type_var,
                                            state='readonly', width=15)
        self.node_type_combo['values'] = [c.display_name for c in get_all_node_components()]
        self.node_type_combo.grid(row=0, column=1, padx=5, pady=2)
        self.node_type_combo.bind('<<ComboboxSelected>>', self._on_node_type_changed)
        
        # 标签编号（类似边上元件）
        ttk.Label(self.node_frame, text="Label:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.node_label_var = tk.StringVar(value="0")
        self.node_label_entry = ttk.Entry(self.node_frame, textvariable=self.node_label_var, width=8)
        self.node_label_entry.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        self.node_label_entry.bind('<FocusOut>', self._on_node_label_changed)
        self.node_label_entry.bind('<Return>', self._on_node_label_changed)
        
        # 朝向
        ttk.Label(self.node_frame, text="Orientation:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.node_orient_var = tk.StringVar(value="Right")
        self.node_orient_combo = ttk.Combobox(self.node_frame, textvariable=self.node_orient_var,
                                              state='readonly', width=10)
        self.node_orient_combo['values'] = self.ORIENTATIONS
        self.node_orient_combo.grid(row=2, column=1, sticky='w', padx=5, pady=2)
        self.node_orient_combo.bind('<<ComboboxSelected>>', self._on_node_orient_changed)
        
        # 交叉点标记
        self.junction_var = tk.BooleanVar(value=False)
        self.junction_check = ttk.Checkbutton(self.node_frame, text="Junction Marker",
                                              variable=self.junction_var,
                                              command=self._on_junction_changed)
        self.junction_check.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 删除节点元件按钮
        self.delete_node_btn = ttk.Button(self.node_frame, text="Delete Component", 
                                          command=self._delete_node_component)
        self.delete_node_btn.grid(row=4, column=0, columnspan=2, pady=10)
    
    def show_edge(self, direction: str, i: int, j: int):
        """显示边属性"""
        self.current_edge = (direction, i, j)
        self.current_node = None
        
        # 更新位置标签
        self.pos_label.config(text=f"Edge: {'H' if direction == 'h' else 'V'}({i}, {j})")
        
        # 获取数据
        if direction == 'h':
            data = self.model.get_hedge_data(i, j)
        else:
            data = self.model.get_vedge_data(i, j)
        
        if data:
            # 更新控件
            comp = get_edge_component(data.comp_type)
            if comp:
                self.edge_type_var.set(comp.display_name)
            self.edge_label_var.set(str(data.label))
            self.edge_value_var.set(str(data.value))
            self.edge_unit_combo.current(data.value_unit)
            # 方向：0=Forward, 1=Reverse
            self.edge_direction_combo.current(data.direction)
        
        # 显示边面板，隐藏节点面板
        self.edge_frame.pack(fill='x', padx=10, pady=5)
        self.node_frame.pack_forget()
    
    def show_node(self, i: int, j: int):
        """显示节点属性"""
        self.current_node = (i, j)
        self.current_edge = None
        
        # 更新位置标签
        self.pos_label.config(text=f"Node: ({i}, {j})")
        
        # 获取数据
        data = self.model.get_node_data(i, j)
        if data:
            comp = get_node_component(data.comp_type)
            if comp:
                self.node_type_var.set(comp.display_name)
            # 显示 label（类似边上元件）
            self.node_label_var.set(str(self.model.node_comp_label[i][j]))
            self.node_orient_combo.current(data.orientation)
        
        # 交叉点标记
        self.junction_var.set(bool(self.model.junction_marker[i][j]))
        
        # 显示节点面板，隐藏边面板
        self.node_frame.pack(fill='x', padx=10, pady=5)
        self.edge_frame.pack_forget()
    
    def _clear_panel(self):
        """清空面板"""
        self.current_edge = None
        self.current_node = None
        self.pos_label.config(text="No selection")
        self.edge_frame.pack_forget()
        self.node_frame.pack_forget()
    
    # ============================================================
    # 事件处理
    # ============================================================
    
    def _on_edge_type_changed(self, event=None):
        """边元件类型改变"""
        if not self.current_edge:
            return
        
        direction, i, j = self.current_edge
        type_name = self.edge_type_var.get()
        
        # 查找类型 ID
        for comp in get_all_edge_components():
            if comp.display_name == type_name:
                edge_direction = 0 if self.edge_direction_var.get() == "Forward" else 1
                if direction == 'h':
                    self.model.set_hedge_component(i, j, comp.type_id,
                                                   label=self.edge_label_var.get(),
                                                   value=int(self.edge_value_var.get() or 0),
                                                   value_unit=self.UNITS.index(self.edge_unit_var.get()),
                                                   direction=edge_direction)
                else:
                    self.model.set_vedge_component(i, j, comp.type_id,
                                                   label=self.edge_label_var.get(),
                                                   value=int(self.edge_value_var.get() or 0),
                                                   value_unit=self.UNITS.index(self.edge_unit_var.get()),
                                                   direction=edge_direction)
                break
    
    def _on_edge_label_changed(self, event=None):
        """边标签改变"""
        if not self.current_edge:
            return
        direction, i, j = self.current_edge
        label = self.edge_label_var.get()
        # 尝试转为数字，如果失败则保持字符串
        try:
             # 如果是纯数字字符串，转为int，保持兼容性? 
             # 用户说想要VD，所以字符串。
             # 但如果用户输入 "1"，最好存为 int 1 还是 str "1"?
             # LaTeX handle logic: if int, it uses `int(label)`. If str, it uses string.
             # Better to try convert to int if possible, else keep string.
             # Because existing logic might expect int for auto-increment logic or something?
             # But GridRules check `type_number`?
             # Let's check: if I store "1" (str), formatting `f"{label}"` works same as `f"{1}"`.
             # BUT `grid_rules.py` Line 231: `int(label_subscript)`. This will crash if I pass "1" (str)? No `int("1")` works.
             # `int("vd")` crashes.
             # So safely try valid int.
             if label.isdigit():
                 label = int(label)
        except:
             pass
        
        if direction == 'h':
            self.model.hcomp_label[i][j] = label
        else:
            self.model.vcomp_label[i][j] = label
        self.model.notify_update()
    
    def _on_edge_value_changed(self, event=None):
        """边数值改变"""
        if not self.current_edge:
            return
        direction, i, j = self.current_edge
        try:
            value = int(self.edge_value_var.get())
        except ValueError:
            value = 0
        
        if direction == 'h':
            self.model.hcomp_value[i][j] = value
        else:
            self.model.vcomp_value[i][j] = value
        self.model.notify_update()
    
    def _on_edge_unit_changed(self, event=None):
        """边单位改变"""
        if not self.current_edge:
            return
        direction, i, j = self.current_edge
        unit_idx = self.UNITS.index(self.edge_unit_var.get())
        
        if direction == 'h':
            self.model.hcomp_value_unit[i][j] = unit_idx
        else:
            self.model.vcomp_value_unit[i][j] = unit_idx
        self.model.notify_update()
    
    def _on_edge_direction_changed(self, event=None):
        """边方向改变"""
        if not self.current_edge:
            return
        direction, i, j = self.current_edge
        edge_direction = 0 if self.edge_direction_var.get() == "Forward" else 1
        
        if direction == 'h':
            self.model.hcomp_direction[i][j] = edge_direction
        else:
            self.model.vcomp_direction[i][j] = edge_direction
        self.model.notify_update()
    
    def _delete_edge(self):
        """删除边"""
        if not self.current_edge:
            return
        direction, i, j = self.current_edge
        if direction == 'h':
            self.model.toggle_hedge(i, j)
        else:
            self.model.toggle_vedge(i, j)
        self._clear_panel()
    
    def _on_node_type_changed(self, event=None):
        """节点元件类型改变"""
        if not self.current_node:
            return
        i, j = self.current_node
        type_name = self.node_type_var.get()
        
        for comp in get_all_node_components():
            if comp.display_name == type_name:
                label = self.node_label_var.get()
                if label.isdigit():
                    label = int(label)

                self.model.set_node_component(i, j, comp.type_id,
                                              label=label,
                                              orientation=self.ORIENTATIONS.index(self.node_orient_var.get()))
                break
    
    def _on_node_label_changed(self, event=None):
        """节点元件标签改变"""
        if not self.current_node:
            return
        i, j = self.current_node
        label = self.node_label_var.get()
        try:
             if label.isdigit():
                 label = int(label)
        except:
             pass
        self.model.node_comp_label[i][j] = label
        self.model.notify_update()
    
    def _on_node_orient_changed(self, event=None):
        """节点元件朝向改变"""
        if not self.current_node:
            return
        i, j = self.current_node
        orient = self.ORIENTATIONS.index(self.node_orient_var.get())
        self.model.node_comp_orientation[i][j] = orient
        self.model.notify_update()
    
    def _on_junction_changed(self):
        """交叉点标记改变"""
        if not self.current_node:
            return
        i, j = self.current_node
        self.model.junction_marker[i][j] = 1 if self.junction_var.get() else 0
        self.model.notify_update()
    
    def _delete_node_component(self):
        """删除节点元件"""
        if not self.current_node:
            return
        i, j = self.current_node
        self.model.set_node_component(i, j, 0)  # 设置为 NONE
        self._clear_panel()
