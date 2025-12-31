# 完整流程分析 - 工具图案来源与LaTeX渲染

## 1. 工具中的图案来源

### 1.1 绘制函数：`draw_npn` (component_renderer.py:367-436)

**输入参数**：
- `x, y`: 画布坐标（元件中心位置）
- `orientation`: 基极指向的方向 (0=up, 1=right, 2=down, 3=left)

**旋转角度定义**：
```python
angles = {0: -90, 1: 180, 2: 90, 3: 0}  # Tkinter角度（度）
angle = math.radians(angles.get(orientation, 0))
```

**旋转函数**：
```python
def rotate(px, py):
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return x + px*cos_a - py*sin_a, y + px*sin_a + py*cos_a
```

**引脚位置定义**（旋转前，相对于元件中心）：
```python
# 基极：指向orientation方向
bx1, by1 = rotate(lead_len, 0)  # 基极末端

# 集电极和发射极：相对于元件中心
cx3, cy3 = rotate(0, -lead_len)  # C在上（负y方向）
ex3, ey3 = rotate(0, lead_len)  # E在下（正y方向）
```

**关键点**：
- 工具中C在上（`rotate(0, -lead_len)`），E在下（`rotate(0, lead_len)`）
- 这与CircuitTikZ标准一致（C在上，E在下）

## 2. LaTeX中的图案来源

### 2.1 渲染函数：`get_node_component_draw` (grid_rules.py:446-640)

**旋转角度定义**：
```python
orientation_map = {0: 90, 1: 0, 2: -90, 3: 180}  # LaTeX角度（度）
rotation = orientation_map.get(orientation, 90)
```

**CircuitTikZ节点**：
```latex
\node[npn, rotate={rotation}] (Q0) at (x, y) {};
```

**CircuitTikZ标准**（rotate=0）：
- Base在左
- Collector在上
- Emitter在下

## 3. 关键发现

### 3.1 旋转角度对比

| orientation | 工具角度 | LaTeX角度 | 差异 |
|-------------|---------|-----------|------|
| 0 (up)      | -90°    | 90°       | 相差180° |
| 1 (right)   | 180°    | 0°        | 相差180° |
| 2 (down)    | 90°     | -90°      | 相差180° |
| 3 (left)    | 0°      | 180°      | 相差180° |

**所有方向的旋转角度都相差180度！**

### 3.2 问题根源

**工具中的旋转和LaTeX中的旋转相差180度！**

这意味着：
- 工具中orientation=0时，旋转-90度，C在上，E在下
- LaTeX中orientation=0时，旋转90度，但旋转方向相反，导致C和E位置相反！

**解决方案**：
1. 修正LaTeX中的旋转角度，使其与工具一致
2. 或者修正工具中的旋转角度，使其与LaTeX一致
3. 或者在所有情况下都交换C和E的连接

## 4. 根本修复方案

既然所有方向都上下翻转，说明工具和LaTeX的旋转方向完全相反。

**最佳方案**：修正LaTeX中的旋转角度，使其与工具一致：
- orientation=0: rotation=-90（而不是90）
- orientation=1: rotation=180（而不是0）
- orientation=2: rotation=90（而不是-90）
- orientation=3: rotation=0（而不是180）

这样工具和LaTeX的旋转就一致了，不需要交换C和E。

