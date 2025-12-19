"""
示例：生成一个包含三极管的简单电路

电路描述：
- 一个NPN三极管放大电路
- 基极通过电阻Rb连接到输入
- 集电极通过电阻Rc连接到电源
- 发射极接地
"""
import numpy as np
import sys
import os

# 添加父目录到路径以导入grid_rules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from grid_rules import (
    Circuit, 
    TYPE_SHORT, TYPE_VOLTAGE_SOURCE, TYPE_RESISTOR,
    NODE_TYPE_TRANSISTOR_NPN, NODE_TYPE_NONE,
    UNIT_MODE_1, UNIT_MODE_k
)

def generate_transistor_amplifier_example():
    """
    生成一个简单的NPN三极管共发射极放大电路（含电压源）
    
    简化电路拓扑 - 确保所有节点度数>=2：
    
        Vcc(12V)----Rc(1k)----[C]
            |                  |
            |                 Q1
            |                  |
           Vin(5V)---Rb(10k)--[B]
            |                  |
            |                  |
           GND----------------[E]
    
    Grid布局 (3x2) - 最小化设计：
    
           0         1
      0   Vcc ----  [C]   <- 集电极 (Rc连接)
           |         |
      1   Vin ----  [B]   <- 基极 (Rb连接) + Q1在此
           |         |
      2   GND ----  [E]   <- 发射极 (接地)
    
    所有节点通过边连接，形成完整回路
    """
    
    # 网格尺寸 3x2
    m, n = 4, 4
    
    # 节点坐标（y值从上到下递减，使Vcc在顶部，GND在底部）
    vertical_dis = np.array([9.0, 6.0, 3.0, 0.0])   # 3行
    horizontal_dis = np.array([9.0, 6.0, 3.0, 0.0])      # 2列
    
    # ========== 边的存在性 ==========
    # has_vedge 用来指示哪些垂直方向的边存在。在(m-1, n)的二维数组中，每个元素为1表示该位置存在一条垂直边（如电压源、短路等），0表示该位置没有垂直边。
    # 以本例为 4x4 网格，has_vedge 形状为 (3,4)：每一行表示起点行号，每一列为列号，值为1的位置表示网格中对应的上下节点之间连有“元件/路径”。
    # 例如：
    # 修改为4x4网格格式
    # has_vedge 形状 (m-1, n)，即 (3,4)
    # 每个元素 1 表示该位置有垂直边，0表示无
    has_vedge = np.array([
        [0, 0, 0, 1],  # (0,0)-(1,0): 有（Vcc），(0,1)-(1,1): 有（但此例可选填0/1，看拓扑设计）
        [1, 0, 0, 1],  # (1,0)-(2,0): 有（Vin-GND），(1,1)-(2,1): 可选
        [1, 1, 0, 1]   # (2,*)-(3,*): 暂无垂直边，全部0（最底行）
    ])
    # has_hedge 形状 (m, n-1)，即 (4,3)
    # 每一行对应一行Grid，每一列是该行的三个水平边：“1”表示有一条水平边，“0”表示无
    has_hedge = np.array([
        [0, 1, 1],  # (0,0)-(0,1): Rc，(0,1)-(0,2),(0,2)-(0,3): 无
        [0, 0, 0],  # (1,0)-(1,1): Rb，其余无
        [0, 0, 0],  # (2,0)-(2,1): 发射极与GND短路
        [1, 1, 1]  # (3,*) 行无水平边
    ])
    
    # ========== 边上元件类型 ==========
    # 下面对用于描述电路结构的各类数据结构进行解释说明：

    # 垂直边上元件类型数组 (vertical component type)：每个元素表示网格上对应垂直边的元件类型，例如电压源、无元件等。
    # 示例含义：vcomp_type[0,0]=TYPE_VOLTAGE_SOURCE，表示网格顶部(0,0)-(1,0)是一只电压源（如Vcc）。
    # 为了格式统一，不论每个边是否只有一个元件，所有元件类型都用二维数组表示
    # 这样便于未来扩展和矩阵操作，不会有任何影响，只是空的地方填0
    # 4x4 网络，垂直元件和水平元件类型均补全为适合4*4网格
    vcomp_type = np.array([
        [0, 0, 0, 0],  # (0,0)-(1,0)：Vcc电压源，其它无
        [TYPE_RESISTOR, 0, 0, TYPE_RESISTOR],                    # (1,*)-(2,*)
        [TYPE_VOLTAGE_SOURCE, TYPE_RESISTOR, TYPE_RESISTOR, 0],                    # (2,*)-(3,*)
    ])

    # 修改为 4x4 网格的 hcomp_type（行数为 m=4，列数为 n-1=3）
    hcomp_type = np.array([
        [0, 0, 0],     # (0,0)-(0,1)：Rc，其它无
        [0, 0, 0],     # (1,0)-(1,1)：Rb
        [0, 0, 0],     # (2,0)-(2,1)：发射极与GND短路
        [0, 0, 0]      # (3,*) 行如无水平边则填0，4*3矩阵
    ])

    # 垂直边元件标签数组（形状与vcomp_type一致，全部补全0）
    vcomp_label = np.array([
        [0, 0, 0, 0],   # Vcc编号为1，其它元件无编号
        [2, 0, 0, 4],   # Vin编号为2，其它无
        [1, 5, 3, 0],   # 其它全无编号
    ])

    # 水平边元件标签数组（形状与hcomp_type一致，全部补全0）
    hcomp_label = np.array([
        [0, 0, 0],   # Rc编号为1，其它无
        [0, 0, 0],   # Rb编号为2，其它无
        [0, 0, 0],   # 发射极短路无编号
        [0, 0, 0]    # 其余全无编号
    ])

    # 垂直边元件数值数组（同理补足0，每个为标量数值）
    vcomp_value = np.array([
        [0,   0, 0, 0],   # Vcc=12V
        [10,    0, 0, 18],   # Vin=5V
        [12,    50, 0, 0],   # 其它为0
    ])

    # 水平边元件数值数组（同理补足0）
    hcomp_value = np.array([
        [0,   0, 0],    # Rc=1k
        [0,  0, 0],    # Rb=10k
        [0,   0, 0],    # 发射极短路
        [0,   0, 0],    # 其余为0
    ])

    # 垂直边元件单位模式（同理补足0）
    vcomp_value_unit = np.array([
        [0, 0, 0, 0],    # Vcc为V
        [UNIT_MODE_k, 0, 0, UNIT_MODE_k],    # Vin为V
        [UNIT_MODE_1,UNIT_MODE_k, 0, 0],     # 其它无单位
    ])

    # 水平边元件单位模式（同理补足0）
    hcomp_value_unit = np.array([
        [0, 0, 0],   # Rc用kΩ
        [0, 0, 0],   # Rb用kΩ
        [0,          0, 0],    # 发射极短路无单位
        [0,          0, 0],    # 其余为0
    ])

    # 垂直边元件方向数组（已是二维，无需更改）
    vcomp_direction = np.zeros((m-1, n), dtype=int)
    # 水平边元件方向数组（已是二维，无需更改）
    hcomp_direction = np.zeros((m, n-1), dtype=int)

    # ======== 与测量相关的数据结构 ==========
    # 全部保持二维、补零，如上模式
    vcomp_measure = np.zeros((m-1, n), dtype=int)
    hcomp_measure = np.zeros((m, n-1), dtype=int)
    vcomp_measure_label = np.zeros((m-1, n), dtype=int)
    hcomp_measure_label = np.zeros((m, n-1), dtype=int)
    vcomp_measure_direction = np.zeros((m-1, n), dtype=int)
    hcomp_measure_direction = np.zeros((m, n-1), dtype=int)
    vcomp_control_meas_label = np.zeros((m-1, n), dtype=int)
    hcomp_control_meas_label = np.zeros((m, n-1), dtype=int)
    
    # # ========== 节点元件（三极管） ==========
    # # 三极管放在Grid外部，连接到右侧三个节点
    node_comp_type = np.zeros((m, n), dtype=int)
    node_comp_type[1][1] = NODE_TYPE_TRANSISTOR_NPN  # Q1在(1,1)
    
    node_comp_label = np.zeros((m, n), dtype=int)
    node_comp_label[1][1] = 1  # Q1
    
    node_comp_orientation = np.ones((m, n), dtype=int)
    node_comp_orientation[1][1] = 3
    
    node_comp_connections = np.empty((m, n), dtype=object)
    for i in range(m):
        for j in range(n):
            node_comp_connections[i][j] = None
    
    # Q1连接：
    # - Collector -> (0,1): Rc输出端 (5.0, 6.0)
    # - Base -> (1,1): Rb输出端 (5.0, 3.0)
    # - Emitter -> (2,1): GND (5.0, 0.0)
    node_comp_connections[1][1] = {
        'collector': (horizontal_dis[1], vertical_dis[2]),  # (5.0, 6.0)
        'base': (horizontal_dis[0], vertical_dis[1]),       # (5.0, 3.0)
        'emitter': (horizontal_dis[1], vertical_dis[0])     # (5.0, 0.0)
    }
    
    # 创建Circuit对象
    circuit = Circuit(
        m=m, n=n,
        vertical_dis=vertical_dis,
        horizontal_dis=horizontal_dis,
        has_vedge=has_vedge,
        has_hedge=has_hedge,
        vcomp_type=vcomp_type,
        hcomp_type=hcomp_type,
        vcomp_label=vcomp_label,
        hcomp_label=hcomp_label,
        vcomp_value=vcomp_value,
        hcomp_value=hcomp_value,
        vcomp_value_unit=vcomp_value_unit,
        hcomp_value_unit=hcomp_value_unit,
        vcomp_direction=vcomp_direction,
        hcomp_direction=hcomp_direction,
        vcomp_measure=vcomp_measure,
        hcomp_measure=hcomp_measure,
        vcomp_measure_label=vcomp_measure_label,
        hcomp_measure_label=hcomp_measure_label,
        vcomp_measure_direction=vcomp_measure_direction,
        hcomp_measure_direction=hcomp_measure_direction,
        vcomp_control_meas_label=vcomp_control_meas_label,
        hcomp_control_meas_label=hcomp_control_meas_label,
        node_comp_type=node_comp_type,
        node_comp_label=node_comp_label,
        node_comp_orientation=node_comp_orientation,
        node_comp_connections=node_comp_connections,
        use_value_annotation=True,
        note="v11",
        id="transistor_example_1"
    )
    
    import json

    # circuit对象本地JSON打印（纵向排列，主序为行）
    def convert_to_builtin_type(obj):
        """递归地将所有numpy类型转换为内建类型，以便JSON序列化。
        """
        import numpy as np
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        elif isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8,
                              np.int16, np.int32, np.int64, np.uint8, np.uint16,
                              np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            # 只toList，不再转置，保持纵向（按行主序）
            arr = obj.tolist()
            if isinstance(arr, list) and arr and isinstance(arr[0], list):
                # 二维及以上
                return [list(r) for r in arr]
            return arr
        elif isinstance(obj, dict):
            return {k: convert_to_builtin_type(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_to_builtin_type(x) for x in obj]
        elif isinstance(obj, set):
            return [convert_to_builtin_type(x) for x in obj]
        elif isinstance(obj, bool):
            return obj
        else:
            return obj

    def circuit_to_serializable_dict(circ):
        keys = [
            'm', 'n', 'vertical_dis', 'horizontal_dis',
            'has_vedge', 'has_hedge',
            'vcomp_type', 'hcomp_type', 'vcomp_label', 'hcomp_label',
            'vcomp_value', 'hcomp_value', 'vcomp_value_unit', 'hcomp_value_unit',
            'vcomp_direction', 'hcomp_direction',
            'vcomp_measure', 'hcomp_measure',
            'vcomp_measure_label', 'hcomp_measure_label',
            'vcomp_measure_direction', 'hcomp_measure_direction',
            'vcomp_control_meas_label', 'hcomp_control_meas_label',
            'node_comp_type', 'node_comp_label', 'node_comp_orientation',
            'node_comp_connections'
        ]
        # 保持纵向排列（不再做转置）
        result = {}
        for k in keys:
            val = getattr(circ, k, None)
            v = convert_to_builtin_type(val)
            # node_comp_connections特殊转换
            if k == 'node_comp_connections':
                arr_conn = []
                for row in val:
                    arr_conn.append([convert_to_builtin_type(v) if isinstance(v, dict) or v is None else str(v) for v in row])
                # 纵向排列，不转置
                result[k] = arr_conn
            else:
                result[k] = v

        if hasattr(circ, 'branches'):
            def fix_branch(b):
                if isinstance(b, dict):
                    return {k: convert_to_builtin_type(v) for k,v in b.items()}
                return convert_to_builtin_type(b)
            result['branches'] = [fix_branch(x) for x in circ.branches]
        return result

    # 生成JSON文本并保存本地（纵向排列，主序为行，便于技术进一步处理）
    circuit_json_path = 'circuit.json'
    with open(circuit_json_path, 'w', encoding='utf-8') as f:
        json.dump(
            circuit_to_serializable_dict(circuit), f, indent=2, ensure_ascii=False
        )
    print(f"[OK] Circuit info written to {circuit_json_path}")

    return circuit


def print_grid_structure():
    """打印Grid数据结构的完整说明"""
    print("="*80)
    print("扩展后的Grid数据结构（支持三极管等节点元件）")
    print("="*80)
    print("""
### 1. 基本网格结构
- m, n: 网格行数和列数
- vertical_dis: shape=(m,), 垂直方向各行的y坐标
- horizontal_dis: shape=(n,), 水平方向各列的x坐标

### 2. 边的连通性
- has_vedge: shape=(m-1, n), 垂直边是否存在 (1=有边, 0=无边)
- has_hedge: shape=(m, n-1), 水平边是否存在 (1=有边, 0=无边)

### 3. 边上元件（传统双端元件）
垂直元件 (vcomp_*): shape=(m-1, n)
- vcomp_type: 元件类型 (TYPE_RESISTOR, TYPE_VOLTAGE_SOURCE等)
- vcomp_label: 元件标签编号
- vcomp_value: 元件值
- vcomp_value_unit: 单位 (UNIT_MODE_1, UNIT_MODE_k等)
- vcomp_direction: 方向 (0或1)
- vcomp_measure: 测量类型
- vcomp_measure_label: 测量标签
- vcomp_measure_direction: 测量方向
- vcomp_control_meas_label: 受控源控制量标签

水平元件 (hcomp_*): shape=(m, n-1)
- hcomp_type, hcomp_label, hcomp_value等（与vcomp_*对应）

### 4. 节点元件（新增，支持三极管等多端元件）
- node_comp_type: shape=(m, n), 节点元件类型
  * NODE_TYPE_NONE = 0 (无元件)
  * NODE_TYPE_TRANSISTOR_NPN = 1 (NPN三极管)
  * NODE_TYPE_TRANSISTOR_PNP = 2 (PNP三极管)
  * NODE_TYPE_DIODE = 3 (二极管)
  * NODE_TYPE_OPAMP = 4 (运放)

- node_comp_label: shape=(m, n), 节点元件标签编号

- node_comp_orientation: shape=(m, n), 节点元件朝向
  * 0 = up (朝上)
  * 1 = right (朝右)
  * 2 = down (朝下)
  * 3 = left (朝左)

- node_comp_connections: shape=(m, n), dtype=object
  每个元素是一个dict或None，包含元件引脚的连接信息
  
  对于三极管，字典格式：
  {
      'base': (x, y),      # 基极连接的坐标
      'collector': (x, y), # 集电极连接的坐标
      'emitter': (x, y)    # 发射极连接的坐标
  }

### 5. 其他属性
- use_value_annotation: bool, 是否在图上标注数值
- note: str, 版本号 (如"v10")
- id: str, 电路ID
- label_numerical_subscript: bool, 标签是否使用数字下标
""")
    print("="*80)


if __name__ == "__main__":
    # 打印数据结构说明
    print_grid_structure()
    
    # 生成示例电路
    print("\n\n" + "="*80)
    print("Generating transistor circuit example...")
    print("="*80)
    circuit = generate_transistor_amplifier_example()
    
    if circuit.valid:
        print("[OK] Circuit is valid")
        print(f"[OK] Node count: {len(circuit.nodes)}")
        print(f"[OK] Branch count: {len(circuit.branches)}")
        
        # 生成LaTeX代码
        latex_code = circuit.to_latex()
        spice_code = circuit._to_SPICE()
        
        # 保存到文件
        output_file = "transistor_example.tex"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(latex_code)
        print(f"[OK] LaTeX code saved to: {output_file}")
        
        # 打印Grid结构摘要
        print("\n" + "="*80)
        print("Grid Structure Summary")
        print("="*80)
        print(f"Grid size: {circuit.m} x {circuit.n}")
        print(f"\nNode component type matrix:\n{circuit.node_comp_type}")
        print(f"\nNode component label matrix:\n{circuit.node_comp_label}")
        print(f"\nNode component orientation matrix:\n{circuit.node_comp_orientation}")
        print(f"\nVertical component type matrix:\n{circuit.vcomp_type}")
        print(f"\nHorizontal component type matrix:\n{circuit.hcomp_type}")
        
        # 打印支路信息
        print("\n" + "="*80)
        print("Branch Information")
        print("="*80)
        for br in circuit.branches:
            if br.get('is_node_component', False):
                print(f"  [Transistor] Q{br['label']}: B={br['base_node']}, C={br['collector_node']}, E={br['emitter_node']}")
            else:
                print(f"  [Edge] type={br['type']}, label={br['label']}, n1={br['n1']}, n2={br['n2']}")
    else:
        print("[FAIL] Circuit is invalid")
