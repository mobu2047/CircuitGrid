# 上下镜像反转问题修复策略

## 问题确认
用户反馈：工具中的图案和 LaTeX 代码中渲染的图案上下镜像反转了。

## 根本原因分析

### 1. 坐标系统差异
- **Tkinter Canvas**：y 向下为正，原点在左上角
  - 负 y = 画布上方
  - 正 y = 画布下方
- **LaTeX/TikZ**：y 向上为正，原点在左下角
  - 正 y = LaTeX 上方
  - 负 y = LaTeX 下方

### 2. 物理坐标转换
- `vertical_dis[i] = (m - 1 - i) * 3.0`
- 网格行 i 小 → vertical_dis 大 → LaTeX 中在上方
- 网格行 i 大 → vertical_dis 小 → LaTeX 中在下方

### 3. 默认坐标定义
在 `get_node_component_draw` 中：
```python
cx, cy = connections.get('collector', (x, y-1))  # 默认 collector 在上方（y-1）
ex, ey = connections.get('emitter', (x, y+1))    # 默认 emitter 在下方（y+1）
```

**问题**：在 LaTeX 坐标系统中：
- `y-1` 表示**更小的 y 值** = **LaTeX 中的下方**！
- `y+1` 表示**更大的 y 值** = **LaTeX 中的上方**！

**这就是上下反转的根本原因！**

## 修复方案

### 方案 1：修正默认坐标定义（推荐）
在 `get_node_component_draw` 中，默认坐标应该：
```python
cx, cy = connections.get('collector', (x, y+1))  # collector 在上方（y+1，更大的y值）
ex, ey = connections.get('emitter', (x, y-1))     # emitter 在下方（y-1，更小的y值）
```

### 方案 2：保持工具和 LaTeX 的交换连接
如果工具中确实 C 在上（负y），E 在下（正y），那么：
- 工具中的 C（上方）→ connections 中应该存储**上方节点的物理坐标**（y值大）
- 工具中的 E（下方）→ connections 中应该存储**下方节点的物理坐标**（y值小）

但当前默认坐标定义是反的！

## 验证逻辑

对于 orientation=0 (up) 的 NPN：
- **工具中显示**：C 在上（`rotate(0, -lead_len)`），E 在下（`rotate(0, lead_len)`）
- **connections 应该**：
  - collector → 上方节点 (i-1, j) → `vertical_dis[i-1]` → **y 值大**（LaTeX 上方）
  - emitter → 下方节点 (i+1, j) → `vertical_dis[i+1]` → **y 值小**（LaTeX 下方）
- **LaTeX 渲染**：
  - CircuitTikZ npn：C 在上，E 在下
  - 应该：C 连接到 `vertical_dis[i-1]`（y值大），E 连接到 `vertical_dis[i+1]`（y值小）

**当前代码的问题**：默认坐标 `(x, y-1)` 和 `(x, y+1)` 是反的！
