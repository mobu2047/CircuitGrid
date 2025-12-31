# 工具图案来源与 LaTeX 渲染对比分析

## 1. 工具中的图案来源

### 1.1 绘制函数：`draw_npn` (component_renderer.py)
- **坐标系统**：Tkinter Canvas，y 向下为正（原点在左上角）
- **旋转角度定义**：
  ```python
  angles = {0: -90, 1: 180, 2: 90, 3: 0}  # Tkinter 角度
  ```
- **引脚位置定义**（相对于元件中心，旋转前）：
  ```python
  cx3, cy3 = rotate(0, -lead_len)  # C 在上（负y方向）
  ex3, ey3 = rotate(0, lead_len)   # E 在下（正y方向）
  ```
- **旋转函数**：
  ```python
  def rotate(px, py):
      cos_a, sin_a = math.cos(angle), math.sin(angle)
      return x + px*cos_a - py*sin_a, y + px*sin_a + py*cos_a
  ```

### 1.2 关键点
- 工具中使用**负 y 方向**表示"上方"（因为 Tkinter y 向下）
- 工具中使用**正 y 方向**表示"下方"
- 旋转是**顺时针**还是**逆时针**取决于角度定义

## 2. LaTeX 代码中的图案

### 2.1 CircuitTikZ npn 节点
- **坐标系统**：LaTeX/TikZ，y 向上为正（原点在左下角）
- **旋转角度定义**：
  ```python
  orientation_map = {0: 90, 1: 0, 2: -90, 3: 180}  # LaTeX 角度
  ```
- **节点定义**：
  ```latex
  \node[npn, rotate={rotation}] (Q0) at (x, y) {};
  ```
- **CircuitTikZ 标准**：
  - 默认方向（rotate=0）：base 在左，**C 在上**，**E 在下**
  - 旋转后，C 和 E 的相对位置保持不变（都是相对于 base 旋转）

### 2.2 关键点
- CircuitTikZ 使用**正 y 方向**表示"上方"
- CircuitTikZ 使用**负 y 方向**表示"下方"
- 旋转角度：**正角度 = 逆时针**（TikZ 标准）

## 3. 坐标系统转换

### 3.1 物理坐标转换
- `vertical_dis[i] = (m - 1 - i) * 3.0`
- 网格行 i 小 → vertical_dis 大 → LaTeX 中在上方
- 网格行 i 大 → vertical_dis 小 → LaTeX 中在下方

### 3.2 问题分析
当工具中显示 C 在上（负 y 方向）时：
- 工具中的引脚位置：`cx3, cy3 = rotate(0, -lead_len)` → 画布上方
- 对应的 connections：应该连接到**上方节点**（i-1, j）
- 物理坐标：`vertical_dis[i-1]` → **y 值较大** → LaTeX 中在上方

**理论上应该一致！**

## 4. 上下镜像反转的根本原因

### 4.1 可能的原因

#### 原因 1：旋转方向相反
- **Tkinter**：角度定义可能与 LaTeX 相反
- **LaTeX**：rotate=90 是逆时针旋转
- **Tkinter**：angle=-90 可能是顺时针旋转

#### 原因 2：默认方向不同
- **CircuitTikZ npn**：默认 base 在左，C 在上，E 在下
- **工具中**：可能默认方向不同

#### 原因 3：坐标系统映射错误
- 工具中的"上方"（负 y）可能映射到了 LaTeX 的"下方"（小 y 值）
- 或者 connections 中的坐标映射错误

### 4.2 验证方法
需要检查：
1. 工具中 orientation=0 (up) 时，C 和 E 的实际位置
2. LaTeX 中 rotation=90 时，C 和 E 的实际位置
3. connections 中的坐标是否正确对应

## 5. 修复方向

如果工具和 LaTeX 上下镜像反转，可能的修复方案：

### 方案 1：交换工具中的 C 和 E 位置
- 工具中：E 在上，C 在下
- LaTeX 中：C 在上，E 在下
- 连接时：交换映射

### 方案 2：修正旋转角度
- 检查 Tkinter 和 LaTeX 的旋转方向是否一致
- 如果不一致，调整角度定义

### 方案 3：修正坐标映射
- 检查 connections 中的坐标是否正确
- 确保工具中的"上方"映射到 LaTeX 的"上方"
