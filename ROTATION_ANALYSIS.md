# CircuitTikZ npn 节点旋转分析

## CircuitTikZ npn 节点默认方向（rotate=0）
- **Base (B)**: 在左
- **Collector (C)**: 在上（y值大）
- **Emitter (E)**: 在下（y值小）

## 旋转后的引脚位置

### orientation=0 (up), rotation=90度
- 逆时针旋转90度
- **Base**: 在上
- **Collector**: 在右（x值大）← 从"上"变成"右"
- **Emitter**: 在左（x值小）← 从"下"变成"左"
- **关键**：C和E的关系从"上下"变成"左右"！

### orientation=1 (right), rotation=0度
- 不旋转
- **Base**: 在左
- **Collector**: 在上（y值大）
- **Emitter**: 在下（y值小）
- **正常**：C和E保持上下关系

### orientation=2 (down), rotation=-90度
- 顺时针旋转90度
- **Base**: 在下
- **Collector**: 在左（x值小）← 从"上"变成"左"
- **Emitter**: 在右（x值大）← 从"下"变成"右"
- **关键**：C和E的关系从"上下"变成"左右"！

### orientation=3 (left), rotation=180度
- 旋转180度
- **Base**: 在右
- **Collector**: 在下（y值小）← 从"上"变成"下"
- **Emitter**: 在上（y值大）← 从"下"变成"上"
- **关键**：C和E上下反转！

## 问题分析

当旋转90度或270度时：
- C和E从"上下关系"变成"左右关系"
- connections中的坐标：cx,cy 和 ex,ey 的x、y含义会改变
- 需要根据旋转角度动态调整连接逻辑

当旋转180度时：
- C和E上下反转
- 需要交换C和E的连接

## 修复策略

需要根据rotation角度动态决定：
1. **rotation=0**: 正常连接（C在上，E在下）
2. **rotation=90**: C在右，E在左（需要根据x值判断）
3. **rotation=-90**: C在左，E在右（需要根据x值判断）
4. **rotation=180**: C和E上下反转（需要交换）
