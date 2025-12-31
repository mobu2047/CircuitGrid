# NPN 上下翻转问题根本原因分析

## 问题描述
用户反馈：工具中的 NPN 图案和 LaTeX 渲染出来的结果是上下翻转的。

## 根本问题定位

### 1. CircuitTikZ npn 节点的标准定义
- CircuitTikZ 的 `\node[npn]` 节点：
  - **Collector (C) 在上方**
  - **Emitter (E) 在下方**
  - **Base (B) 在中间（水平方向）**
- 这是 CircuitTikZ 的标准定义，不可改变

### 2. 工具中的当前实现
- `draw_npn` 函数中：
  - `ex3, ey3 = rotate(0, -lead_len)`  # 发射极在上方（负y方向）
  - `cx3, cy3 = rotate(0, lead_len)`   # 集电极在下方（正y方向）
- **问题**：工具中显示 E 在上，C 在下，与 CircuitTikZ 标准相反！

### 3. LaTeX 渲染中的连接逻辑
- 当前代码：
  ```python
  ret += f"\\draw ({comp_label_main}{int(label)}.C) |- ({ex:.1f},{ey:.1f});\n"  # LaTeX C 连接到工具的 E
  ret += f"\\draw ({comp_label_main}{int(label)}.E) |- ({cx:.1f},{cy:.1f});\n"  # LaTeX E 连接到工具的 C
  ```
- **问题**：这个交换逻辑是为了补偿工具中的翻转，但这是错误的！

### 4. 根本原因
**工具中的引脚位置定义与 CircuitTikZ 标准相反！**

正确的做法应该是：
1. **工具中的渲染**：应该与 CircuitTikZ 标准一致
   - C 在上（负y方向）
   - E 在下（正y方向）
2. **LaTeX 渲染**：直接连接，不需要交换
   - LaTeX 的 C 连接到 connections 中的 collector
   - LaTeX 的 E 连接到 connections 中的 emitter

### 5. 修复方案
1. **修复工具中的渲染**：交换 C 和 E 的位置，使其与 CircuitTikZ 标准一致
2. **修复 LaTeX 渲染**：移除交换逻辑，直接连接

## 坐标系统说明
- **Tkinter Canvas**：y 向下为正（原点在左上角）
- **CircuitTikZ**：y 向上为正（原点在左下角）
- **vertical_dis**：已经考虑了 y 轴反转，`vertical_dis[i] = (m - 1 - i) * 3.0`

因此，在工具中：
- **负 y 方向（向上）** = 在画布上显示为**上方**
- **正 y 方向（向下）** = 在画布上显示为**下方**

但在物理坐标（LaTeX）中：
- **y 值大** = 在 LaTeX 中显示为**上方**
- **y 值小** = 在 LaTeX 中显示为**下方**

由于 `vertical_dis[i] = (m - 1 - i) * 3.0`，所以：
- 网格行 i 小 → vertical_dis 大 → LaTeX 中在上方
- 网格行 i 大 → vertical_dis 小 → LaTeX 中在下方

## 正确的引脚位置定义

对于 orientation=0 (up) 的 NPN：
- **Collector** 应该连接到**上方节点**（i-1, j）
  - 工具中：`rotate(0, -lead_len)` → 画布上方
  - 物理坐标：`vertical_dis[i-1]` → LaTeX 上方
- **Emitter** 应该连接到**下方节点**（i+1, j）
  - 工具中：`rotate(0, lead_len)` → 画布下方
  - 物理坐标：`vertical_dis[i+1]` → LaTeX 下方

**当前代码的问题**：工具中 E 在上，C 在下，与标准相反！
