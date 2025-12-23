"""
Circuit Grid Editor - 电路网格编辑器

入口文件

功能：
- 可视化编辑电路网格
- 添加/删除边和元件
- 设置元件类型和参数
- 导出 LaTeX 和 SPICE

使用方法：
    python main.py
    
快捷键：
    Ctrl+N: 新建
    Ctrl+O: 打开
    Ctrl+S: 保存
    
交互：
    左键点击边/节点: 选中，在右侧面板编辑属性
    右键点击边: 切换边存在/删除
    右键点击节点: 切换交叉点标记
"""
import tkinter as tk
import sys
import os

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views.main_window import MainWindow


def main():
    """应用入口"""
    root = tk.Tk()
    
    # 设置主题样式
    try:
        root.tk.call('source', 'azure.tcl')  # 如果有主题文件
    except:
        pass  # 使用默认主题
    
    # 设置 DPI 感知（Windows）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # 创建主窗口
    app = MainWindow(root)
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()
