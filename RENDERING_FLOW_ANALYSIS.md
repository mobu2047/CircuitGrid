# 电路元件渲染流程分析

## 1. 工具中的渲染（Tkinter Canvas）

### 1.1 绘制函数（component_renderer.py）
- `draw_npn(canvas, x, y, orientation, ...)` 
  - 输入：画布坐标 `(x, y)`，方向 `orientation` (0=up, 1=right, 2=down, 3=left)
  - 输出：返回引脚位置字典 `{'base': (bx1, by1), 'collector': (cx3, cy3), 'emitter': (ex3, ey3)}`
  - **这些坐标是画布像素坐标（Canvas Coordinates）**

### 1.2 坐标系统
- **画布坐标**：像素坐标，原点在左上角，x 向右，y 向下
- **网格坐标**：`(i, j)`，i 是行（向下），j 是列（向右）
- **物理坐标**：LaTeX 使用的坐标，通过 `horizontal_dis[j]` 和 `vertical_dis[i]` 转换

### 1.3 坐标转换
```python
# 网格坐标 -> 画布坐标
def _grid_to_canvas(i, j):
    x = PADDING + j * CELL_SIZE
    y = PADDING + i * CELL_SIZE
    return x, y

# 画布坐标 -> 网格坐标
def _canvas_to_grid(x, y):
    j = round((x - PADDING) / CELL_SIZE)
    i = round((y - PADDING) / CELL_SIZE)
    return i, j
```

## 2. Connections 数据的存储

### 2.1 自动连接（_auto_connect_transistor）
- 输入：网格坐标 `(i, j)`，方向 `orientation`
- 输出：`{'base': (ni, nj), 'collector': (ci, cj), 'emitter': (ei, ej)}`
- **存储格式：网格坐标 (i, j)**

### 2.2 手动连接（_on_release）
- 输入：画布坐标 `(x, y)`，目标网格 `(ti, tj)`
- 转换：`target_x = horizontal_dis[tj]`, `target_y = vertical_dis[ti]`
- 存储：`connections[pin_name] = (target_x, target_y)`
- **存储格式：物理坐标 (x, y)**

### 2.3 问题
- **两种存储格式混用**：自动连接用网格坐标，手动连接用物理坐标
- 这导致 LaTeX 渲染时需要判断格式并转换

## 3. LaTeX 渲染流程

### 3.1 CircuitTikZ 节点命名
- NPN: `\node[npn] (Q1) at (x, y) {};`
- 引脚：`Q1.B`, `Q1.C`, `Q1.E`
- MOSFET: `\node[nmos] (M1) at (x, y) {};`
- 引脚：`M1.G`, `M1.D`, `M1.S`

### 3.2 坐标系统
- CircuitTikZ 使用物理坐标 `(x, y)`
- x 向右，y 向上（与 Tkinter 相反！）
- `vertical_dis[i] = (m - 1 - i) * 3.0` 已经考虑了 y 轴反转

### 3.3 渲染流程（grid_rules.py）

#### 3.3.1 _draw_node_component
```python
def _draw_node_component(self, i, j):
    x = self.horizontal_dis[j]  # 物理坐标 x
    y = self.vertical_dis[i]     # 物理坐标 y
    connections = self.node_comp_connections[i][j]
    
    # 转换 connections：如果是网格坐标，转换为物理坐标
    converted_connections = convert_connections(connections, i, j)
    
    result = get_node_component_draw(x, y, node_type, label, orientation, 
                                     converted_connections)
```

#### 3.3.2 get_node_component_draw
```python
def get_node_component_draw(x, y, node_type, label, orientation, connections):
    # connections 现在应该是物理坐标 (x, y)
    # 提取引脚坐标
    cx, cy = connections.get('collector', (x, y-1))
    bx, by = connections.get('base', (x-1, y))
    ex, ey = connections.get('emitter', (x, y+1))
    
    # 生成 CircuitTikZ 代码
    ret = f"\\node[npn] (Q{label}) at ({x:.1f},{y:.1f}) {{}};\n"
    ret += f"\\draw (Q{label}.B) -- ({bx:.1f},{by:.1f});\n"
    ret += f"\\draw (Q{label}.C) |- ({cx:.1f},{cy:.1f});\n"
    ret += f"\\draw (Q{label}.E) |- ({ex:.1f},{ey:.1f});\n"
```

## 4. 问题根源

### 4.1 坐标系统不一致
1. **Tkinter**：y 向下，原点在左上角
2. **CircuitTikZ**：y 向上，原点在左下角
3. **vertical_dis** 已经考虑了 y 轴反转：`vertical_dis[i] = (m - 1 - i) * 3.0`

### 4.2 connections 格式不一致
1. **自动连接**：存储网格坐标 `(i, j)`
2. **手动连接**：存储物理坐标 `(x, y)`
3. **LaTeX 渲染**：需要统一为物理坐标

### 4.3 引脚位置映射问题
1. **工具中**：`draw_npn` 返回画布像素坐标
2. **connections**：存储的是目标节点的物理坐标（手动）或网格坐标（自动）
3. **LaTeX**：使用 connections 中的坐标连接到 CircuitTikZ 节点引脚

### 4.4 方向映射问题
- **工具中**：orientation 0=up, 1=right, 2=down, 3=left
- **CircuitTikZ**：rotation 角度不同
- **引脚位置**：不同方向的 C/E 或 D/S 位置可能不同

## 5. 解决方案

### 5.1 统一 connections 格式 ✅
- **所有 connections 都存储物理坐标**
- 在 `_auto_connect_transistor` 中，将网格坐标转换为物理坐标
- 添加了 `_auto_connect_mosfet` 函数，也返回物理坐标
- 简化了 LaTeX 渲染中的坐标转换逻辑（不再需要判断格式）

### 5.2 修复引脚位置映射
- **确保工具中的引脚位置与 CircuitTikZ 节点引脚位置一致**
- 工具中：`draw_npn` 返回画布像素坐标（用于显示）
- connections：存储目标节点的物理坐标（用于 LaTeX 渲染）
- **关键**：工具中的引脚位置（画布坐标）与 connections（物理坐标）是不同的坐标系统，但它们指向同一个目标节点

### 5.3 修复方向映射
- **确保工具中的 orientation 与 CircuitTikZ 的 rotation 正确对应**
- orientation_map: {0: 90, 1: 0, 2: -90, 3: 180}
- 需要检查不同方向的渲染是否正确

## 6. 修复后的流程

### 6.1 自动连接（_auto_connect_transistor / _auto_connect_mosfet）
1. 输入：网格坐标 `(i, j)`，方向 `orientation`
2. 计算目标网格坐标：`(ni, nj) = (i + di, j + dj)`
3. **转换为物理坐标**：`phys_x = horizontal_dis[nj]`, `phys_y = vertical_dis[ni]`
4. 返回：`{'base': (phys_x, phys_y), ...}`

### 6.2 手动连接（_on_release）
1. 输入：目标网格坐标 `(ti, tj)`
2. **转换为物理坐标**：`target_x = horizontal_dis[tj]`, `target_y = vertical_dis[ti]`
3. 存储：`connections[pin_name] = (target_x, target_y)`

### 6.3 LaTeX 渲染（_draw_node_component）
1. 获取 connections（现在统一是物理坐标）
2. **直接使用**，不再需要转换
3. 传递给 `get_node_component_draw` 生成 LaTeX 代码

## 7. 关键修复点

1. ✅ **统一 connections 格式**：所有 connections 现在都存储物理坐标
2. ✅ **简化坐标转换**：LaTeX 渲染中不再需要判断和转换格式
3. ✅ **添加 MOSFET 自动连接**：确保 MOSFET 也有自动连接功能

## 8. 待验证的问题

根据用户反馈，以下问题可能仍然存在：
1. **MOSFET right/left 方向**：上下镜像翻转，连线接反
2. **MOSFET up/down 方向**：左右接口方向正确，但是上下镜像翻转
3. **NPN right/left 方向**：图案一致但连线接反（集电极和射极）
4. **NPN up/down 方向**：既上下翻转也左右翻转
5. **PNP 所有方向**：上下镜像翻转

这些问题可能与以下因素有关：
- **工具中的引脚位置**（画布坐标）与 **CircuitTikZ 节点引脚位置**（物理坐标）的映射
- **不同方向的引脚位置计算**是否正确
- **connections 中的坐标**是否正确对应到目标节点

需要进一步调试和验证。
