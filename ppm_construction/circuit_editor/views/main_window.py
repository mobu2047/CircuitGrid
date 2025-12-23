"""
主窗口 - 应用程序主界面

布局：
┌──────────────────────────────────────────────────────┐
│  Toolbar                                             │
├────────┬─────────────────────────┬───────────────────┤
│        │                         │                   │
│ Comp   │      GridCanvas         │  PropertyPanel    │
│ Palette│                         │                   │
│        │                         │                   │
└────────┴─────────────────────────┴───────────────────┘
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.grid_model import GridModel
from views.grid_canvas import GridCanvas
from views.property_panel import PropertyPanel
from views.component_palette import ComponentPalette
from registry.component_registry import ComponentConfig


class MainWindow:
    """主窗口"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Circuit Grid Editor")
        self.root.geometry("1200x750")
        
        self.model = GridModel(m=4, n=4)
        self.current_file: str = None
        
        # 状态（拖拽功能已禁用）
        self.dragging_component: tuple = None  # (is_edge, ComponentConfig)
        
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._bind_shortcuts()
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File 菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Export 菜单
        export_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Export", menu=export_menu)
        export_menu.add_command(label="Export LaTeX...", command=self._export_latex)
        export_menu.add_command(label="Export SPICE...", command=self._export_spice)
        
        # Grid 菜单
        grid_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Grid", menu=grid_menu)
        grid_menu.add_command(label="Resize Grid...", command=self._resize_grid)
        grid_menu.add_command(label="Clear All", command=self._clear_all)
        
        # Help 菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Shortcuts", command=self._show_shortcuts)
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        # 文件操作
        ttk.Button(toolbar, text="📄 New", command=self._new_file).pack(side='left', padx=2)
        ttk.Button(toolbar, text="📂 Open", command=self._open_file).pack(side='left', padx=2)
        ttk.Button(toolbar, text="💾 Save", command=self._save_file).pack(side='left', padx=2)
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=10)
        
        # 导出
        ttk.Button(toolbar, text="📤 LaTeX", command=self._export_latex).pack(side='left', padx=2)
        ttk.Button(toolbar, text="📤 SPICE", command=self._export_spice).pack(side='left', padx=2)
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=10)
        
        # Grid 大小
        ttk.Label(toolbar, text="Grid:").pack(side='left', padx=(5, 2))
        self.grid_size_var = tk.StringVar(value="4x4")
        grid_combo = ttk.Combobox(toolbar, textvariable=self.grid_size_var,
                                  state='readonly', width=6)
        grid_combo['values'] = ["3x3", "4x4", "5x5", "6x6", "8x8", "10x10"]
        grid_combo.pack(side='left', padx=2)
        grid_combo.bind('<<ComboboxSelected>>', self._on_grid_size_changed)
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=10)
        
        # 状态提示
        self.status_label = ttk.Label(toolbar, text="Ready", foreground='gray')
        self.status_label.pack(side='right', padx=10)
    
    def _create_main_area(self):
        """创建主区域"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # === 左侧：元件库 ===
        self.component_palette = ComponentPalette(main_frame, width=100)
        self.component_palette.pack(side='left', fill='y', padx=(0, 5))
        
        # 绑定选择事件（拖拽功能已禁用）
        self.component_palette.on_component_selected = self._on_palette_select
        
        # === 中间：画布 ===
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side='left', fill='both', expand=True)
        
        # 滚动条
        h_scroll = ttk.Scrollbar(canvas_frame, orient='horizontal')
        v_scroll = ttk.Scrollbar(canvas_frame, orient='vertical')
        
        canvas_container = tk.Canvas(canvas_frame,
                                     xscrollcommand=h_scroll.set,
                                     yscrollcommand=v_scroll.set,
                                     bg='#F0F0F0')
        
        h_scroll.config(command=canvas_container.xview)
        v_scroll.config(command=canvas_container.yview)
        
        h_scroll.pack(side='bottom', fill='x')
        v_scroll.pack(side='right', fill='y')
        canvas_container.pack(side='left', fill='both', expand=True)
        
        # Grid 画布
        self.grid_canvas = GridCanvas(canvas_container, self.model)
        canvas_container.create_window(0, 0, anchor='nw', window=self.grid_canvas)
        
        def update_scroll_region(event=None):
            canvas_container.config(scrollregion=canvas_container.bbox("all"))
        self.grid_canvas.bind('<Configure>', update_scroll_region)
        
        self.canvas_container = canvas_container
        
        # 拖拽功能已禁用，使用点击选择模式
        
        # === 右侧：属性面板 ===
        self.property_panel = PropertyPanel(main_frame, self.model, width=250)
        self.property_panel.pack(side='right', fill='y', padx=(10, 0))
        
        # 连接画布事件到属性面板
        self.grid_canvas.on_edge_selected = self.property_panel.show_edge
        self.grid_canvas.on_node_selected = self.property_panel.show_node
        self.grid_canvas.on_pin_connected = self._on_pin_connected
        self.grid_canvas.on_component_placed = self._on_component_placed
        self.grid_canvas.on_cancel = self._on_cancel
    
    def _bind_shortcuts(self):
        """绑定快捷键"""
        self.root.bind('<Control-s>', lambda e: self._save_file())
        self.root.bind('<Control-o>', lambda e: self._open_file())
        self.root.bind('<Control-n>', lambda e: self._new_file())
        self.root.bind('<Escape>', lambda e: self._cancel_operation())
        self.root.bind('<Delete>', lambda e: self._delete_selected())
    
    # ============================================================
    # 拖放处理
    # ============================================================
    
    def _on_palette_select(self, is_edge: bool, comp: ComponentConfig):
        """从元件库选中元件（点击选择模式）"""
        self.status_label.config(text=f"Selected: {comp.display_name} - Click to place (Esc to cancel)")
        self.dragging_component = (is_edge, comp)
        # 设置待放置元件
        self.grid_canvas.pending_component = (is_edge, comp.type_id)
    
    # 拖拽功能已禁用，使用点击选择 + 点击放置模式
    
    def _on_pin_connected(self, i: int, j: int, pin_name: str, ti: int, tj: int):
        """引脚连接完成"""
        self.status_label.config(text=f"Connected {pin_name} to ({ti}, {tj})")
    
    def _on_component_placed(self, is_edge: bool, type_id: int, target):
        """元件放置完成"""
        from registry.component_registry import get_edge_component, get_node_component
        comp = get_edge_component(type_id) if is_edge else get_node_component(type_id)
        name = comp.display_name if comp else "Component"
        self.status_label.config(text=f"Placed {name} - Click to place more (Esc to cancel)")
    
    def _on_cancel(self):
        """取消操作（右键或ESC触发）"""
        self.dragging_component = None
        self.status_label.config(text="Ready")
    
    # ============================================================
    # 文件操作
    # ============================================================
    
    def _new_file(self):
        """新建文件"""
        if messagebox.askyesno("New File", "Create new circuit? Unsaved changes will be lost."):
            self.model = GridModel(m=4, n=4)
            self._refresh_canvas()
            self.current_file = None
            self.root.title("Circuit Grid Editor - New")
            self.status_label.config(text="New circuit created")
    
    def _open_file(self):
        """打开文件"""
        filepath = filedialog.askopenfilename(
            title="Open Circuit",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            try:
                self.model = GridModel.load_json(filepath)
                self._refresh_canvas()
                self.current_file = filepath
                self.root.title(f"Circuit Grid Editor - {os.path.basename(filepath)}")
                self.status_label.config(text=f"Opened: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{e}")
    
    def _save_file(self):
        """保存文件"""
        if self.current_file:
            self.model.save_json(self.current_file)
            self.status_label.config(text="Saved")
        else:
            self._save_file_as()
    
    def _save_file_as(self):
        """另存为"""
        filepath = filedialog.asksaveasfilename(
            title="Save Circuit As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            self.model.save_json(filepath)
            self.current_file = filepath
            self.root.title(f"Circuit Grid Editor - {os.path.basename(filepath)}")
            self.status_label.config(text=f"Saved: {os.path.basename(filepath)}")
    
    # ============================================================
    # 导出
    # ============================================================
    
    def _export_latex(self):
        """导出 LaTeX"""
        filepath = filedialog.asksaveasfilename(
            title="Export LaTeX",
            defaultextension=".tex",
            filetypes=[("TeX files", "*.tex"), ("All files", "*.*")]
        )
        if filepath:
            try:
                circuit = self.model.to_circuit()
                latex_code = circuit.to_latex()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(latex_code)
                self.status_label.config(text=f"LaTeX exported")
                messagebox.showinfo("Exported", f"LaTeX exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export LaTeX:\n{e}")
    
    def _export_spice(self):
        """导出 SPICE"""
        filepath = filedialog.asksaveasfilename(
            title="Export SPICE",
            defaultextension=".sp",
            filetypes=[("SPICE files", "*.sp"), ("All files", "*.*")]
        )
        if filepath:
            try:
                circuit = self.model.to_circuit()
                spice_code = circuit._to_SPICE()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(spice_code)
                self.status_label.config(text=f"SPICE exported")
                messagebox.showinfo("Exported", f"SPICE exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export SPICE:\n{e}")
    
    # ============================================================
    # Grid 操作
    # ============================================================
    
    def _resize_grid(self):
        """调整 Grid 大小"""
        dialog = GridSizeDialog(self.root, self.model.m, self.model.n)
        if dialog.result:
            new_m, new_n = dialog.result
            self.model.resize(new_m, new_n)
            self._refresh_canvas()
            self.grid_size_var.set(f"{new_m}x{new_n}")
    
    def _on_grid_size_changed(self, event=None):
        """Grid 大小下拉框改变"""
        size_str = self.grid_size_var.get()
        m, n = map(int, size_str.split('x'))
        self.model.resize(m, n)
        self._refresh_canvas()
    
    def _clear_all(self):
        """清空所有"""
        if messagebox.askyesno("Clear All", "Clear all components?"):
            m, n = self.model.m, self.model.n
            self.model = GridModel(m=m, n=n)
            self._refresh_canvas()
            self.status_label.config(text="Cleared")
    
    def _refresh_canvas(self):
        """刷新画布"""
        self.grid_canvas.destroy()
        self.grid_canvas = GridCanvas(self.canvas_container, self.model)
        self.canvas_container.create_window(0, 0, anchor='nw', window=self.grid_canvas)
        
        self.property_panel.model = self.model
        self.grid_canvas.on_edge_selected = self.property_panel.show_edge
        self.grid_canvas.on_node_selected = self.property_panel.show_node
        self.grid_canvas.on_pin_connected = self._on_pin_connected
        self.grid_canvas.on_component_placed = self._on_component_placed
        self.grid_canvas.on_cancel = self._on_cancel
        
        # 拖拽功能已禁用
    
    def _cancel_operation(self):
        """取消当前操作"""
        self.dragging_component = None
        self.grid_canvas.cancel_drop()
        self.grid_canvas.pending_component = None  # 清除待放置元件
        self.status_label.config(text="Ready")
    
    def _delete_selected(self):
        """删除选中的元素"""
        if self.grid_canvas.selected_edge:
            direction, i, j = self.grid_canvas.selected_edge
            if direction == 'h':
                self.model.toggle_hedge(i, j)
            else:
                self.model.toggle_vedge(i, j)
            self.grid_canvas.selected_edge = None
        elif self.grid_canvas.selected_node:
            i, j = self.grid_canvas.selected_node
            self.model.set_node_component(i, j, 0)  # 清除节点元件
            self.grid_canvas.selected_node = None
    
    def _show_shortcuts(self):
        """显示快捷键帮助"""
        shortcuts = """
Keyboard Shortcuts:
───────────────────
Ctrl+N     New file
Ctrl+O     Open file
Ctrl+S     Save file
Delete     Delete selected
Escape     Cancel operation

Mouse:
───────────────────
Left click       Select edge/node
Right click      Toggle edge/junction
Drag from palette    Add component
Drag pin         Connect to node
        """
        messagebox.showinfo("Shortcuts", shortcuts)


class GridSizeDialog:
    """Grid 大小对话框"""
    
    def __init__(self, parent, current_m, current_n):
        self.result = None
        
        dialog = tk.Toplevel(parent)
        dialog.title("Resize Grid")
        dialog.geometry("250x150")
        dialog.transient(parent)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Rows (m):").grid(row=0, column=0, padx=10, pady=10)
        self.m_var = tk.StringVar(value=str(current_m))
        ttk.Entry(dialog, textvariable=self.m_var, width=8).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Columns (n):").grid(row=1, column=0, padx=10, pady=10)
        self.n_var = tk.StringVar(value=str(current_n))
        ttk.Entry(dialog, textvariable=self.n_var, width=8).grid(row=1, column=1, padx=10, pady=10)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="OK", command=lambda: self._on_ok(dialog)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=5)
        
        dialog.wait_window()
    
    def _on_ok(self, dialog):
        try:
            m = int(self.m_var.get())
            n = int(self.n_var.get())
            if m >= 2 and n >= 2:
                self.result = (m, n)
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Grid size must be at least 2x2")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
