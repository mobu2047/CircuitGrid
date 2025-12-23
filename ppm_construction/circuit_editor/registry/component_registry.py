"""
元件注册表 - 可扩展的元件类型管理

使用方法：
    # 注册新元件类型
    @EdgeComponentRegistry.register("my_component")
    class MyComponent(EdgeComponentBase):
        type_id = 99
        display_name = "My Component"
        circuitikz_type = "mycomp"
        ...
"""
from abc import ABC, abstractmethod
from typing import Dict, Type, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ComponentConfig:
    """元件配置数据类"""
    type_id: int                    # 类型 ID（与 grid_rules.py 对应）
    display_name: str               # 显示名称
    short_name: str                 # 简短名称（用于画布显示）
    circuitikz_type: str            # CircuiTikZ 元件类型
    label_prefix: str               # 标签前缀（如 R, C, L）
    unit: str                       # 单位（如 Ω, F, H）
    color: str = "#000000"          # 画布显示颜色
    has_value: bool = True          # 是否有数值
    has_direction: bool = False     # 是否有方向（电源等）
    spice_prefix: str = ""          # SPICE 前缀


class ComponentRegistryBase(ABC):
    """元件注册表基类"""
    _registry: Dict[int, ComponentConfig] = {}
    _name_to_id: Dict[str, int] = {}
    
    @classmethod
    def register(cls, config: ComponentConfig) -> None:
        """注册元件"""
        cls._registry[config.type_id] = config
        cls._name_to_id[config.display_name] = config.type_id
    
    @classmethod
    def get(cls, type_id: int) -> Optional[ComponentConfig]:
        """根据 ID 获取元件配置"""
        return cls._registry.get(type_id)
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional[ComponentConfig]:
        """根据名称获取元件配置"""
        type_id = cls._name_to_id.get(name)
        return cls._registry.get(type_id) if type_id is not None else None
    
    @classmethod
    def get_all(cls) -> List[ComponentConfig]:
        """获取所有已注册元件"""
        return list(cls._registry.values())
    
    @classmethod
    def get_display_names(cls) -> List[str]:
        """获取所有元件显示名称（用于下拉菜单）"""
        return [c.display_name for c in cls._registry.values()]


class EdgeComponentRegistry(ComponentRegistryBase):
    """边上元件注册表（双端元件）"""
    _registry: Dict[int, ComponentConfig] = {}
    _name_to_id: Dict[str, int] = {}


class NodeComponentRegistry(ComponentRegistryBase):
    """节点元件注册表（多端元件）"""
    _registry: Dict[int, ComponentConfig] = {}
    _name_to_id: Dict[str, int] = {}


# ============================================================
# 注册默认元件类型
# ============================================================

def _register_default_components():
    """注册默认的边上元件"""
    edge_components = [
        ComponentConfig(
            type_id=0, display_name="Short", short_name="—",
            circuitikz_type="short", label_prefix="", unit="",
            color="#666666", has_value=False
        ),
        ComponentConfig(
            type_id=1, display_name="Voltage Source", short_name="V",
            circuitikz_type="V", label_prefix="U", unit="V",
            color="#FF6B6B", has_value=True, has_direction=True, spice_prefix="V"
        ),
        ComponentConfig(
            type_id=2, display_name="Current Source", short_name="I",
            circuitikz_type="I", label_prefix="I", unit="A",
            color="#4ECDC4", has_value=True, has_direction=True, spice_prefix="I"
        ),
        ComponentConfig(
            type_id=3, display_name="Resistor", short_name="R",
            circuitikz_type="generic", label_prefix="R", unit="Ω",
            color="#45B7D1", has_value=True, spice_prefix="R"
        ),
        ComponentConfig(
            type_id=4, display_name="Capacitor", short_name="C",
            circuitikz_type="C", label_prefix="C", unit="F",
            color="#96CEB4", has_value=True, spice_prefix="C"
        ),
        ComponentConfig(
            type_id=5, display_name="Inductor", short_name="L",
            circuitikz_type="L", label_prefix="L", unit="H",
            color="#FFEAA7", has_value=True, spice_prefix="L"
        ),
        ComponentConfig(
            type_id=6, display_name="Open", short_name="×",
            circuitikz_type="open", label_prefix="", unit="",
            color="#CCCCCC", has_value=False
        ),
    ]
    
    for comp in edge_components:
        EdgeComponentRegistry.register(comp)
    
    # 节点元件
    node_components = [
        ComponentConfig(
            type_id=0, display_name="None", short_name="",
            circuitikz_type="", label_prefix="", unit="",
            color="#FFFFFF", has_value=False
        ),
        ComponentConfig(
            type_id=1, display_name="NPN Transistor", short_name="NPN",
            circuitikz_type="npn", label_prefix="Q", unit="",
            color="#E17055", has_value=False, spice_prefix="Q"
        ),
        ComponentConfig(
            type_id=2, display_name="PNP Transistor", short_name="PNP",
            circuitikz_type="pnp", label_prefix="Q", unit="",
            color="#E17055", has_value=False, spice_prefix="Q"
        ),
        ComponentConfig(
            type_id=3, display_name="Diode", short_name="D",
            circuitikz_type="D", label_prefix="D", unit="",
            color="#FDCB6E", has_value=False, spice_prefix="D"
        ),
        ComponentConfig(
            type_id=4, display_name="Op-Amp", short_name="OA",
            circuitikz_type="op amp", label_prefix="U", unit="",
            color="#A29BFE", has_value=False, spice_prefix="U"
        ),
    ]
    
    for comp in node_components:
        NodeComponentRegistry.register(comp)


# 模块加载时自动注册默认元件
_register_default_components()


# ============================================================
# 便捷函数
# ============================================================

def get_edge_component(type_id: int) -> Optional[ComponentConfig]:
    """获取边上元件配置"""
    return EdgeComponentRegistry.get(type_id)

def get_node_component(type_id: int) -> Optional[ComponentConfig]:
    """获取节点元件配置"""
    return NodeComponentRegistry.get(type_id)

def get_all_edge_components() -> List[ComponentConfig]:
    """获取所有边上元件"""
    return EdgeComponentRegistry.get_all()

def get_all_node_components() -> List[ComponentConfig]:
    """获取所有节点元件"""
    return NodeComponentRegistry.get_all()
