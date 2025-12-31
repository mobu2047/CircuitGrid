"""
Grid 数据模型 - 管理电路网格数据

与 grid_rules.py 中的 Circuit 类对接
"""
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import sys
import os

# 添加父目录以导入 grid_rules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@dataclass
class EdgeData:
    """边数据"""
    exists: bool = False
    comp_type: int = 0
    label: int = 0
    value: int = 0
    value_unit: int = 0
    direction: int = 0


@dataclass
class NodeData:
    """节点元件数据"""
    comp_type: int = 0
    label: int = 0
    orientation: int = 1  # 0=up, 1=right, 2=down, 3=left
    connections: Optional[Dict] = None


class GridModel:
    """
    Grid 数据模型
    
    管理 m x n 网格的所有数据，包括：
    - 水平边 (m, n-1)
    - 垂直边 (m-1, n)
    - 节点元件 (m, n)
    - 交叉点标记 (m, n)
    """
    
    def __init__(self, m: int = 4, n: int = 4):
        self.m = m
        self.n = n
        self._init_arrays()
        self._observers = []  # 观察者列表，用于通知视图更新
    
    def _init_arrays(self):
        """初始化所有数组"""
        m, n = self.m, self.n
        
        # 水平边 (m, n-1)
        self.has_hedge = np.zeros((m, n-1), dtype=int)
        self.hcomp_type = np.zeros((m, n-1), dtype=int)
        self.hcomp_label = np.zeros((m, n-1), dtype=int)
        self.hcomp_value = np.zeros((m, n-1), dtype=int)
        self.hcomp_value_unit = np.zeros((m, n-1), dtype=int)
        self.hcomp_direction = np.zeros((m, n-1), dtype=int)
        
        # 垂直边 (m-1, n)
        self.has_vedge = np.zeros((m-1, n), dtype=int)
        self.vcomp_type = np.zeros((m-1, n), dtype=int)
        self.vcomp_label = np.zeros((m-1, n), dtype=int)
        self.vcomp_value = np.zeros((m-1, n), dtype=int)
        self.vcomp_value_unit = np.zeros((m-1, n), dtype=int)
        self.vcomp_direction = np.zeros((m-1, n), dtype=int)
        
        # 节点元件 (m, n)
        self.node_comp_type = np.zeros((m, n), dtype=int)
        self.node_comp_label = np.zeros((m, n), dtype=int)
        self.node_comp_orientation = np.ones((m, n), dtype=int)  # 默认朝右
        self.node_comp_connections = np.empty((m, n), dtype=object)
        for i in range(m):
            for j in range(n):
                self.node_comp_connections[i][j] = None
        
        # 交叉点标记 (m, n)
        self.junction_marker = np.zeros((m, n), dtype=int)
        
        # 坐标距离（用于渲染）
        self.horizontal_dis = np.array([i * 3.0 for i in range(n)])
        self.vertical_dis = np.array([(m - 1 - i) * 3.0 for i in range(m)])
    
    # ============================================================
    # 边操作
    # ============================================================
    
    def toggle_hedge(self, i: int, j: int) -> bool:
        """切换水平边存在状态"""
        if 0 <= i < self.m and 0 <= j < self.n - 1:
            self.has_hedge[i][j] = 1 - self.has_hedge[i][j]
            if self.has_hedge[i][j] == 0:
                # 边被删除时，清除元件数据
                self.hcomp_type[i][j] = 0
                self.hcomp_label[i][j] = 0
                self.hcomp_value[i][j] = 0
            self._notify_observers()
            return True
        return False
    
    def toggle_vedge(self, i: int, j: int) -> bool:
        """切换垂直边存在状态"""
        if 0 <= i < self.m - 1 and 0 <= j < self.n:
            self.has_vedge[i][j] = 1 - self.has_vedge[i][j]
            if self.has_vedge[i][j] == 0:
                self.vcomp_type[i][j] = 0
                self.vcomp_label[i][j] = 0
                self.vcomp_value[i][j] = 0
            self._notify_observers()
            return True
        return False
    
    def set_hedge_component(self, i: int, j: int, comp_type: int, 
                           label: int = 0, value: int = 0, 
                           value_unit: int = 0, direction: int = 0):
        """设置水平边元件"""
        print(f"[DEBUG] set_hedge_component({i}, {j}, type={comp_type})")
        if 0 <= i < self.m and 0 <= j < self.n - 1:
            self.has_hedge[i][j] = 1
            self.hcomp_type[i][j] = comp_type
            self.hcomp_label[i][j] = label
            self.hcomp_value[i][j] = value
            self.hcomp_value_unit[i][j] = value_unit
            self.hcomp_direction[i][j] = direction
            print(f"[DEBUG] After set: hcomp_type[{i}][{j}] = {self.hcomp_type[i][j]}")
            self._notify_observers()
    
    def set_vedge_component(self, i: int, j: int, comp_type: int,
                           label: int = 0, value: int = 0,
                           value_unit: int = 0, direction: int = 0):
        """设置垂直边元件"""
        print(f"[DEBUG] set_vedge_component({i}, {j}, type={comp_type})")
        if 0 <= i < self.m - 1 and 0 <= j < self.n:
            self.has_vedge[i][j] = 1
            self.vcomp_type[i][j] = comp_type
            self.vcomp_label[i][j] = label
            self.vcomp_value[i][j] = value
            self.vcomp_value_unit[i][j] = value_unit
            self.vcomp_direction[i][j] = direction
            print(f"[DEBUG] After set: vcomp_type[{i}][{j}] = {self.vcomp_type[i][j]}")
            self._notify_observers()
    
    def get_hedge_data(self, i: int, j: int) -> Optional[EdgeData]:
        """获取水平边数据"""
        if 0 <= i < self.m and 0 <= j < self.n - 1:
            return EdgeData(
                exists=bool(self.has_hedge[i][j]),
                comp_type=int(self.hcomp_type[i][j]),
                label=int(self.hcomp_label[i][j]),
                value=int(self.hcomp_value[i][j]),
                value_unit=int(self.hcomp_value_unit[i][j]),
                direction=int(self.hcomp_direction[i][j])
            )
        return None
    
    def get_vedge_data(self, i: int, j: int) -> Optional[EdgeData]:
        """获取垂直边数据"""
        if 0 <= i < self.m - 1 and 0 <= j < self.n:
            return EdgeData(
                exists=bool(self.has_vedge[i][j]),
                comp_type=int(self.vcomp_type[i][j]),
                label=int(self.vcomp_label[i][j]),
                value=int(self.vcomp_value[i][j]),
                value_unit=int(self.vcomp_value_unit[i][j]),
                direction=int(self.vcomp_direction[i][j])
            )
        return None
    
    # ============================================================
    # 节点元件操作
    # ============================================================
    
    def set_node_component(self, i: int, j: int, comp_type: int,
                          label: int = 0, orientation: int = 1,
                          connections: Optional[Dict] = None):
        """
        设置节点元件
        
        对于三极管等多引脚元件，会自动设置引脚连接和短路边
        orientation: 0=up, 1=right, 2=down, 3=left (基极指向的方向)
        """
        if 0 <= i < self.m and 0 <= j < self.n:
            self.node_comp_type[i][j] = comp_type
            self.node_comp_label[i][j] = label
            self.node_comp_orientation[i][j] = orientation
            
            # 取消自动连线：不再自动设置引脚连接，由用户手动连线
            # if comp_type in [1, 2]:  # NPN=1, PNP=2
            #     connections = self._auto_connect_transistor(i, j, orientation)
            # elif comp_type == 5:  # MOSFET=5
            #     connections = self._auto_connect_mosfet(i, j, orientation)
            
            self.node_comp_connections[i][j] = connections  # 保持为 None 或用户手动设置的 connections
            self._notify_observers()
    
    def _auto_connect_transistor(self, i: int, j: int, orientation: int) -> Dict:
        """
        根据三极管朝向自动设置引脚连接（不创建短路边，由用户手动连线）
        
        orientation: 基极指向的方向
        - 0=up: B→上, C→左, E→右
        - 1=right: B→右, C→上, E→下
        - 2=down: B→下, C→右, E→左
        - 3=left: B→左, C→下, E→上
        
        返回: connections 字典 {'base': (x,y), 'collector': (x,y), 'emitter': (x,y)}
        注意：返回的是物理坐标（与手动连接格式一致），不是网格坐标
        """
        connections = {}
        m, n = self.m, self.n
        
        # 根据朝向定义各引脚连接的相对位置
        # (di, dj) 表示相对于元件位置的偏移（网格坐标）
        if orientation == 0:  # up
            pin_dirs = {'base': (-1, 0), 'collector': (0, -1), 'emitter': (0, 1)}
        elif orientation == 1:  # right
            pin_dirs = {'base': (0, 1), 'collector': (-1, 0), 'emitter': (1, 0)}
        elif orientation == 2:  # down
            pin_dirs = {'base': (1, 0), 'collector': (0, 1), 'emitter': (0, -1)}
        else:  # left
            pin_dirs = {'base': (0, -1), 'collector': (1, 0), 'emitter': (-1, 0)}
        
        # 只设置引脚连接，不创建短路边（由用户手动连线）
        # 将网格坐标转换为物理坐标（与手动连接格式一致）
        for pin_name, (di, dj) in pin_dirs.items():
            ni, nj = i + di, j + dj
            # 检查目标节点是否在网格范围内
            if 0 <= ni < m and 0 <= nj < n:
                # 转换为物理坐标（与手动连接格式一致）
                phys_x = self.horizontal_dis[nj]
                phys_y = self.vertical_dis[ni]
                connections[pin_name] = (phys_x, phys_y)
        
        return connections
    
    def _auto_connect_mosfet(self, i: int, j: int, orientation: int) -> Dict:
        """
        根据MOSFET朝向自动设置引脚连接（不创建短路边，由用户手动连线）
        
        orientation: 栅极指向的方向
        - 0=up: G→上, D→左, S→右
        - 1=right: G→右, D→上, S→下
        - 2=down: G→下, D→右, S→左
        - 3=left: G→左, D→下, S→上
        
        返回: connections 字典 {'gate': (x,y), 'drain': (x,y), 'source': (x,y)}
        注意：返回的是物理坐标（与手动连接格式一致），不是网格坐标
        """
        connections = {}
        m, n = self.m, self.n
        
        # 根据朝向定义各引脚连接的相对位置
        # (di, dj) 表示相对于元件位置的偏移（网格坐标）
        if orientation == 0:  # up
            pin_dirs = {'gate': (-1, 0), 'drain': (0, -1), 'source': (0, 1)}
        elif orientation == 1:  # right
            pin_dirs = {'gate': (0, 1), 'drain': (-1, 0), 'source': (1, 0)}
        elif orientation == 2:  # down
            pin_dirs = {'gate': (1, 0), 'drain': (0, 1), 'source': (0, -1)}
        else:  # left
            pin_dirs = {'gate': (0, -1), 'drain': (1, 0), 'source': (-1, 0)}
        
        # 只设置引脚连接，不创建短路边（由用户手动连线）
        # 将网格坐标转换为物理坐标（与手动连接格式一致）
        for pin_name, (di, dj) in pin_dirs.items():
            ni, nj = i + di, j + dj
            # 检查目标节点是否在网格范围内
            if 0 <= ni < m and 0 <= nj < n:
                # 转换为物理坐标（与手动连接格式一致）
                phys_x = self.horizontal_dis[nj]
                phys_y = self.vertical_dis[ni]
                connections[pin_name] = (phys_x, phys_y)
        
        return connections
    
    def get_node_data(self, i: int, j: int) -> Optional[NodeData]:
        """获取节点元件数据"""
        if 0 <= i < self.m and 0 <= j < self.n:
            return NodeData(
                comp_type=int(self.node_comp_type[i][j]),
                label=int(self.node_comp_label[i][j]),
                orientation=int(self.node_comp_orientation[i][j]),
                connections=self.node_comp_connections[i][j]
            )
        return None
    
    # ============================================================
    # 交叉点操作
    # ============================================================
    
    def toggle_junction(self, i: int, j: int) -> bool:
        """切换交叉点标记"""
        if 0 <= i < self.m and 0 <= j < self.n:
            self.junction_marker[i][j] = 1 - self.junction_marker[i][j]
            self._notify_observers()
            return True
        return False
    
    # ============================================================
    # 观察者模式
    # ============================================================
    
    def add_observer(self, callback):
        """添加观察者"""
        self._observers.append(callback)
    
    def remove_observer(self, callback):
        """移除观察者"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self):
        """通知所有观察者"""
        for callback in self._observers:
            callback()
    
    # ============================================================
    # 序列化
    # ============================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 JSON 保存）"""
        return {
            "m": self.m,
            "n": self.n,
            "has_hedge": self.has_hedge.tolist(),
            "hcomp_type": self.hcomp_type.tolist(),
            "hcomp_label": self.hcomp_label.tolist(),
            "hcomp_value": self.hcomp_value.tolist(),
            "hcomp_value_unit": self.hcomp_value_unit.tolist(),
            "hcomp_direction": self.hcomp_direction.tolist(),
            "has_vedge": self.has_vedge.tolist(),
            "vcomp_type": self.vcomp_type.tolist(),
            "vcomp_label": self.vcomp_label.tolist(),
            "vcomp_value": self.vcomp_value.tolist(),
            "vcomp_value_unit": self.vcomp_value_unit.tolist(),
            "vcomp_direction": self.vcomp_direction.tolist(),
            "node_comp_type": self.node_comp_type.tolist(),
            "node_comp_label": self.node_comp_label.tolist(),
            "node_comp_orientation": self.node_comp_orientation.tolist(),
            "node_comp_connections": [[self.node_comp_connections[i][j] 
                                       for j in range(self.n)] 
                                      for i in range(self.m)],
            "junction_marker": self.junction_marker.tolist(),
            "horizontal_dis": self.horizontal_dis.tolist(),
            "vertical_dis": self.vertical_dis.tolist(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GridModel':
        """从字典创建模型"""
        model = cls(data["m"], data["n"])
        model.has_hedge = np.array(data["has_hedge"])
        model.hcomp_type = np.array(data["hcomp_type"])
        model.hcomp_label = np.array(data["hcomp_label"])
        model.hcomp_value = np.array(data["hcomp_value"])
        model.hcomp_value_unit = np.array(data["hcomp_value_unit"])
        model.hcomp_direction = np.array(data["hcomp_direction"])
        model.has_vedge = np.array(data["has_vedge"])
        model.vcomp_type = np.array(data["vcomp_type"])
        model.vcomp_label = np.array(data["vcomp_label"])
        model.vcomp_value = np.array(data["vcomp_value"])
        model.vcomp_value_unit = np.array(data["vcomp_value_unit"])
        model.vcomp_direction = np.array(data["vcomp_direction"])
        model.node_comp_type = np.array(data["node_comp_type"])
        model.node_comp_label = np.array(data["node_comp_label"])
        model.node_comp_orientation = np.array(data["node_comp_orientation"])
        for i in range(model.m):
            for j in range(model.n):
                model.node_comp_connections[i][j] = data["node_comp_connections"][i][j]
        model.junction_marker = np.array(data["junction_marker"])
        model.horizontal_dis = np.array(data["horizontal_dis"])
        model.vertical_dis = np.array(data["vertical_dis"])
        return model
    
    def save_json(self, filepath: str):
        """保存为 JSON 文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_json(cls, filepath: str) -> 'GridModel':
        """从 JSON 文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    # ============================================================
    # 与 Circuit 类对接
    # ============================================================
    
    def to_circuit(self):
        """转换为 grid_rules.Circuit 对象"""
        from data_syn.grid_rules import Circuit
        
        # 调试输出
        print("=" * 50)
        print("GridModel.to_circuit() - 数据检查")
        print(f"has_hedge:\n{self.has_hedge}")
        print(f"hcomp_type:\n{self.hcomp_type}")
        print(f"has_vedge:\n{self.has_vedge}")
        print(f"vcomp_type:\n{self.vcomp_type}")
        print("=" * 50)
        
        # 创建 Circuit 所需的额外数组（测量等）
        m, n = self.m, self.n
        
        circuit = Circuit(
            m=m, n=n,
            vertical_dis=self.vertical_dis,
            horizontal_dis=self.horizontal_dis,
            has_vedge=self.has_vedge,
            has_hedge=self.has_hedge,
            vcomp_type=self.vcomp_type,
            vcomp_label=self.vcomp_label,
            vcomp_value=self.vcomp_value,
            vcomp_value_unit=self.vcomp_value_unit,
            vcomp_direction=self.vcomp_direction,
            vcomp_measure=np.zeros((m-1, n), dtype=int),
            vcomp_measure_label=np.zeros((m-1, n), dtype=int),
            vcomp_measure_direction=np.zeros((m-1, n), dtype=int),
            vcomp_control_meas_label=np.zeros((m-1, n), dtype=int),
            hcomp_type=self.hcomp_type,
            hcomp_label=self.hcomp_label,
            hcomp_value=self.hcomp_value,
            hcomp_value_unit=self.hcomp_value_unit,
            hcomp_direction=self.hcomp_direction,
            hcomp_measure=np.zeros((m, n-1), dtype=int),
            hcomp_measure_label=np.zeros((m, n-1), dtype=int),
            hcomp_measure_direction=np.zeros((m, n-1), dtype=int),
            hcomp_control_meas_label=np.zeros((m, n-1), dtype=int),
            node_comp_type=self.node_comp_type,
            node_comp_label=self.node_comp_label,
            node_comp_orientation=self.node_comp_orientation,
            node_comp_connections=self.node_comp_connections,
            junction_marker=self.junction_marker,
            use_value_annotation=True,
            note="v10",
            id="editor_circuit",
        )
        return circuit
    
    def resize(self, new_m: int, new_n: int):
        """调整网格大小"""
        old_m, old_n = self.m, self.n
        old_data = self.to_dict()
        
        self.m, self.n = new_m, new_n
        self._init_arrays()
        
        # 复制旧数据
        min_m = min(old_m, new_m)
        min_n = min(old_n, new_n)
        
        for i in range(min_m):
            for j in range(min_n - 1):
                self.has_hedge[i][j] = old_data["has_hedge"][i][j]
                self.hcomp_type[i][j] = old_data["hcomp_type"][i][j]
                self.hcomp_label[i][j] = old_data["hcomp_label"][i][j]
                self.hcomp_value[i][j] = old_data["hcomp_value"][i][j]
        
        for i in range(min_m - 1):
            for j in range(min_n):
                self.has_vedge[i][j] = old_data["has_vedge"][i][j]
                self.vcomp_type[i][j] = old_data["vcomp_type"][i][j]
                self.vcomp_label[i][j] = old_data["vcomp_label"][i][j]
                self.vcomp_value[i][j] = old_data["vcomp_value"][i][j]
        
        self._notify_observers()
