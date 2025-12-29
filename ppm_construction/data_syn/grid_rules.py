import os
import json 
import numpy as np
import random
np.random.seed(42)
random.seed(42)
import readchar

# NOTE: Components Types
# 边上元件（Edge Components）- 双端元件
(
    TYPE_SHORT,
    TYPE_VOLTAGE_SOURCE,
    TYPE_CURRENT_SOURCE,
    TYPE_RESISTOR,
    TYPE_CAPACITOR,
    TYPE_INDUCTOR,

    TYPE_OPEN, # Open Circuit
    TYPE_VCCS, # Voltage-Controlled Current Source --> G in SPICE
    TYPE_VCVS, # Voltage-Controlled Voltage Source --> E in SPICE
    TYPE_CCCS, # Current-Controlled Current Source --> F in SPICE
    TYPE_CCVS, # Current-Controlled Voltage Source --> H in SPICE
) = tuple( range(11) )
NUM_NORMAL=6

# 节点上元件（Node Components）- 多端元件
(
    NODE_TYPE_NONE,
    NODE_TYPE_TRANSISTOR_NPN,  # NPN三极管
    NODE_TYPE_TRANSISTOR_PNP,  # PNP三极管
    NODE_TYPE_DIODE,           # 二极管
    NODE_TYPE_OPAMP,           # 运放
) = tuple( range(5) )

# NOTE: Type of Measurements
(
    MEAS_TYPE_NONE,
    MEAS_TYPE_VOLTAGE,
    MEAS_TYPE_CURRENT,
) = tuple( range(3) )

# NOTE: TYPE of Units
(
    UNIT_MODE_1,
    UNIT_MODE_k,
    UNIT_MODE_m,
    UNIT_MODE_u,
    UNIT_MODE_n,
    UNIT_MODE_p,
) = tuple( range(6) )

# NOTE: LATEX formatting
vlt7_latex_template = r"""\documentclass[border=10pt]{standalone}
\usepackage{tikz}
\usepackage{circuitikz}
\begin{document}
\begin{center}
\begin{circuitikz}[line width=1pt]
\ctikzset{tripoles/en amp/input height=0.5};
\ctikzset{inductors/scale=1.2, inductor=american}
<main>
\end{circuitikz}
\end{center}
\end{document}"""
v8_latex_template = r"""\documentclass[border=10pt]{standalone}
\usepackage{tikz}
\usepackage{circuitikz}
\tikzset{every node/.style={font=<font>}}
\tikzset{every draw/.style={font=<font>}}
\begin{document}
\begin{center}
\begin{circuitikz}[line width=1pt]
\ctikzset{tripoles/en amp/input height=0.5};
\ctikzset{inductors/scale=1.2, inductor=american}
<main>
\end{circuitikz}
\end{center}
\end{document}"""
v8_latex_template = r"""\documentclass[border=10pt]{standalone}
\usepackage{tikz}
\usepackage{circuitikz}
\tikzset{every node/.style={font=<font>}}
\tikzset{every draw/.style={font=<font>}}
\begin{document}
\begin{center}
\begin{circuitikz}[line width=1pt]
\ctikzset{tripoles/en amp/input height=0.5};
\ctikzset{inductors/scale=1.2, inductor=american}
<main>
\end{circuitikz}
\end{center}
\end{document}"""

LATEX_TEMPLATES = {
    "v<=7": vlt7_latex_template,
    "v8": v8_latex_template,
    "v9": v8_latex_template,
    "v10": v8_latex_template,
    "v11": v8_latex_template,
}

unit_scales = ["", "k", "m", "\\mu", "n", "p"]

LABEL_TYPE_NUMBER, LABEL_TYPE_STRING = tuple(range(2)) # label is numerical format or string format
# 边上元件的LaTeX信息: (circuitikz_type, label_prefix, unit)
components_latex_info = [("short", "", ""), ("V","U","V"), ("I","I","A"), ("generic","R","\Omega"), ("C","C","F"), ("L","L","H"),
                         ("open", "", ""), ("cisource", "", ""), ("cvsource", "", ""), ("cisource", "", ""), ("cvsource", "", "") ] # type, label, unit

# 节点元件的LaTeX信息: (circuitikz_type, label_prefix, unit)
node_components_latex_info = [
    ("", "", ""),           # NONE
    ("npn", "Q", ""),       # NPN三极管
    ("pnp", "Q", ""),       # PNP三极管
    ("D", "D", ""),         # 二极管
    ("op amp", "U", "")     # 运放
]

CUR_MODE_1, CUR_MODE_2, CUR_MODE_3, CUR_MODE_4, CUR_MODE_5, CUR_MODE_6 = tuple(range(6))
flow_direction = ["^>", ">_", "^>", "_>"]

def get_latex_line_draw(x1, y1, x2, y2,
                        type_number, 
                        label_subscript,
                        value, 
                        value_unit,
                        use_value_annotation,   # True: annotate value in the figure / False: annotate label in the figure
                        style="chinese",
                        measure_type=MEAS_TYPE_NONE,
                        measure_label="",
                        measure_direction=0,
                        control_label="",
                        label_subscript_type=LABEL_TYPE_NUMBER,
                        direction=0,
                        note='v5'
                    ) -> str:
    
    if direction == 1:
        x1, y1, x2, y2 = x2, y2, x1, y1
    meas_comp_same_direction = (direction == measure_direction)
    
    if style == "chinese":
        print(f"drawing between ({x1:.1f},{y1:.1f}) and ({x2:.1f},{y2:.1f})\n")
        print(f"type_num: {type_number}, label_num: {label_subscript}, value: {value}, use_value_annotation: {use_value_annotation}, label_type_number: {label_subscript_type}, direction: {direction}")
        print(f"measure_type: {measure_type}, measure_label: {measure_label}, measure_direction: {measure_direction}")
        type_number = int(type_number)
        
        comp_circuitikz_type = components_latex_info[type_number][0]
        comp_label_main = components_latex_info[type_number][1]
        comp_standard_unit = components_latex_info[type_number][2]

        # NOTE: Get the label of the component
        labl = ""
        if control_label == -1: control_label = ""
        control_label = f"_{control_label}" if control_label != "" else ""
        if use_value_annotation:    # numerical-type circuit
            if type_number < NUM_NORMAL:
                real_value = value
                unit_mode = value_unit
                unit_scale = unit_scales[unit_mode]
                if int(note[1:]) <= 9:
                    raise NotImplementedError
                elif int(note[1:]) > 9:
                    labl = f"{int(real_value)} \\mathrm{{ {unit_scale}{comp_standard_unit} }}"
            else:
                if type_number == TYPE_VCCS or type_number == TYPE_VCVS:
                    labl = f"{value} U_{{ {control_label} }}"
                elif type_number == TYPE_CCCS or type_number == TYPE_CCVS:
                    labl = f"{value} I_{{ {control_label} }}"

        else:       # label-type circuit
            if type_number < NUM_NORMAL:
                if label_subscript_type == LABEL_TYPE_NUMBER:
                    if type_number == TYPE_RESISTOR:
                        labl = f"{comp_label_main}_{{ {int(label_subscript)} }}" # e.g. R_{1}
                    elif type_number == TYPE_VOLTAGE_SOURCE or type_number == TYPE_CURRENT_SOURCE:
                        labl = f"{comp_label_main}_{{ S{int(label_subscript)} }}" # e.g. U_{S1}

                elif label_subscript_type == LABEL_TYPE_STRING:
                    labl = f"{comp_label_main}_{{ {label_subscript} }}" # e.g. R_{load}
            
            else:
                if type_number == TYPE_VCCS or type_number == TYPE_VCVS:
                    labl = f"\\beta_{{ {label_subscript} }} U_{{ {control_label} }}"
                elif type_number == TYPE_CCCS or type_number == TYPE_CCVS:
                    labl = f"\\alpha_{{ {label_subscript} }} I_{{ {control_label} }}"

        print(f'labl: {labl}')

        # NOTE: get the label of measurement
        if measure_label == -1: measure_label = ""
        measure_label = f"_{{{str(measure_label)}}}" if measure_label != "" else ""
        if measure_type == MEAS_TYPE_CURRENT:
            measure_label = f"I{measure_label}"
        elif measure_type == MEAS_TYPE_VOLTAGE:
            measure_label = f"U{measure_label}"
        
# NOTE: Plot the components 
            
# NOTE: plot the shorcut
        if type_number == TYPE_SHORT:
            ret = f"\\draw ({x1:.1f},{y1:.1f}) to[short] ({x2:.1f},{y2:.1f});\n"
            
            if not meas_comp_same_direction:
                    x1, y1, x2, y2 = x2, y2, x1, y1
            
            if measure_type == MEAS_TYPE_CURRENT:
                flow_dir = flow_direction[np.random.choice(range(4))]
                ret += f"\\draw ({x1:.1f},{y1:.1f}) to[short, f{flow_dir}=${measure_label}$] ({x2:.1f},{y2:.1f});\n"
            print(f"ret: {ret}")
            return ret
        
# NOTE: plot the voltage source
        elif type_number == TYPE_VOLTAGE_SOURCE:
            if int(note[1:]) < 8:
                ret =  f"\\draw ({x1:.1f},{y1:.1f}) to[V] ({x2:.1f},{y2:.1f});\n\\ctikzset{{american}}\n\\draw ({x1:.1f},{y1:.1f}) to [short, v=${labl}$] ({x2:.1f},{y2:.1f});\n\\ctikzset{{european}}\n"
            else:
                ret =  f"\\draw ({x1:.1f},{y1:.1f}) to [short] ({x2:.1f},{y2:.1f});\n\\ctikzset{{american}};\n\\draw ({x1:.1f},{y1:.1f}) to[rmeter, t, v=${labl}$] ({x2:.1f},{y2:.1f});\n\\ctikzset{{european}};\n"

            if not meas_comp_same_direction:
                x1, y1, x2, y2 = x2, y2, x1, y1
            if measure_type == MEAS_TYPE_CURRENT:
                flow_dir = flow_direction[np.random.choice(range(4))]
                ret += f"\\draw ({x1:.1f},{y1:.1f}) to[rmeter, f{flow_dir}=${measure_label}$] ({x2:.1f},{y2:.1f});\n"
            
            return ret

# NOTE: plot the current source
        elif type_number == TYPE_CURRENT_SOURCE:
            if int(note[1:]) >= 8:
                cur_mode_choices = [CUR_MODE_1, CUR_MODE_2] * 10 + [CUR_MODE_3, CUR_MODE_4] * 0 + [CUR_MODE_5, CUR_MODE_6] * 1
                cur_mode = np.random.choice(cur_mode_choices)
                print(f"cur_mode: {cur_mode} when ploting current source")
            else:
                cur_mode == CUR_MODE_1
            
            ret = f"\\draw ({x1:.1f},{y1:.1f}) to[I] ({x2:.1f},{y2:.1f});\n"

            if cur_mode == CUR_MODE_1 or cur_mode == CUR_MODE_2:
                mid = np.array([(x1+x2)/2, (y1+y2)/2])
                vector = np.array([x2-x1, y2-y1])
                normal = np.array([-vector[1], vector[0]], dtype=np.float64)
                normal /= np.linalg.norm(normal)
                if cur_mode == CUR_MODE_1:
                    new_mid = mid + 0.6*normal
                    new_mid_node = mid + normal

                else:
                    new_mid = mid - 0.6*normal
                    new_mid_node = mid - normal

                norm_vector = vector / np.linalg.norm(vector)
                new_start = new_mid - 0.4*norm_vector
                new_end = new_mid + 0.4*norm_vector
                ret += f"\\draw[-latexslim] ({new_start[0]:.1f},{new_start[1]:.1f}) to ({new_end[0]:.1f},{new_end[1]:.1f});\n"
                ret += f"\\node at ({new_mid_node[0]:.1f}, {new_mid_node[1]:.1f}) {{${labl}$}};\n"
                
            elif cur_mode in [CUR_MODE_3, CUR_MODE_4, CUR_MODE_5, CUR_MODE_6]:
                flow_dir = flow_direction[cur_mode-2]
                ret += f"\\draw ({x1:.1f},{y1:.1f}) to[rmeter, f{flow_dir}=${labl}$] ({x2:.1f},{y2:.1f});\n"
            
            v_plot_extra = ""
            if not meas_comp_same_direction:
                x1, y1, x2, y2 = x2, y2, x1, y1
                v_plot_extra = "^"
            if measure_type == MEAS_TYPE_VOLTAGE:
                ret += f"\\ctikzset{{american}}\n\\draw ({x1:.1f},{y1:.1f}) to[rmeter, v{v_plot_extra}=${measure_label}$] ({x2:.1f},{y2:.1f});\n\\ctikzset{{european}}\n"
                
            return ret

# NOTE: Plot resistance, capacitance & inductance
        elif type_number in [TYPE_RESISTOR, TYPE_CAPACITOR, TYPE_INDUCTOR]:
            ret = f"\\draw ({x1:.1f},{y1:.1f}) to[{comp_circuitikz_type}, l=${labl}$, ] ({x2:.1f},{y2:.1f});\n"

            v_plot_extra = ""
            if not meas_comp_same_direction:
                x1, y1, x2, y2 = x2, y2, x1, y1
                v_plot_extra = "^"
            if measure_type == MEAS_TYPE_VOLTAGE:
                ret +=  f"\\ctikzset{{american}}\n\\draw ({x1:.1f},{y1:.1f}) to[{comp_circuitikz_type}, v{v_plot_extra}=${measure_label}$] ({x2:.1f},{y2:.1f});\n\\ctikzset{{european}}\n"

            elif measure_type == MEAS_TYPE_CURRENT:
                if int(note[1:]) >= 8:
                    cur_mode_choices = [CUR_MODE_1, CUR_MODE_2] * 0 + [CUR_MODE_3, CUR_MODE_4] * 1 + [CUR_MODE_5, CUR_MODE_6] * 1
                    cur_mode = np.random.choice(cur_mode_choices)
                else:
                    cur_mode == CUR_MODE_5

                if cur_mode in [CUR_MODE_1, CUR_MODE_2]:
                    # ret = f"\\draw ({x1:.1f},{y1:.1f}) to[{comp_circuitikz_type}, l=${labl}$] ({x2:.1f},{y2:.1f});\n"
                    mid = np.array([(x1+x2)/2, (y1+y2)/2])
                    vector = np.array([x2-x1, y2-y1])
                    normal = np.array([-vector[1], vector[0]], dtype=np.float64)
                    normal /= np.linalg.norm(normal)
                    if cur_mode == CUR_MODE_1:
                        new_mid = mid + 0.4*normal
                        new_mid_node = mid + 0.8*normal

                    else:
                        new_mid = mid - 0.4*normal
                        new_mid_node = mid - 0.8*normal

                    norm_vector = vector / np.linalg.norm(vector)
                    new_start = new_mid - 0.4*norm_vector
                    new_end = new_mid + 0.4*norm_vector
                    ret += f"\\draw[-latexslim] ({new_start[0]:.1f},{new_start[1]:.1f}) to ({new_end[0]:.1f},{new_end[1]:.1f});\n"
                    ret += f"\\node at ({new_mid_node[0]:.1f},{new_mid_node[1]:.1f}) {{${labl}$}};\n"
                
                elif cur_mode in [CUR_MODE_3, CUR_MODE_4, CUR_MODE_5, CUR_MODE_6]:
                    flow_dir = flow_direction[cur_mode-2]
                    ret += f"\\draw ({x1:.1f},{y1:.1f}) to[{comp_circuitikz_type}, f{flow_dir}=${measure_label}$] ({x2:.1f},{y2:.1f});\n" 

            return ret

# NOTE: plot open circuit
        elif type_number == TYPE_OPEN:
            ret = ""

            v_plot_extra = ""
            if not meas_comp_same_direction:
                x1, y1, x2, y2 = x2, y2, x1, y1
                v_plot_extra = "^"
            if measure_type == MEAS_TYPE_VOLTAGE:
                ret += f"\\ctikzset{{american}};\n\\draw ({x1:.1f},{y1:.1f}) to[open, v{v_plot_extra}=${measure_label}$] ({x2:.1f},{y2:.1f});\n\\ctikzset{{european}};\n"
            return ret
        
# NOTE: plot controlled voltage source
        elif type_number in [TYPE_VCVS, TYPE_CCVS]:
            ret = f"\\ctikzset{{american}};\n\\draw ({x1:.1f},{y1:.1f}) to [short, v=${labl}$] ({x2:.1f},{y2:.1f});\n\\ctikzset{{european}};\n\\draw ({x1:.1f},{y1:.1f}) to[cvsource] ({x2:.1f},{y2:.1f});"

            if not meas_comp_same_direction:
                x1, y1, x2, y2 = x2, y2, x1, y1
            if measure_type == MEAS_TYPE_CURRENT:
                flow_dir = flow_direction[np.random.choice(range(4))]
                ret += f"\\draw ({x1:.1f},{y1:.1f}) to[short, f{flow_dir}=${measure_label}$] ({x2:.1f},{y2:.1f});\n"
            
            return ret

# NOTE：plot controlled current source
        elif type_number in [TYPE_VCCS, TYPE_CCCS]:
            ret = f"\\draw ({x1:.1f},{y1:.1f}) to[cisource] ({x2:.1f},{y2:.1f});\n"

            cur_mode_choices = [CUR_MODE_1, CUR_MODE_2] * 10 + [CUR_MODE_3, CUR_MODE_4] * 0 + [CUR_MODE_5, CUR_MODE_6] * 1
            cur_mode = np.random.choice(cur_mode_choices)
            print(f"cur_mode: {cur_mode} when ploting current source")

            if cur_mode == CUR_MODE_1 or cur_mode == CUR_MODE_2:
                mid = np.array([(x1+x2)/2, (y1+y2)/2])
                vector = np.array([x2-x1, y2-y1])
                normal = np.array([-vector[1], vector[0]], dtype=np.float64)
                normal /= np.linalg.norm(normal)
                if cur_mode == CUR_MODE_1:
                    new_mid = mid + 0.6*normal
                    new_mid_node = mid + normal

                else:
                    new_mid = mid - 0.6*normal
                    new_mid_node = mid - normal

                norm_vector = vector / np.linalg.norm(vector)
                new_start = new_mid - 0.4*norm_vector
                new_end = new_mid + 0.4*norm_vector
                ret += f"\\draw[-latexslim] ({new_start[0]:.1f},{new_start[1]:.1f}) to ({new_end[0]:.1f},{new_end[1]:.1f});\n"
                ret += f"\\node at ({new_mid_node[0]:.1f}, {new_mid_node[1]:.1f}) {{${labl}$}};\n"
                
            elif cur_mode in [CUR_MODE_3, CUR_MODE_4, CUR_MODE_5, CUR_MODE_6]:
                flow_dir = flow_direction[cur_mode-2]
                ret += f"\\draw ({x1:.1f},{y1:.1f}) to[cisource, f{flow_dir}=${labl}$] ({x2:.1f},{y2:.1f});\n"

            v_plot_extra = ""
            if not meas_comp_same_direction:
                x1, y1, x2, y2 = x2, y2, x1, y1
                v_plot_extra = "^"
            if measure_type == MEAS_TYPE_VOLTAGE:
                ret += f"\\ctikzset{{american}};\n\\draw ({x1:.1f},{y1:.1f}) to[open, v{v_plot_extra}=${measure_label}$] ({x2:.1f},{y2:.1f});\n\\ctikzset{{european}};\n"
                
            return ret

    elif style == "american":
        pass

    elif style == "european":

        pass

    else:
        raise NotImplementedError
    pass


def get_node_component_draw(x, y,
                            node_type,
                            label,
                            orientation=0,  # 0=up, 1=right, 2=down, 3=left
                            connections=None,  # dict: {base: (x,y), collector: (x,y), emitter: (x,y)}
                            style="chinese",
                            note='v10'
                            ) -> str:
    """
    绘制节点上的元件（三极管、运放等）
    
    参数:
        x, y: 节点元件的Grid位置（用于参考，实际位置根据connections计算）
        node_type: 节点元件类型
        label: 元件标签
        orientation: 朝向 (0=up, 1=right, 2=down, 3=left)
        connections: 连接信息字典
        style: 绘制风格
        note: 版本号
    """
    if node_type == NODE_TYPE_NONE:
        return ""
    
    if style == "chinese":
        node_info = node_components_latex_info[node_type]
        comp_type = node_info[0]
        comp_label_main = node_info[1]

        # orientation的含义：0=up, 1=right, 2=down, 3=left, 转为角度
        orientation_map = {
            0: 90,
            1: 0,
            2: -90,
            3: 180
        }
        
        if node_type == NODE_TYPE_TRANSISTOR_NPN or node_type == NODE_TYPE_TRANSISTOR_PNP:
            if not connections:
                return ""
            
            # 获取三个引脚的坐标
            cx, cy = connections.get('collector', (x, y-1))
            bx, by = connections.get('base', (x-1, y))
            ex, ey = connections.get('emitter', (x, y+1))
            
            # 将节点元件放在网格交点 (x, y) 上，避免漂移到网格外
            tx, ty = x, y

            # orientation优先生效：外部指定角度
            rotation = orientation_map.get(orientation, 90)  # 默认朝上

            # ⚠️兼容旧策略：如orientation未指定(默认0/90°)，允许按实际引脚方向进一步判断/微调
            # （也可仅依据orientation，这里优先支持orientation参数驱动角度）
            
            # 绘制三极管
            ret = f"% NPN/PNP Transistor {comp_label_main}_{{{int(label)}}}\n"
            ret += f"\\node[{comp_type}, rotate={rotation}] ({comp_label_main}{int(label)}) at ({tx:.1f},{ty:.1f}) {{}};\n"

            # 标签方向随朝向，默认在右侧（朝右时），其余方向在适当侧
            label_position = {
                0: "above",   # up
                1: "right",   # right
                2: "below",   # down
                3: "left"     # left
            }
            pos = label_position.get(orientation, "right")
            if orientation == 0:
                dx, dy = 0, 0.5
            elif orientation == 1:
                dx, dy = 0.5, 0
            elif orientation == 2:
                dx, dy = 0, -0.5
            elif orientation == 3:
                dx, dy = -0.5, 0
            else:
                dx, dy = 0.5, 0

            ret += f"\\node[{pos}] at ({tx + dx:.1f},{ty + dy:.1f}) {{${comp_label_main}_{{{int(label)}}}$}};\n"

            # 绘制引脚连线，B、C、E三者分别按节点端口名输出
            # 仍保持正交连接（|-），但引脚实际在tikz的(B)，(C)，(E)
            ret += f"\\draw ({comp_label_main}{int(label)}.B) -- ({bx:.1f},{by:.1f});\n"
            ret += f"\\draw ({comp_label_main}{int(label)}.C) |- ({cx:.1f},{cy:.1f});\n"
            ret += f"\\draw ({comp_label_main}{int(label)}.E) |- ({ex:.1f},{ey:.1f});\n"

            return ret
        
        elif node_type == NODE_TYPE_DIODE:
            # 二极管方向也可用orientation
            orientation_map_d = {
                0: 90,
                1: 0,
                2: -90,
                3: 180
            }
            rotation = orientation_map_d.get(orientation, 0)
            ret = f"% Diode {comp_label_main}_{{{int(label)}}}\n"
            ret += f"\\draw ({x-0.5:.1f},{y:.1f}) to[D, l=${comp_label_main}_{{{int(label)}}}$, rotate={rotation}] ({x+0.5:.1f},{y:.1f});\n"
            return ret

        elif node_type == NODE_TYPE_OPAMP:
            # 运放方向依赖orientation参数
            orientation_map_opamp = {
                0: 90,
                1: 0,
                2: -90,
                3: 180
            }
            rotation = orientation_map_opamp.get(orientation, 0)
            ret = f"% Op Amp {comp_label_main}_{{{int(label)}}}\n"
            ret += f"\\node[op amp, rotate={rotation}] ({comp_label_main}{int(label)}) at ({x:.1f},{y:.1f}) {{}};\n"
            # 标签朝向按朝右(right)，其它与朝向类似，可自定义
            label_position = {
                0: "above",
                1: "right",
                2: "below",
                3: "left"
            }
            pos = label_position.get(orientation, "right")
            if orientation == 0:
                dx, dy = 0, 0.5
            elif orientation == 1:
                dx, dy = 0.5, 0
            elif orientation == 2:
                dx, dy = 0, -0.5
            elif orientation == 3:
                dx, dy = -0.5, 0
            else:
                dx, dy = 0.5, 0
            ret += f"\\node[{pos}] at ({x+dx:.1f},{y+dy:.1f}) {{${comp_label_main}_{{{int(label)}}}$}};\n"
            return ret
        
        else:
            return ""
    
    else:
        raise NotImplementedError



# NOTE: SPICE formatting
SPICE_TEMPLATES = {
    "v4": ".title Active DC Circuit {id}\n{components}\n.END\n",
    "v5": ".title Active DC Circuit\n{components}\n\n{simulation}.END\n",
    "v6": ".title Active DC Circuit\n{components}\n\n{simulation}.END\n",
    "v7": ".title Active DC Circuit\n{components}\n\n{simulation}.END\n",
    "v8": ".title Active DC Circuit\n{components}\n\n{simulation}.END\n",
    "v9": ".title Active DC Circuit\n{components}\n\n{simulation}.END\n",
    "v10": ".title Active DC Circuit\n{components}\n\n{simulation}.end\n",
    "v11": ".title Active DC Circuit\n{components}\n\n{simulation}.end\n",
}
SPICE_PREFFIX = {
    TYPE_RESISTOR: "R",
    TYPE_CAPACITOR: "C",
    TYPE_INDUCTOR: "L",
    TYPE_VOLTAGE_SOURCE: "V",
    TYPE_CURRENT_SOURCE: "I",
    TYPE_VCCS: "G",
    TYPE_VCVS: "E",
    TYPE_CCCS: "F",
    TYPE_CCVS: "H",
    TYPE_OPEN: "",
    TYPE_SHORT: "",
}

class Circuit:

    def __init__(self, m = 3, n = 4, 
                vertical_dis = None, horizontal_dis = None,
                has_vedge = None, has_hedge = None,

                vcomp_type = None, hcomp_type = None,
                vcomp_label = None, hcomp_label = None,             # only support string label
                vcomp_value = None, hcomp_value = None,
                vcomp_value_unit = None, hcomp_value_unit = None,
                vcomp_direction = None, hcomp_direction = None,

                vcomp_measure = None, hcomp_measure = None,
                vcomp_measure_label = None, hcomp_measure_label = None,     # only support string label
                vcomp_measure_direction = None, hcomp_measure_direction = None,

                vcomp_control_meas_label = None, hcomp_control_meas_label = None,     # only support string label  ==> For Controlled Source

                # 节点元件（新增）
                node_comp_type = None,           # 节点元件类型 (m, n)
                node_comp_label = None,          # 节点元件标签 (m, n)
                node_comp_orientation = None,    # 节点元件朝向 (m, n): 0=up, 1=right, 2=down, 3=left
                node_comp_connections = None,    # 节点元件连接信息 (m, n) - dict

                # 交叉点标记（实心圆点）
                junction_marker = None,          # (m, n) 1=显示实心圆点, 0=不显示

                use_value_annotation = False,
                note = "v11",
                id = "",
                label_numerical_subscript = True,
                ):
        self.m = m
        self.n = n
        self.vertical_dis = np.arange(m)*4.0 if vertical_dis is None else vertical_dis
        self.horizontal_dis = np.arange(n)*3.0 if horizontal_dis is None else horizontal_dis

        self.has_vedge = np.ones((m-1, n)) if has_vedge is None else has_vedge # 1 or 0
        self.has_hedge = np.ones((m, n-1)) if has_hedge is None else has_hedge

        self.vcomp_type = np.zeros((m-1, n)) if vcomp_type is None else vcomp_type
        self.hcomp_type = np.zeros((m, n-1)) if hcomp_type is None else hcomp_type
        self.vcomp_label = np.ones((m-1, n)) if vcomp_label is None else vcomp_label
        self.hcomp_label = np.ones((m, n-1)) if hcomp_label is None else hcomp_label
        self.vcomp_value = np.zeros((m-1, n)) if vcomp_value is None else vcomp_value
        self.hcomp_value = np.zeros((m, n-1)) if hcomp_value is None else hcomp_value
        self.vcomp_value_unit = np.zeros((m-1, n)) if vcomp_value_unit is None else vcomp_value_unit
        self.hcomp_value_unit = np.zeros((m, n-1)) if hcomp_value_unit is None else hcomp_value_unit

        self.vcomp_direction = np.zeros((m-1, n)) if vcomp_direction is None else vcomp_direction # 0: n1==>n2, 1: n2==>n1
        self.hcomp_direction = np.zeros((m, n-1)) if hcomp_direction is None else hcomp_direction # 0: n1==>n2, 1: n2==>n1

        self.vcomp_measure = np.zeros((m-1, n)) if vcomp_measure is None else vcomp_measure
        self.hcomp_measure = np.zeros((m, n-1)) if hcomp_measure is None else hcomp_measure

        self.vcomp_measure_label = np.zeros((m-1, n)) if vcomp_measure_label is None else vcomp_measure_label
        self.hcomp_measure_label = np.zeros((m, n-1)) if hcomp_measure_label is None else hcomp_measure_label

        self.vcomp_measure_direction = np.zeros((m-1, n)) if vcomp_measure_direction is None else vcomp_measure_direction
        self.hcomp_measure_direction = np.zeros((m, n-1)) if hcomp_measure_direction is None else hcomp_measure_direction

        self.vcomp_control_meas_label = np.zeros((m-1, n)) if vcomp_control_meas_label is None else vcomp_control_meas_label
        self.hcomp_control_meas_label = np.zeros((m, n-1)) if hcomp_control_meas_label is None else hcomp_control_meas_label

        # 节点元件属性初始化
        self.node_comp_type = np.zeros((m, n), dtype=int) if node_comp_type is None else node_comp_type
        self.node_comp_label = np.zeros((m, n), dtype=int) if node_comp_label is None else node_comp_label
        self.node_comp_orientation = np.zeros((m, n), dtype=int) if node_comp_orientation is None else node_comp_orientation  # 0=up, 1=right, 2=down, 3=left
        # node_comp_connections是一个字典矩阵，每个元素是一个dict或None
        if node_comp_connections is None:
            self.node_comp_connections = np.empty((m, n), dtype=object)
            for i in range(m):
                for j in range(n):
                    self.node_comp_connections[i][j] = None
        else:
            self.node_comp_connections = node_comp_connections

        # 交叉点标记：1=显示实心圆点（导线连接处），0=不显示
        self.junction_marker = np.zeros((m, n), dtype=int) if junction_marker is None else junction_marker

        self.use_value_annotation = use_value_annotation # MEAS: True: annotate value in the figure / False: annotate label in the figure

        self.latex_font_size = "\\large"

        if self.use_value_annotation:
            self.label_numerical_subscript = True
        else:
            self.label_numerical_subscript = label_numerical_subscript

        
        self.note = note
        self.id = id

        self._init_degree() # initialize degree
        self._check_circuit_valid_by_degree() # check if the circuit is valid via degree
        self._init_netlist() # init netlist, and check if the circuit is valid by the topology

    def _init_degree(self):
        self.degree = np.zeros((self.m, self.n))
        # 1. 计算边上元件对节点度数的贡献
        for i in range(self.m):
            for j in range(self.n):
                # 如果当前节点不是最左侧，检查左边的水平边是否存在且不是开路
                if j > 0:
                    self.degree[i][j] += (self.has_hedge[i][j-1] and self.hcomp_type[i][j-1] != TYPE_OPEN)
                # 如果当前节点不是最右侧，检查右边的水平边是否存在且不是开路
                if j < self.n-1:
                    self.degree[i][j] += (self.has_hedge[i][j] and self.hcomp_type[i][j] != TYPE_OPEN)
                # 如果当前节点不是最上侧，检查上边的竖直边是否存在且不是开路
                if i > 0:
                    self.degree[i][j] += (self.has_vedge[i-1][j] and self.vcomp_type[i-1][j] != TYPE_OPEN)
                # 如果当前节点不是最下侧，检查下边的竖直边是否存在且不是开路
                if i < self.m-1:
                    self.degree[i][j] += (self.has_vedge[i][j] and self.vcomp_type[i][j] != TYPE_OPEN)

        # 2. 计算节点元件（三极管等）对度数的贡献
        for i in range(self.m):
            for j in range(self.n):
                if self.node_comp_type[i][j] != NODE_TYPE_NONE:
                    connections = self.node_comp_connections[i][j]
                    if connections:
                        # 三极管等多端元件：每个引脚连接增加对应节点的度数
                        for pin_name, (px, py) in connections.items():
                            # 根据坐标找到对应的grid位置
                            target_i, target_j = self._coord_to_grid(px, py)
                            if target_i is not None and target_j is not None:
                                self.degree[target_i][target_j] += 1

        self._degree_init = True
    
    def _coord_to_grid(self, x, y):
        """根据坐标查找对应的grid位置 (i, j)"""
        for i in range(self.m):
            for j in range(self.n):
                if abs(self.horizontal_dis[j] - x) < 0.01 and abs(self.vertical_dis[i] - y) < 0.01:
                    return i, j
        return None, None
    
    def _count_edges(self, i, j):
        """计算节点 (i,j) 有几条短路边"""
        m, n = self.m, self.n
        count = 0
        # 上边
        if i > 0 and self.has_vedge[i-1][j] :
            count += 1
        # 下边
        if i < m-1 and self.has_vedge[i][j] :
            count += 1
        # 左边
        if j > 0 and self.has_hedge[i][j-1] :
            count += 1
        # 右边
        if j < n-1 and self.has_hedge[i][j] :
            count += 1
        return count

    def _is_4way_crossing(self, i, j):
        """判断节点 (i,j) 是否是四向交叉点（有4条短路边）"""
        return self._count_edges(i, j) == 4

    def _can_turn_at(self, i, j):
        """
        判断在节点 (i,j) 是否可以拐弯
        - 四向交叉点：只有有圆点（junction_marker=1）才能拐弯
        - 其他节点（三向、两向等）：默认可以拐弯
        """
        if self._is_4way_crossing(i, j):
            return self.junction_marker[i][j] == 1
        return True  # 非四向交叉点默认可以拐弯

    def _is_x_node(self, i, j):
        """判断节点 (i,j) 是否是 x 节点（无圆点的四向交叉点）"""
        return self._is_4way_crossing(i, j) and self.junction_marker[i][j] == 0
    
    def _get_grid_nodes(self):
        """
        使用 BFS 生成电路网格中的等价节点。
        
        规则：
        - 四向交叉点无圆点（x节点）：不能拐弯，只能直穿，标记为 x（值 -1）
        - 四向交叉点有圆点：可以拐弯，正常节点编号
        - 三向/两向节点：默认可以拐弯
        - x 节点在水平/垂直方向上分别属于不同的等价组
        
        返回：
        - grid_nodes: 二维数组，每个元素为等价节点编号（整数），x 节点为 -1
        
        副作用：
        - self.x_node_groups: 记录每个 x 节点在水平/垂直方向上属于哪个等价组
          格式: {(i,j): {'horizontal': group_id, 'vertical': group_id}}
        """
        from collections import deque
        
        m, n = self.m, self.n
        # -2 表示未访问，-1 表示 x 节点
        grid_nodes = np.full((m, n), -2, dtype=int)
        
        # 预标记所有 x 节点（无圆点的四向交叉点）
        x_nodes = set()
        for i in range(m):
            for j in range(n):
                if self._is_x_node(i, j):
                    x_nodes.add((i, j))
                    grid_nodes[i][j] = -1  # 标记为 x
        
        # 记录 x 节点在各方向上的等价组号
        self.x_node_groups = {pos: {} for pos in x_nodes}
        
        # 方向定义：'up', 'down', 'left', 'right'
        # 对应移动：(-1,0), (1,0), (0,-1), (0,1)
        directions = {
            'up': (-1, 0),
            'down': (1, 0),
            'left': (0, -1),
            'right': (0, 1)
        }
        opposite = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}
        
        def has_short_edge(i, j, direction):
            """检查从 (i,j) 往 direction 方向是否有短路边"""
            if direction == 'up':
                return i > 0 and self.has_vedge[i-1][j] and self.vcomp_type[i-1][j] == TYPE_SHORT
            elif direction == 'down':
                return i < m-1 and self.has_vedge[i][j] and self.vcomp_type[i][j] == TYPE_SHORT
            elif direction == 'left':
                return j > 0 and self.has_hedge[i][j-1] and self.hcomp_type[i][j-1] == TYPE_SHORT
            elif direction == 'right':
                return j < n-1 and self.has_hedge[i][j] and self.hcomp_type[i][j] == TYPE_SHORT
            return False
        
        def get_allowed_directions(i, j, from_dir):
            """
            获取从 (i,j) 可以扩展的方向
            from_dir: 进入该节点的方向（从哪个方向来的），None 表示起点
            """
            all_dirs = ['up', 'down', 'left', 'right']
            
            if from_dir is None:
                # 起点：可以往任意有边的方向
                return [d for d in all_dirs if has_short_edge(i, j, d)]
            
            if (i, j) in x_nodes:
                # x 节点：只能继续同方向（直穿）
                # from_dir 是"来的方向"，需要继续"去的方向"
                # 如果从 up 来，说明从上方进入，应该继续往 down 去
                continue_dir = opposite[from_dir]
                if has_short_edge(i, j, continue_dir):
                    return [continue_dir]
                return []
            
            if self._can_turn_at(i, j):
                # 可以拐弯：往任意有边的方向
                return [d for d in all_dirs if has_short_edge(i, j, d)]
            else:
                # 不能拐弯（理论上不会到这里，因为 x 节点已经处理了）
                continue_dir = opposite[from_dir]
                if has_short_edge(i, j, continue_dir):
                    return [continue_dir]
                return []
        
        components = []
        node_id = 0
        
        # BFS 遍历
        for start_i in range(m):
            for start_j in range(n):
                # 跳过已访问的节点和 x 节点（x 节点不作为起点）
                if grid_nodes[start_i][start_j] != -2:
                    continue
                
                # 开始新的等价组
                component = []
                queue = deque()
                queue.append((start_i, start_j, None))  # (i, j, from_direction)
                
                while queue:
                    i, j, from_dir = queue.popleft()
                    
                    if (i, j) in x_nodes:
                        # x 节点：记录该方向属于当前等价组，然后继续穿透
                        if (i, j) not in component:
                            component.append((i, j))
                        
                        # 根据来向确定方向类型（水平/垂直）
                        if from_dir in ['left', 'right']:
                            dir_type = 'horizontal'
                        else:  # 'up', 'down'
                            dir_type = 'vertical'
                        
                        # 记录 x 节点在该方向上属于当前等价组
                        self.x_node_groups[(i, j)][dir_type] = node_id
                        
                        # 获取可以继续的方向（只能直穿）
                        allowed = get_allowed_directions(i, j, from_dir)
                        for d in allowed:
                            di, dj = directions[d]
                            ni, nj = i + di, j + dj
                            if 0 <= ni < m and 0 <= nj < n:
                                # x 节点可以被多次穿过，所以不检查 visited
                                queue.append((ni, nj, opposite[d]))
                    else:
                        # 普通节点
                        if grid_nodes[i][j] != -2:
                            continue  # 已访问
                        
                        grid_nodes[i][j] = node_id
                        component.append((i, j))
                        
                        # 获取可以扩展的方向
                        allowed = get_allowed_directions(i, j, from_dir)
                        for d in allowed:
                            di, dj = directions[d]
                            ni, nj = i + di, j + dj
                            if 0 <= ni < m and 0 <= nj < n:
                                queue.append((ni, nj, opposite[d]))
                
                if component:
                    components.append(component)
                    node_id += 1
        
        # x 节点最终赋值：取所属等价组中的任意一个编号（这里取第一个经过它的）
        # 实际上 x 节点在 component 中已经记录，可以属于多个组
        # 但 grid_nodes 只能存一个值，保持 -1 表示特殊

        print(f"components: {components}")
        print(f"x_nodes: {x_nodes}")
        
        # 为 x 节点未记录的方向分配新的独立节点号
        # 检查 x 节点在各方向是否有边（元件边也算）
        for (xi, xj) in x_nodes:
            # 检查水平方向是否有边
            has_h_edge = (xj > 0 and self.has_hedge[xi][xj-1]) or (xj < n-1 and self.has_hedge[xi][xj])
            # 检查垂直方向是否有边
            has_v_edge = (xi > 0 and self.has_vedge[xi-1][xj]) or (xi < m-1 and self.has_vedge[xi][xj])
            
            # 如果有水平边但没有记录水平方向，分配新节点号
            if has_h_edge and 'horizontal' not in self.x_node_groups[(xi, xj)]:
                self.x_node_groups[(xi, xj)]['horizontal'] = node_id
                node_id += 1
            
            # 如果有垂直边但没有记录垂直方向，分配新节点号
            if has_v_edge and 'vertical' not in self.x_node_groups[(xi, xj)]:
                self.x_node_groups[(xi, xj)]['vertical'] = node_id
                node_id += 1
        
        print(f"x_node_groups: {self.x_node_groups}")
        self.nodes = [f"{i}" for i in range(node_id)]
        
        return grid_nodes
    
    def _check_conflict_component_measure(self, comp_type, comp_measure):
        conflict_pairs = [
            (TYPE_SHORT, MEAS_TYPE_VOLTAGE),
            (TYPE_OPEN, MEAS_TYPE_CURRENT),
            (TYPE_VOLTAGE_SOURCE, MEAS_TYPE_VOLTAGE),
            (TYPE_VCVS, MEAS_TYPE_VOLTAGE),
            (TYPE_CCVS, MEAS_TYPE_VOLTAGE),
            (TYPE_CURRENT_SOURCE, MEAS_TYPE_CURRENT),
            (TYPE_VCCS, MEAS_TYPE_CURRENT),
            (TYPE_CCCS, MEAS_TYPE_CURRENT),
        ]
        for pair in conflict_pairs:
            if comp_type == pair[0] and comp_measure == pair[1]:
                return True
        return False

    def init_netlist(self):
        return self._init_netlist()

    def _get_node_name(self, i, j, direction):
        """
        获取格点 (i, j) 在指定方向上的节点名称。
        
        Args:
            i, j: 格点坐标
            direction: 'horizontal' 或 'vertical'，表示边的方向
            
        Returns:
            节点名称字符串
        """
        if self.grid_nodes[i][j] == -1:
            # x 节点：根据方向查找对应的等价组号
            # 所有 x 节点的方向都应该已经在 _get_grid_nodes 中被分配了节点号
            return f"{self.x_node_groups[(i, j)][direction]}"
        else:
            return f"{int(self.grid_nodes[i][j])}"

    def _init_netlist(self):
        """
        初始化电路网表（netlist）。
        节点列表: self.nodes
        支路列表: self.branches（支路字典，包含节点、类型、标签、值等信息）

        步骤如下：
        1. 初始化节点与支路列表；
        2. 生成所有格点的等价节点（self.grid_nodes）；
        3. 遍历所有格点，查找横向/纵向有连线的位置，并对每条有效支路生成支路描述；
        4. 校验支路的物理合法性（如短路、度量类型冲突等）；
        5. 对受控源，保证其仅与唯一电压测量支路关联。
        """

        assert self._degree_init, "degree not initialized"

        self.nodes = []
        self.branches = []

        # 生成格点网络节点，标识每个格点所属的等价节点编号
        self.grid_nodes = self._get_grid_nodes()
        print(f"Grid Nodes:\n{self.grid_nodes}\n\n")

        # 输出横/纵组件类型与存在性调试信息
        print("self.hcomp_type: \n", self.hcomp_type)
        print("self.has_hedge: \n", self.has_hedge)

        add_order = 0
        # 遍历电路网格中的每一个格点
        for i in range(self.m):
            for j in range(self.n):
                # 低编号笔记（非10*10及以上模板）暂未实现
                if int(self.note[1:]) <= 9:
                    raise NotImplementedError
                # 10*10及以上模板实现如下
                elif int(self.note[1:]) > 9:
                    print(f"({i}, {j}) / ({self.m}, {self.n})")
                    # 处理横向支路
                    if j < self.n-1 and self.has_hedge[i][j]:
                        print(f"({i}, {j}) has hedge")
                        # 检查不可出现的断路
                        assert self.hcomp_type[i][j] != TYPE_OPEN, f"open circuit should not be in the netlist, {self.hcomp_type[i][j]}"
                        # 获取实际节点名（考虑 x 节点的方向）
                        n1 = self._get_node_name(i, j, 'horizontal')
                        n2 = self._get_node_name(i, j+1, 'horizontal')
                        # 若两侧节点等价且该横向不是短路，则电路非法（组件被短路）
                        if n1 == n2:
                            if self.hcomp_type[i][j] != TYPE_SHORT:
                                print("invalid circuit, some components are shorted")
                                self.valid = False
                                return False
                            # 短路边连接同一节点，不添加（但不用 continue，继续处理垂直边）
                        else:
                            if self.hcomp_direction[i][j]:
                                n1, n2 = n2, n1
                            # 构造支路信息
                            new_branch = {
                                "n1": n1,
                                "n2": n2,
                                "type": self.hcomp_type[i][j],
                                "label": self.hcomp_label[i][j],
                                "value": self.hcomp_value[i][j],
                                "value_unit": self.hcomp_value_unit[i][j],
                                "measure": self.hcomp_measure[i][j],
                                "measure_label": self.hcomp_measure_label[i][j],
                                "meas_comp_same_direction": self.hcomp_measure_direction[i][j] == self.hcomp_direction[i][j],
                                "control_measure_label": self.hcomp_control_meas_label[i][j],
                                "info": "",
                                "order": add_order
                            }

                            # 调试信息（仅用于特定位置，可删除或注释）
                            if i == 1 and j == 1:
                                print(f"new_branch: {new_branch} on [1, 1]")

                            # 校验类型与度量类型冲突
                            if self._check_conflict_component_measure(self.hcomp_type[i][j], self.hcomp_measure[i][j]):
                                print("invalid circuit, conflict between component type and measure type")
                                self.valid = False
                                return False
                            # 合法支路加入列表
                            self.branches.append(new_branch)
                            add_order += 1

                    # 处理纵向支路
                    if i < self.m-1 and self.has_vedge[i][j]:
                        print(f"({i}, {j}) has vedge")
                        # 获取实际节点名（考虑 x 节点的方向）
                        n1 = self._get_node_name(i, j, 'vertical')
                        n2 = self._get_node_name(i+1, j, 'vertical')
                        # 若上下节点等价且该纵向不是短路，则电路非法
                        if n1 == n2:
                            if self.vcomp_type[i][j] != TYPE_SHORT:
                                print("invalid circuit, some components are shorted")
                                self.valid = False
                                return False
                            # 短路边连接同一节点，不添加
                        else:   # 不等价节点的边
                            if self.vcomp_direction[i][j]:
                                n1, n2 = n2, n1
                            new_branch = {
                                "n1": n1,
                                "n2": n2,
                                "type": self.vcomp_type[i][j],
                                "label": self.vcomp_label[i][j],
                                "value": self.vcomp_value[i][j],
                                "value_unit": self.vcomp_value_unit[i][j],
                                "measure": self.vcomp_measure[i][j],
                                "measure_label": self.vcomp_measure_label[i][j],
                                "meas_comp_same_direction": self.vcomp_measure_direction[i][j] == self.vcomp_direction[i][j],
                                "control_measure_label": self.vcomp_control_meas_label[i][j],
                                "info": "",
                                "order": add_order
                            }
                            # 校验类型与度量类型冲突
                            if self._check_conflict_component_measure(self.vcomp_type[i][j], self.vcomp_measure[i][j]):
                                print("invalid circuit, conflict between component type and measure type")
                                self.valid = False
                                return False

                            self.branches.append(new_branch)
                            add_order += 1

        # 处理节点元件（三极管等多端元件）
        for i in range(self.m):
            for j in range(self.n):
                if self.node_comp_type[i][j] != NODE_TYPE_NONE:
                    node_type = self.node_comp_type[i][j]
                    connections = self.node_comp_connections[i][j]
                    
                    if node_type in [NODE_TYPE_TRANSISTOR_NPN, NODE_TYPE_TRANSISTOR_PNP]:
                        # 三极管支路：获取各引脚连接的等价节点
                        base_node, collector_node, emitter_node = None, None, None
                        
                        # 根据三极管朝向确定引脚连接方向
                        # orientation: 0=up, 1=right, 2=down, 3=left（base 指向的方向）
                        orientation = self.node_comp_orientation[i][j]
                        # base 方向：0/2 为垂直，1/3 为水平
                        # collector/emitter 方向与 base 垂直
                        base_dir = 'vertical' if orientation in [0, 2] else 'horizontal'
                        ce_dir = 'horizontal' if orientation in [0, 2] else 'vertical'
                        
                        if connections:
                            if 'base' in connections:
                                bi, bj = self._coord_to_grid(*connections['base'])
                                if bi is not None:
                                    base_node = self._get_node_name(bi, bj, base_dir)
                            if 'collector' in connections:
                                ci, cj = self._coord_to_grid(*connections['collector'])
                                if ci is not None:
                                    collector_node = self._get_node_name(ci, cj, ce_dir)
                            if 'emitter' in connections:
                                ei, ej = self._coord_to_grid(*connections['emitter'])
                                if ei is not None:
                                    emitter_node = self._get_node_name(ei, ej, ce_dir)
                        
                        new_branch = {
                            "type": node_type,
                            "label": self.node_comp_label[i][j],
                            "base_node": base_node,
                            "collector_node": collector_node,
                            "emitter_node": emitter_node,
                            "orientation": self.node_comp_orientation[i][j],
                            "is_node_component": True,  # 标记为节点元件
                            "order": add_order
                        }
                        self.branches.append(new_branch)
                        add_order += 1
                        print(f"Added transistor branch: {new_branch}")

        # 校验：受控源对应的控制量支路（电压型）仅唯一一条，否则电路非法
        # 注意：跳过节点元件（三极管等）和非受控源元件的校验
        for br in self.branches:
            if br.get('is_node_component', False):
                continue  # 跳过节点元件
            # 只检查受控源元件
            if br.get('type') not in [TYPE_VCCS, TYPE_VCVS, TYPE_CCCS, TYPE_CCVS]:
                continue
            if br.get('control_measure_label', -1) == -1 or br.get('control_measure_label', 0) == 0:
                continue  # 没有控制标签的跳过
            tmp = [(b['n1'], b['n2']) for b in self.branches if not b.get('is_node_component', False) and b.get('measure_label') == br['control_measure_label'] and b.get('measure') == MEAS_TYPE_VOLTAGE]
            if len(tmp) != 1:
                print(f"Controlled Source should have one and only one voltage measurement, but got {len(tmp)}, {br['control_measure_label']}")
                self.valid = False
                return False

        # TODO: 可扩展新检验：并联多电压源，或串联多电流源等可能不合法图结构

        print(f"init netlist done, get branches: {self.branches}")
        return True
        pass

    def _to_SPICE(self):
        """
        example in OP:
        .title Active DC Circuit
        R1 1 2 4k
        R2 3 2 4k
        R3 1 NR3 2k
        VI NR3 0 0
        R4 3 0 3k
        VS1 1 3 25
        IS1 3 2 3m
        IS2 0 1 10m
        IS3 0 2 5m

        .control
        op
        print I(vi)
        * print v(1,2)
        .endc
        .end
        """
        spice_str = ""

        # NOTE: Element Card
        if int(self.note[1:]) <= 9:
            raise NotImplementedError
        elif int(self.note[1:]) > 9:
            sorted_branches = sorted(self.branches, key=lambda x: x["order"])
            for br in sorted_branches:
                # 处理节点元件（三极管等）
                if br.get('is_node_component', False):
                    if br["type"] in [NODE_TYPE_TRANSISTOR_NPN, NODE_TYPE_TRANSISTOR_PNP]:
                        # 三极管SPICE格式: Q<name> <collector> <base> <emitter> <model>
                        model_name = "NPN_MODEL" if br["type"] == NODE_TYPE_TRANSISTOR_NPN else "PNP_MODEL"
                        spice_str += "Q%s %s %s %s %s\n" % (
                            int(br["label"]),
                            br["collector_node"],
                            br["base_node"],
                            br["emitter_node"],
                            model_name
                        )
                    continue  # 跳过后续边上元件的处理
                
                meas_comp_same_direction = br["meas_comp_same_direction"]
                ms_label_str = "" if br["measure_label"] == -1 else str(int(br["measure_label"]))
                ctr_ms_label_str = "" if br["control_measure_label"] == -1 else str(int(br["control_measure_label"])) 

                value_write = str(int(br["value"]))+unit_scales[br["value_unit"]] if self.use_value_annotation else "<Empty>"
                label_write = "" if self.use_value_annotation else str(br["label"])
                # NOTE: For value annotation, the label is not annotated in SPICE;
                #       For label annotation, the value is not annotated in SPICE;

                print(br["type"], br["label"], br["n1"], br["n2"], br["value"], br["value_unit"])
                type_str = SPICE_PREFFIX[br['type']]

                if br["type"] == TYPE_SHORT:
                    # 短路边：只有当有电流测量时才生成 SPICE 元件
                    # 对于连接到 x 节点的短路边（没有电流测量），跳过
                    if br["measure"] != MEAS_TYPE_CURRENT:
                        continue  # 跳过没有电流测量的短路边
                    vmeas_str = f"VI{ms_label_str}"
                    spice_str += "%s %s %s %s\n" % (vmeas_str, br["n1"], br["n2"], 0)
                
                if br["type"] in [TYPE_VOLTAGE_SOURCE, TYPE_CURRENT_SOURCE, TYPE_RESISTOR, TYPE_CAPACITOR, TYPE_INDUCTOR]:
                    if br["measure"] == MEAS_TYPE_CURRENT:
                        mid_node = "N%s%s" % (br['n1'], br['n2'])
                        vmeas_str = f"VI{ms_label_str}"
                        spice_str += "%s%s %s %s %s\n" %  (type_str, label_write,  br["n1"],   mid_node,   value_write)
                        spice_str += "%s %s %s 0\n" %       (vmeas_str,             mid_node,   br["n2"]) if meas_comp_same_direction \
                                else "%s %s %s 0\n" % (vmeas_str, br["n2"], mid_node)
                    else:
                        spice_str += "%s%s %s %s %s\n" %   (type_str, label_write,  br["n1"],   br["n2"],   value_write)

                if br["type"] in [TYPE_CCVS, TYPE_CCCS]:    # 流控电压源、流控电流源

                    tmp = [b for b in self.branches if b['measure_label'] == br['control_measure_label'] and b['measure'] == MEAS_TYPE_CURRENT]
                    assert len(tmp) == 1, "Controlled Source should have one and only one voltage measurement, but got %d, %d" % (len(tmp), br['control_measure_label'])

                    control_measure_str = f"VI{ctr_ms_label_str}"

                    if br["measure"] == MEAS_TYPE_CURRENT:
                        mid_node = "N%s%s" % (br['n1'], br['n2'])
                        vmeas_str = f"VI{ms_label_str}"
                        spice_str += "%s%s %s %s %s %s\n" %  (type_str, label_write,  br["n1"],   mid_node,   control_measure_str,  value_write)
                        spice_str += "%s %s %s 0\n" %       (vmeas_str,             mid_node,   br["n2"]) if meas_comp_same_direction \
                                else "%s %s %s 0\n" % (vmeas_str, br["n2"], mid_node)
                    else:
                        spice_str += "%s%s %s %s %s %s\n" %   (type_str, label_write,  br["n1"],   br["n2"],  control_measure_str,   value_write)
            
                if br["type"] in [TYPE_VCVS, TYPE_VCCS]:    # 压控电压源、压控电流源

                    tmp = [(b['n1'], b['n2']) for b in self.branches if b['measure_label'] == br['control_measure_label'] and b['measure'] == MEAS_TYPE_VOLTAGE]
                    assert len(tmp) == 1, "Controlled Source should have one and only one voltage measurement, but got %d, %d" % (len(tmp), br['control_measure_label'])

                    control_n1, control_n2 = tmp[0]

                    if br["measure"] == MEAS_TYPE_CURRENT:
                        mid_node = "N%s%s" % (br['n1'], br['n2'])
                        vmeas_str = f"VI{ms_label_str}"
                        spice_str += "%s%s %s %s %s %s %s\n" %  (type_str, label_write,  br["n1"],   mid_node,   control_n1,  control_n2,  value_write)
                        spice_str += "%s %s %s 0\n" %       (vmeas_str,             mid_node,   br["n2"]) if meas_comp_same_direction \
                                else "%s %s %s 0\n" % (vmeas_str, br["n2"], mid_node)
                    else:
                        spice_str += "%s%s %s %s %s %s %s\n" %  (type_str, label_write,  br["n1"],   br["n2"],   control_n1,  control_n2,  value_write)

        # NOTE: Control Card
        if int(self.note[1:]) <= 9:
            raise NotImplementedError
        elif int(self.note[1:]) > 9:
            zero_order = True
            for br in self.branches:
                # 跳过节点元件（三极管等）
                if br.get('is_node_component', False):
                    continue
                if br["type"] in [TYPE_CAPACITOR, TYPE_INDUCTOR]:
                    zero_order = False
                    break

            if zero_order:      # 零阶电路
                sim_str = ".control\nop\n"
                for br in self.branches:
                    # 跳过节点元件（三极管等），它们没有 measure_label 等字段
                    if br.get('is_node_component', False):
                        continue
                    
                    if br["measure_label"] == -1:
                        ms_label_str = ""
                    else:
                        ms_label_str = str(int(br["measure_label"]))

                    if br["measure"] == MEAS_TYPE_VOLTAGE:
                        print(f"#n1: {br['n1']}, n2: {br['n2']}")
                        # sim_str += f".PRINT DC V({br['n1']}, {br['n2']}) * measurement of U{br['measure_label']}\n"
                        meas_n1, meas_n2 = br["n1"], br["n2"]
                        if not br["meas_comp_same_direction"]:
                            meas_n1, meas_n2 = meas_n2, meas_n1
                        if str(meas_n1) == '0':
                            sim_str += "print -v(%s) ; measurement of U%s\n" % (meas_n2, ms_label_str)
                        elif str(meas_n2) == '0':
                            sim_str += "print v(%s) ; measurement of U%s\n" % (meas_n1, ms_label_str)
                        else:
                            sim_str += "print v(%s, %s) ; measurement of U%s\n" % (meas_n1, meas_n2, ms_label_str)
                    elif br["measure"] == MEAS_TYPE_CURRENT:
                        print('#')
                        # sim_str += f".PRINT DC V({br['n1']}, {br['n2']}) / (R{br['label']}) * measurement of I{br['measure_label']} : I(R{br['label']})\n"
                        vmeas_str = f"VI{ms_label_str}"
                        sim_str += "print i(%s) ; measurement of I%s\n" % (vmeas_str, ms_label_str)
                sim_str += ".endc\n"
                
                # 检查是否有三极管，添加模型定义
                has_npn = any(br.get('is_node_component') and br.get('type') == NODE_TYPE_TRANSISTOR_NPN for br in self.branches)
                has_pnp = any(br.get('is_node_component') and br.get('type') == NODE_TYPE_TRANSISTOR_PNP for br in self.branches)
                model_str = ""
                if has_npn:
                    model_str += ".MODEL NPN_MODEL NPN\n"
                if has_pnp:
                    model_str += ".MODEL PNP_MODEL PNP\n"
                if model_str:
                    spice_str = model_str + spice_str
                
                print(f"spice_str: {spice_str}, \n\nsim_str: {sim_str}\n\n")
                # exit()
                spice_str = SPICE_TEMPLATES[self.note].format(components=spice_str, simulation=sim_str)   

            else:   # high order circuit (含电容/电感)
                # 使用瞬态分析
                sim_str = ".control\ntran 1u 10m\n"
                sim_str += ".endc\n"
                
                # 检查是否有三极管，添加模型定义
                has_npn = any(br.get('is_node_component') and br.get('type') == NODE_TYPE_TRANSISTOR_NPN for br in self.branches)
                has_pnp = any(br.get('is_node_component') and br.get('type') == NODE_TYPE_TRANSISTOR_PNP for br in self.branches)
                model_str = ""
                if has_npn:
                    model_str += ".MODEL NPN_MODEL NPN\n"
                if has_pnp:
                    model_str += ".MODEL PNP_MODEL PNP\n"
                if model_str:
                    spice_str = model_str + spice_str
                
                print(f"spice_str: {spice_str}, \n\nsim_str: {sim_str}\n\n")
                spice_str = SPICE_TEMPLATES[self.note].format(components=spice_str, simulation=sim_str)        
        else:
            raise NotImplementedError

        return spice_str
        pass

    def _check_circuit_valid_by_degree(self):

        assert self._degree_init, "degree not initialized"

        # 检查电路的每个节点的度数是否合法（所有节点的度数都不能等于1，否则为无效电路）
        self.valid = True
        for i in range(self.m):
            for j in range(self.n):
                if self.degree[i][j] == 1:
                    print("invalid cricuit")
                    self.valid = True
        # TODO: check if there are voltage source in parallel OR current source in series
        if self.valid:
            print("valid circuit")
        else:
            print("invalid circuit")

    def _draw_vertical_edge(self, i, j):
        if ((i>=0 and i<self.m-1) and (j>=0 and j<self.n)) and self.has_vedge[i][j]:
            if int(self.note[1:]) < 9: # <= version 4
                raise NotImplementedError
            else:
                new_line = get_latex_line_draw(self.horizontal_dis[j], self.vertical_dis[i], self.horizontal_dis[j], self.vertical_dis[i+1],
                                                self.vcomp_type[i][j], 
                                                self.vcomp_label[i][j], 
                                                self.vcomp_value[i][j], 
                                                self.vcomp_value_unit[i][j],
                                                self.use_value_annotation,
                                                measure_type=self.vcomp_measure[i][j], 
                                                measure_label=self.vcomp_measure_label[i][j],
                                                measure_direction=self.vcomp_measure_direction[i][j],
                                                direction=self.vcomp_direction[i][j],
                                                label_subscript_type=int(not self.label_numerical_subscript),
                                                control_label=self.vcomp_control_meas_label[i][j],
                                                note=self.note
                                            )
            return new_line
        else:
            return ""
        
    def _draw_horizontal_edge(self, i, j):
        if ((i>=0 and i<self.m) and (j>=0 and j<self.n-1)) and self.has_hedge[i][j]:
            if int(self.note[1:]) < 9: # <= version 4
                raise NotImplementedError
            else:
                new_line = get_latex_line_draw(self.horizontal_dis[j], self.vertical_dis[i], self.horizontal_dis[j+1], self.vertical_dis[i],
                                                self.hcomp_type[i][j], 
                                                self.hcomp_label[i][j], 
                                                self.hcomp_value[i][j],
                                                self.hcomp_value_unit[i][j],
                                                self.use_value_annotation,
                                                measure_type=self.hcomp_measure[i][j], 
                                                measure_label=self.hcomp_measure_label[i][j],
                                                measure_direction=self.hcomp_measure_direction[i][j],
                                                direction=self.hcomp_direction[i][j],
                                                label_subscript_type=int(not self.label_numerical_subscript),
                                                control_label=self.hcomp_control_meas_label[i][j],
                                                note=self.note
                                            )
            return new_line
        else: 
            return ""
        
    def _draw_node_component(self, i, j):
        """绘制节点上的元件（三极管等）"""
        if ((i>=0 and i<self.m) and (j>=0 and j<self.n)) and self.node_comp_type[i][j] != NODE_TYPE_NONE:
            x = self.horizontal_dis[j]
            y = self.vertical_dis[i]
            node_type = self.node_comp_type[i][j]
            label = self.node_comp_label[i][j]
            orientation = self.node_comp_orientation[i][j]
            connections = self.node_comp_connections[i][j]
            
            return get_node_component_draw(x, y, node_type, label, orientation, connections, note=self.note)
        else:
            return ""

    def _draw_junction(self, i, j):
        """绘制交叉点（实心圆点，表示导线连接处）"""
        if ((i>=0 and i<self.m) and (j>=0 and j<self.n)) and self.junction_marker[i][j] == 1:
            x = self.horizontal_dis[j]
            y = self.vertical_dis[i]
            # 使用circuitikz的circ节点绘制实心圆点
            return f"\\node[circ] at ({x:.1f},{y:.1f}) {{}};\n"
        else: 
            return ""
        
    def to_latex(self):
        # with open("./templates/latex_template.txt", "r") as f:
        #     latex_template = f.read()
        if int(self.note[1:]) <= 9:
            raise NotImplementedError
        elif int(self.note[1:]) > 9:
            latex_template = LATEX_TEMPLATES["v9"]
        else:
            raise NotImplementedError
        
        latex_code_main = ""
        # 先绘制所有边上的元件
        for i in range(self.m):
            for j in range(self.n):
                latex_code_main += self._draw_horizontal_edge(i,j)
                latex_code_main += self._draw_vertical_edge(i,j)
        
        # 再绘制所有节点上的元件（确保三极管等在最上层）
        for i in range(self.m):
            for j in range(self.n):
                latex_code_main += self._draw_node_component(i,j)
        
        # 最后绘制交叉点（实心圆点，确保在最顶层）
        for i in range(self.m):
            for j in range(self.n):
                latex_code_main += self._draw_junction(i,j)
        
        latex_code = latex_template.replace("<main>", latex_code_main)
        
        if int(self.note[1:]) >= 8:
            latex_code = latex_code.replace("<font>", self.latex_font_size)

        return latex_code

def gen_circuit(note="v1", id=""):

    ## v1-9 old version
    if int(note[1:]) <= 9:
        raise NotImplementedError
    
    ## v10
    elif int(note[1:]) == 10:

        num_edge_choices = [2]*3 + [3]*5 + [4]*3 + [5]*2 + [6]*1 + [7]*1 + [8]*1
        num_source_choices = [TYPE_VOLTAGE_SOURCE]*5 + [TYPE_CURRENT_SOURCE]*5 + [TYPE_VCCS]*2 + [TYPE_VCVS]*2 + [TYPE_CCCS]*2 + [TYPE_CCVS]*2

        m = np.random.choice(num_edge_choices)
        # n = 3 + np.random.randint(-1, 3)
        n = np.random.choice(num_edge_choices)
        vertical_dis = np.arange(m)* 3 + np.random.uniform(-0.5, 0.5, size=(m,))
        horizontal_dis = np.arange(n)* 3 + np.random.uniform(-0.5, 0.5, size=(n,))

        num_short_max = 0
        # cut_outer_edge_rate = 0.8
        cut_outer_edge_rate = 1
        cut_corner_rate = 0.2

        cut_left_top = random.random()<cut_corner_rate
        cut_left_bottom = random.random()<cut_corner_rate
        cut_right_top = random.random()<cut_corner_rate
        cut_right_bottom = random.random()<cut_corner_rate
        while num_short_max < 1:
            has_vedge = np.random.randint(0, 2, size=(m-1, n)) # 0 or 1
            has_hedge = np.random.randint(0, 2, size=(m, n-1)) # 0 or 1

            for i in range(m-1):
                has_vedge[i][0] = int(random.random() < cut_outer_edge_rate)
                has_vedge[i][n-1] = int(random.random() < cut_outer_edge_rate)
            # has_vedge[:, [0,n-1]] = 1; # left and right
            has_hedge = np.random.randint(0, 2, size=(m, n-1)) # 0 or 1
            for j in range(n-1):
                has_hedge[0][j] = int(random.random() < cut_outer_edge_rate)
                has_hedge[m-1][j] = int(random.random() < cut_outer_edge_rate)
            # has_hedge[[0,m-1], :] = 1; # top and bottom
            
            num_edges = np.sum(has_vedge) + np.sum(has_hedge)
            if num_edges > 8:
                if cut_left_bottom:
                    has_vedge[0][0] = 0
                    has_hedge[0][0] = 0
                if cut_left_top:
                    has_vedge[m-2][0] = 0
                    has_hedge[m-1][0] = 0
                if cut_right_bottom:
                    has_vedge[0][n-1] = 0
                    has_hedge[0][n-2] = 0
                if cut_right_top:
                    has_vedge[m-2][n-1] = 0
                    has_hedge[m-1][n-2] = 0

            idxs_has_vedge = np.where(has_vedge == 1)
            idxs_has_vedge = list(zip(idxs_has_vedge[0], idxs_has_vedge[1]))
            idxs_has_hedge = np.where(has_hedge == 1)
            idxs_has_hedge = list(zip(idxs_has_hedge[0], idxs_has_hedge[1]))
            idxs_edge = [(0, i, j) for i, j in idxs_has_vedge] + [(1, i, j) for i, j in idxs_has_hedge]
            
            num_edges = len(idxs_has_vedge) + len(idxs_has_hedge)
            max_num_source = max(min(5, num_edges // 2 - 1), 1)
            num_sources = np.random.randint(1, max_num_source+1)
            sources = np.random.choice(num_source_choices, num_sources)

            num_volsrs = np.sum(sources == TYPE_VOLTAGE_SOURCE)
            num_cursrs = np.sum(sources == TYPE_CURRENT_SOURCE)
            num_vccs = np.sum(sources == TYPE_VCCS)
            num_vcvs = np.sum(sources == TYPE_VCVS)
            num_cccs = np.sum(sources == TYPE_CCCS)
            num_ccvs = np.sum(sources == TYPE_CCVS)

            num_short_max = (num_edges - num_sources) - 2

        print(f"num_short_max: {num_short_max}")
        print(idxs_edge)
        num_short = np.random.randint(0, num_short_max+1)
        num_open = np.random.randint(0, num_short // 2) if num_short > 2 else 0
        num_r = num_edges - num_sources - num_short  - num_open# Resistor

        np.random.shuffle(idxs_edge)
        idxs_volsrc = idxs_edge[:num_volsrs]
        idxs_cursrc = idxs_edge[num_volsrs:num_volsrs+num_cursrs]
        idxs_vccs = idxs_edge[num_volsrs+num_cursrs:num_volsrs+num_cursrs+num_vccs]
        idxs_vcvs = idxs_edge[num_volsrs+num_cursrs+num_vccs:num_volsrs+num_cursrs+num_vccs+num_vcvs]
        idxs_cccs = idxs_edge[num_volsrs+num_cursrs+num_vccs+num_vcvs:num_volsrs+num_cursrs+num_vccs+num_vcvs+num_cccs]
        idxs_ccvs = idxs_edge[num_volsrs+num_cursrs+num_vccs+num_vcvs+num_cccs:num_sources]
        idxs_r = idxs_edge[num_sources:num_sources+num_r]
        idxs_open = idxs_edge[num_sources+num_r:num_sources+num_r+num_open]

        label_volsrc = np.random.permutation(range(num_volsrs)) + 1
        label_cursrc = np.random.permutation(range(num_cursrs)) + 1
        label_vccs = np.random.permutation(range(num_vccs)) + 1
        label_vcvs = np.random.permutation(range(num_vcvs)) + 1
        label_cccs = np.random.permutation(range(num_cccs)) + 1
        label_ccvs = np.random.permutation(range(num_ccvs)) + 1

        label_r = np.random.permutation(range(num_r)) + 1

        vcomp_type = np.zeros((m-1, n))
        hcomp_type = np.zeros((m, n-1))
        vcomp_label = np.zeros((m-1, n))
        hcomp_label = np.zeros((m, n-1))
        vcomp_value = np.zeros((m-1, n))
        hcomp_value = np.zeros((m, n-1))

        vcomp_value_unit = np.zeros((m-1, n))
        hcomp_value_unit = np.zeros((m, n-1))

        vcomp_direction = np.random.randint(0, 2, size=(m-1, n)) # 0 or 1
        hcomp_direction = np.random.randint(0, 2, size=(m, n-1)) # 0 or 1

        vcomp_measure = np.zeros((m-1, n))
        hcomp_measure = np.zeros((m, n-1))

        vcomp_measure_label = np.zeros((m-1, n))
        hcomp_measure_label = np.zeros((m, n-1))

        vcomp_measure_direction = np.random.randint(0, 2, size=(m-1, n)) # 0 or 1
        hcomp_measure_direction = np.random.randint(0, 2, size=(m, n-1)) # 0 or 1

        vcomp_control_meas_label = np.zeros((m-1, n))   
        hcomp_control_meas_label = np.zeros((m, n-1))
        
        min_value_r, max_value_r = 1, 100
        min_value_v, max_value_v = 1, 100
        min_value_i, max_value_i = 1, 100

        # add measuremaent
        num_measure_choices = list(range(0, num_r+1)) + [0]*5+[1]*5+[2]*2
        num_measure = np.random.choice(num_measure_choices)
        if num_measure > 0:
            num_measure_i = np.random.randint(0, num_measure+1)
            num_measure_v = num_measure - num_measure_i
        else:
            num_measure_i = 0
            num_measure_v = 0
        if num_measure_i < num_cccs + num_ccvs:
            num_measure_i = num_cccs + num_ccvs
        if num_measure_v < num_vccs + num_vcvs:
            num_measure_v = num_vccs + num_vcvs
        num_measure = num_measure_i + num_measure_v

        measure_label_sets = np.random.choice(range(-1, 100), num_measure, replace=False)
        
        idxs_measure_i = random.sample(idxs_edge, num_measure_i)
        idxs_measure_v = random.sample(list(set(idxs_edge) - set(idxs_measure_i)) + (idxs_cursrc), num_measure_v)
    
        for l, (s, i, j) in enumerate(idxs_measure_i):
            if s == 0:
                vcomp_measure[i][j] = MEAS_TYPE_CURRENT
                vcomp_measure_label[i][j] = measure_label_sets[l]
            else:
                hcomp_measure[i][j] = MEAS_TYPE_CURRENT
                hcomp_measure_label[i][j] = measure_label_sets[l]
        for l, (s, i, j) in enumerate(idxs_measure_v):
            if s == 0:
                vcomp_measure[i][j] = MEAS_TYPE_VOLTAGE
                vcomp_measure_label[i][j] = measure_label_sets[l]
            else:
                hcomp_measure[i][j] = MEAS_TYPE_VOLTAGE
                hcomp_measure_label[i][j] = measure_label_sets[l]


        for l, (s, i, j) in enumerate(idxs_open):
            if s == 0:
                vcomp_type[i][j] = TYPE_OPEN
            else:
                hcomp_type[i][j] = TYPE_OPEN

        for l, (s, i, j) in enumerate(idxs_volsrc):
            if s == 0:
                vcomp_type[i][j] = TYPE_VOLTAGE_SOURCE
                vcomp_label[i][j] = label_volsrc[l]
                vcomp_value[i][j] = np.random.randint(min_value_v, max_value_v)
            else:
                hcomp_type[i][j] = TYPE_VOLTAGE_SOURCE
                hcomp_label[i][j] = label_volsrc[l]
                hcomp_value[i][j] = np.random.randint(min_value_v, max_value_v)
        for l, (s, i, j) in enumerate(idxs_cursrc):
            if s == 0:
                vcomp_type[i][j] = TYPE_CURRENT_SOURCE
                vcomp_label[i][j] = label_cursrc[l]
                vcomp_value[i][j] = np.random.randint(min_value_i, max_value_i)
            else:
                hcomp_type[i][j] = TYPE_CURRENT_SOURCE
                hcomp_label[i][j] = label_cursrc[l]
                hcomp_value[i][j] = np.random.randint(min_value_i, max_value_i)
        for l, (s, i, j) in enumerate(idxs_r):
            if s == 0:
                vcomp_type[i][j] = TYPE_RESISTOR
                vcomp_label[i][j] = label_r[l]
                vcomp_value[i][j] = np.random.randint(min_value_r, max_value_r)
            else:
                hcomp_type[i][j] = TYPE_RESISTOR
                hcomp_label[i][j] = label_r[l]
                hcomp_value[i][j] = np.random.randint(min_value_r, max_value_r)
        for l, (s, i, j) in enumerate(idxs_vccs):
            if s == 0:
                vcomp_type[i][j] = TYPE_VCCS
                vcomp_label[i][j] = label_vccs[l]
                vcomp_value[i][j] = np.random.randint(min_value_v, max_value_v)       
            else:
                hcomp_type[i][j] = TYPE_VCCS
                hcomp_label[i][j] = label_vccs[l]
                hcomp_value[i][j] = np.random.randint(min_value_v, max_value_v)
        for l, (s, i, j) in enumerate(idxs_vcvs):
            if s == 0:
                vcomp_type[i][j] = TYPE_VCVS
                vcomp_label[i][j] = label_vcvs[l]
                vcomp_value[i][j] = np.random.randint(min_value_v, max_value_v)
            else:
                hcomp_type[i][j] = TYPE_VCVS
                hcomp_label[i][j] = label_vcvs[l]
                hcomp_value[i][j] = np.random.randint(min_value_v, max_value_v)
        for l, (s, i, j) in enumerate(idxs_cccs):
            if s == 0:
                vcomp_type[i][j] = TYPE_CCCS
                vcomp_label[i][j] = label_cccs[l]
                vcomp_value[i][j] = np.random.randint(min_value_i, max_value_i)
            else:
                hcomp_type[i][j] = TYPE_CCCS
                hcomp_label[i][j] = label_cccs[l]
                hcomp_value[i][j] = np.random.randint(min_value_i, max_value_i)
        for l, (s, i, j) in enumerate(idxs_ccvs):
            if s == 0:
                vcomp_type[i][j] = TYPE_CCVS
                vcomp_label[i][j] = label_ccvs[l]
                vcomp_value[i][j] = np.random.randint(min_value_i, max_value_i)
            else:
                hcomp_type[i][j] = TYPE_CCVS
                hcomp_label[i][j] = label_ccvs[l]
                hcomp_value[i][j] = np.random.randint(min_value_i, max_value_i)

        # 添加控制源
        for l, (s,i,j) in enumerate(idxs_vccs + idxs_vcvs):
            if s == 0:
                control_measure_voltage_idx = random.choice(idxs_measure_v)
                if control_measure_voltage_idx[0] == 0:
                    vcomp_control_meas_label[i][j] = vcomp_measure_label[control_measure_voltage_idx[1]][control_measure_voltage_idx[2]]
                elif control_measure_voltage_idx[0] == 1:
                    vcomp_control_meas_label[i][j] = hcomp_measure_label[control_measure_voltage_idx[1]][control_measure_voltage_idx[2]]
            else:
                control_measure_voltage_idx = random.choice(idxs_measure_v)
                if control_measure_voltage_idx[0] == 0:
                    hcomp_control_meas_label[i][j] = vcomp_measure_label[control_measure_voltage_idx[1]][control_measure_voltage_idx[2]]
                elif control_measure_voltage_idx[0] == 1:
                    hcomp_control_meas_label[i][j] = hcomp_measure_label[control_measure_voltage_idx[1]][control_measure_voltage_idx[2]]
        for l, (s,i,j) in enumerate(idxs_cccs + idxs_ccvs):
            if s == 0:
                control_measure_current_idx = random.choice(idxs_measure_i)
                if control_measure_current_idx[0] == 0:
                    vcomp_control_meas_label[i][j] = vcomp_measure_label[control_measure_current_idx[1]][control_measure_current_idx[2]]
                elif control_measure_current_idx[0] == 1:
                    vcomp_control_meas_label[i][j] = hcomp_measure_label[control_measure_current_idx[1]][control_measure_current_idx[2]]
            else:
                control_measure_current_idx = random.choice(idxs_measure_i)
                if control_measure_current_idx[0] == 0:
                    hcomp_control_meas_label[i][j] = vcomp_measure_label[control_measure_current_idx[1]][control_measure_current_idx[2]]
                elif control_measure_current_idx[0] == 1:
                    hcomp_control_meas_label[i][j] = hcomp_measure_label[control_measure_current_idx[1]][control_measure_current_idx[2]]

        print(f"vcomp_value: {vcomp_value}\n\nhcomp_value: {hcomp_value}")
        print(f"vcomp_value_unit: {vcomp_value_unit}\n\nhcomp_value_unit: {hcomp_value_unit}")

        unit_choices = [UNIT_MODE_1]*10 + [UNIT_MODE_k]*4 + [UNIT_MODE_m]*2
        vcomp_value_unit = np.random.choice(unit_choices, size=(m-1, n))
        hcomp_value_unit = np.random.choice(unit_choices, size=(m, n-1))
        
        # use_value_annotation = False
        use_value_annotation = bool(random.getrandbits(1))
        # label_str_subscript = bool(random.getrandbits(1)) & ~use_value_annotation
        label_str_subscript = False
        label_numerical_subscript = not label_str_subscript

        # Convert all matrix to int
        vcomp_type = vcomp_type.astype(int)
        hcomp_type = hcomp_type.astype(int)
        vcomp_label = vcomp_label.astype(int)
        hcomp_label = hcomp_label.astype(int)
        vcomp_value = vcomp_value.astype(int)
        hcomp_value = hcomp_value.astype(int)
        vcomp_value_unit = vcomp_value_unit.astype(int)
        hcomp_value_unit = hcomp_value_unit.astype(int)

        vcomp_measure = vcomp_measure.astype(int)
        hcomp_measure = hcomp_measure.astype(int)
        vcomp_measure_label = vcomp_measure_label.astype(int)
        hcomp_measure_label = hcomp_measure_label.astype(int)
        vcomp_measure_direction = vcomp_measure_direction.astype(int)
        hcomp_measure_direction = hcomp_measure_direction.astype(int)
        vcomp_control_meas_label = vcomp_control_meas_label.astype(int)
        hcomp_control_meas_label = hcomp_control_meas_label.astype(int)

        print("#"*100)
        print("Generate a random grid for circuit ... ")
        print(f"has_vedge: {has_vedge}\n\nhas_hedge: {has_hedge}")
        print(f"vertical_dis: {vertical_dis}\n\nhorizontal_dis: {horizontal_dis}")
        print(f"m:{m}, n:{n}\n\nnum_edges:{num_edges},\nnum_sources: {num_sources},\nnum_volsrs: {num_volsrs},\nnum_cursrs: {num_cursrs}\nnum_resistors: {num_r}")
        print(f"use_value_annotation: {use_value_annotation}\nlabel_numerical_subscript: {label_numerical_subscript}")

        print(f"vcomp_type: {vcomp_type}\n\nhcomp_type: {hcomp_type}")
        print(f"vcomp_label: {vcomp_label}\n\nhcomp_label: {hcomp_label}")
        print(f"vcomp_value: {vcomp_value}\n\nhcomp_value: {hcomp_value}")
        print(f"vcomp_value_unit: {vcomp_value_unit}\n\nhcomp_value_unit: {hcomp_value_unit}")
        print(f"vcomp_measure: {vcomp_measure}\n\nhcomp_measure: {hcomp_measure}")
        print(f"vcomp_measure_label: {vcomp_measure_label}\n\nhcomp_measure_label: {hcomp_measure_label}")
        print(f"vcomp_measure_direction: {vcomp_measure_direction}\n\nhcomp_measure_direction: {hcomp_measure_direction}")
        print(f"vcomp_control_meas_label: {vcomp_control_meas_label}\n\nhcomp_control_meas_label: {hcomp_control_meas_label}")

        # print(f"Generating a circuit grid of size {m}x{n} with {num_volsrs} voltage sources, {num_cursrs} current sources, and {num_r} resistors.")
        circ = Circuit( m=m, n=n, \
                        vertical_dis=vertical_dis, horizontal_dis=horizontal_dis, \
                        has_vedge=has_vedge, has_hedge=has_hedge, \
                        vcomp_type=vcomp_type, hcomp_type=hcomp_type, \
                        vcomp_label=vcomp_label, hcomp_label=hcomp_label, \
                        vcomp_value=vcomp_value, hcomp_value=hcomp_value, \
                        vcomp_value_unit=vcomp_value_unit, hcomp_value_unit=hcomp_value_unit, \
                        vcomp_measure=vcomp_measure, hcomp_measure=hcomp_measure, \
                        vcomp_measure_label=vcomp_measure_label, hcomp_measure_label=hcomp_measure_label, \
                        use_value_annotation=use_value_annotation, note=note, id=id,
                        vcomp_direction=vcomp_direction, hcomp_direction=hcomp_direction,
                        vcomp_measure_direction=vcomp_measure_direction, hcomp_measure_direction=hcomp_measure_direction,
                        vcomp_control_meas_label=vcomp_control_meas_label, hcomp_control_meas_label=hcomp_control_meas_label,
                        label_numerical_subscript=label_numerical_subscript)    # whether use numerical subscript for label
    
    elif int(note[1:]) == 11:

        # 为什么要有不同的权重？在生成电路网格（即电路节点行/列数）的过程中，不同规模的网格对应着不同复杂度和多样性。通常来说，过小的网格（如2x2）表达能力有限，实际意义不大；而过大的网格（如7x7、8x8）虽然复杂，但样本占比过高会导致整体数据分布极度倾斜、不均衡，且在训练/测试时也会引发资源消耗和难以泛化等问题。因此，设计时通过“权重”来人为控制各个网格维数在最终样本中的采样概率，以便样本更均匀、更贴合实际需求。

        # 采样流程详细说明如下：
        # 1. 准备一个列表num_grid_options，这个列表列举了所有可能允许采样的网格维数，比如从2到8。
        # 2. 为每个维数分配权重（num_grid_dis）。权重越大，代表这个维数被选中的概率越高。例如：
        #    num_grid_options = [2, 3, 4, 5, 6, 7, 8]
        #    num_grid_dis     = [3, 6, 6, 2, 1, 0, 0]
        #    其中 3 和 4 的权重最高（6），2和5偏低（3、2），6仅有1，其余两个为0（即不会采样到）。
        # 3. 根据这些权重，将每个维数按照权重重复次数“展开”为一个一维的大列表num_grid_choices。例如3重复6次、4重复6次。
        # 4. 用np.random.choice(num_grid_choices)进行采样时，由于某个数字在num_grid_choices中出现多次，被采到的概率就更高，实现了加权随机采样。
        #
        # 举个例子，num_grid_choices最终为[2,2,2,3,3,3,3,3,3,4,4,4,4,4,4,5,5,6]，此时采样到3或4的概率分别为6/18，采样到6的概率为1/18。
        # 这种方式比直接用np.random.choice(num_grid_options, p=权重归一化)代码实现更直观，也方便之后直接做enumerate和计数等处理。
        # 网格采样：按权重重复方式构造 choices，再用 np.random.choice 实现加权随机
        num_grid_options = [2, 3, 4, 5, 6, 7, 8]
        num_grid_dis = [3, 6, 6, 2, 1, 0, 0]
        num_grid_choices = []
        for op, dis in zip(num_grid_options, num_grid_dis):
            num_grid_choices += [op]*dis
 
        # 组件类型加权分布（内/外层；外层不含开路），控制短路/源/受控源频次
        num_comp_dis = [10, 5, 5, 20, 0, 0, 5, 2, 2, 2, 2]  # Short, V, I, R, C, L, Open, VCCS, VCVS, CCCS, CCVS
        num_comp_dis_outer = [10, 5, 5, 20, 0, 0, 0, 2, 2, 2, 2]    # in the outer loop: no <open>
        num_comp_choices = []
        num_comp_choices_outer = []
        for op, dis in zip(range(11), num_comp_dis):
            num_comp_choices += [op]*dis
        for op, dis in zip(range(11), num_comp_dis_outer):
            num_comp_choices_outer += [op]*dis
        
        vertical_dis_mean, vertical_dis_std = 3, 0.5
        horizontal_dis_mean, horizontal_dis_std = 3, 0.5

        comp_mean_value = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # 数值下界
        comp_max_value = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]

        unit_dis = [10, 4, 2]
        unit_choices = [UNIT_MODE_1]*unit_dis[0] + [UNIT_MODE_k]*unit_dis[1] + [UNIT_MODE_m]*unit_dis[2]

        meas_dis = [10, 1, 1]
        meas_choices = [MEAS_TYPE_NONE]*meas_dis[0] + [MEAS_TYPE_VOLTAGE]*meas_dis[1] + [MEAS_TYPE_CURRENT]*meas_dis[2]
        meas_dir_prob = 0.5

        meas_label_choices = range(-1, 10)

        use_value_annotation_prob = 0.8

        # 采样网格尺寸并添加坐标抖动
        m = np.random.choice(num_grid_choices)
        n = np.random.choice(num_grid_choices)
        vertical_dis = np.arange(m)* vertical_dis_mean + np.random.uniform(-vertical_dis_std, vertical_dis_std, size=(m,))
        horizontal_dis = np.arange(n)* horizontal_dis_mean + np.random.uniform(-horizontal_dis_std, horizontal_dis_std, size=(n,))

        while True:

            # 初始化全连通；后续开路/冲突会置 0
            has_vedge = np.ones((m-1, n), dtype=int)
            has_hedge = np.ones((m, n-1), dtype=int)

            vcomp_type = np.zeros((m-1, n), dtype=int)
            hcomp_type = np.zeros((m, n-1), dtype=int)
            vcomp_label = np.zeros((m-1, n))
            hcomp_label = np.zeros((m, n-1))
            vcomp_value = np.zeros((m-1, n))
            hcomp_value = np.zeros((m, n-1))

            vcomp_value_unit = np.zeros((m-1, n), dtype=int)
            hcomp_value_unit = np.zeros((m, n-1), dtype=int)

            vcomp_direction = np.zeros((m-1, n), dtype=int) # 0 or 1
            hcomp_direction = np.zeros((m, n-1), dtype=int) # 0 or 1

            vcomp_measure = np.zeros((m-1, n), dtype=int)
            hcomp_measure = np.zeros((m, n-1), dtype=int)

            vcomp_measure_label = np.zeros((m-1, n))
            hcomp_measure_label = np.zeros((m, n-1))

            vcomp_measure_direction = np.zeros((m-1, n), dtype=int) # 0 or 1
            hcomp_measure_direction = np.zeros((m, n-1), dtype=int) # 0 or 1

            vcomp_control_meas_label = np.zeros((m-1, n))   
            hcomp_control_meas_label = np.zeros((m, n-1))

            # 组件计数、测量统计、控制源记录
            comp_cnt = [0] * 11
            meas_label_stat = {
                MEAS_TYPE_NONE: [],
                MEAS_TYPE_VOLTAGE: [],
                MEAS_TYPE_CURRENT: []
            }

            ## type, value, value_unit, label
            VC_sources = {'v': [], 'h': []}
            IC_sources = {'v': [], 'h': []}
            print(f"has_vedge: {has_vedge}\n\nhas_hedge: {has_hedge}")

            for i in range(m-1):
                for j in range(n):
                    if j == 0 or j == n-1:
                        vcomp_type[i][j] = np.random.choice(num_comp_choices_outer)
                    else:
                        vcomp_type[i][j] = np.random.choice(num_comp_choices)

                    if vcomp_type[i][j] in [TYPE_VCCS, TYPE_VCVS]:
                        VC_sources["v"].append((i, j))
                    if vcomp_type[i][j] in [TYPE_CCCS, TYPE_CCVS]:
                        IC_sources["v"].append((i, j))
                    if vcomp_type[i][j] == TYPE_OPEN:
                        has_vedge[i][j] = 0
                        continue

                    vcomp_value[i][j] = np.random.randint(comp_mean_value[vcomp_type[i][j]], comp_max_value[vcomp_type[i][j]])
                    vcomp_value_unit[i][j] = np.random.choice(unit_choices)

                    comp_cnt[vcomp_type[i][j]] += 1
                    vcomp_label[i][j] = comp_cnt[vcomp_type[i][j]]

                    vcomp_measure[i][j] = np.random.choice(meas_choices)
                    vcomp_measure_label[i][j] = np.random.choice(meas_label_choices)
                    meas_label_stat[vcomp_measure[i][j]].append(vcomp_measure_label[i][j])
                    vcomp_direction[i][j] = int(random.random() < meas_dir_prob)

                    print(f"\n\nvcomp_type[{i}][{j}]: {vcomp_type[i][j]}, vcomp_value[{i}][{j}]: {vcomp_value[i][j]}, vcomp_value_unit[{i}][{j}]: {vcomp_value_unit[i][j]}")
                    print(f"vcomp_measure[{i}][{j}]: {vcomp_measure[i][j]}, vcomp_measure_label[{i}][{j}]: {vcomp_measure_label[i][j]}, vcomp_direction[{i}][{j}]: {vcomp_direction[i][j]}")
            for i in range(m):
                for j in range(n-1):
                    if i == 0 or i == m-1:
                        hcomp_type[i][j] = np.random.choice(num_comp_choices_outer)
                    else:
                        hcomp_type[i][j] = np.random.choice(num_comp_choices)

                    if hcomp_type[i][j] in [TYPE_VCCS, TYPE_VCVS]:
                        VC_sources["h"].append((i, j))
                    if hcomp_type[i][j] in [TYPE_CCCS, TYPE_CCVS]:
                        IC_sources["h"].append((i, j))
                    if hcomp_type[i][j] == TYPE_OPEN:
                        has_hedge[i][j] = 0
                        continue
                    
                    hcomp_value[i][j] = np.random.randint(comp_mean_value[hcomp_type[i][j]], comp_max_value[hcomp_type[i][j]])
                    hcomp_value_unit[i][j] = np.random.choice(unit_choices)

                    comp_cnt[hcomp_type[i][j]] += 1
                    hcomp_label[i][j] = comp_cnt[hcomp_type[i][j]]

                    hcomp_measure[i][j] = np.random.choice(meas_choices)
                    hcomp_measure_label[i][j] = np.random.choice(meas_label_choices)
                    meas_label_stat[hcomp_measure[i][j]].append(hcomp_measure_label[i][j])
                    hcomp_direction[i][j] = int(random.random() < meas_dir_prob)

                    print(f"\n\nhcomp_type[{i}][{j}]: {hcomp_type[i][j]}, hcomp_value[{i}][{j}]: {hcomp_value[i][j]}, hcomp_value_unit[{i}][{j}]: {hcomp_value_unit[i][j]}")
                    print(f"hcomp_measure[{i}][{j}]: {hcomp_measure[i][j]}, hcomp_measure_label[{i}][{j}]: {hcomp_measure_label[i][j]}, hcomp_direction[{i}][{j}]: {hcomp_direction[i][j]}")
            
            # Check the control source
            num_vc_sources = len(VC_sources["v"]) + len(VC_sources["h"])
            num_ic_sources = len(IC_sources["v"]) + len(IC_sources["h"])
            num_vmeas = len(meas_label_stat[MEAS_TYPE_VOLTAGE])
            num_imeas = len(meas_label_stat[MEAS_TYPE_CURRENT])

            if (num_vc_sources > 0 and num_vmeas == 0) or (num_ic_sources > 0 and num_imeas == 0):
                continue

            print("VC_sources: ", VC_sources)
            print("IC_sources: ", IC_sources)
            print("meas_label_stat: ", meas_label_stat)

            # 为受控源随机选择控制测量（压控→电压测量；流控→电流测量）
            for i, j in VC_sources["v"]:
                contrl_idx = random.choice(meas_label_stat[MEAS_TYPE_VOLTAGE])
                vcomp_control_meas_label[i][j] = contrl_idx
            for i, j in VC_sources["h"]:
                contrl_idx = random.choice(meas_label_stat[MEAS_TYPE_VOLTAGE])
                hcomp_control_meas_label[i][j] = contrl_idx
            for i, j in IC_sources["v"]:
                contrl_idx = random.choice(meas_label_stat[MEAS_TYPE_CURRENT])
                vcomp_control_meas_label[i][j] = contrl_idx
            for i, j in IC_sources["h"]:
                contrl_idx = random.choice(meas_label_stat[MEAS_TYPE_CURRENT])
                hcomp_control_meas_label[i][j] = contrl_idx
            break
        
        # 是否在图上标数值（True）或标标签（False）
        use_value_annotation = bool(random.random() < use_value_annotation_prob)
        # label_str_subscript = bool(random.getrandbits(1)) & ~use_value_annotation
        label_str_subscript = False
        label_numerical_subscript = not label_str_subscript

        # Convert all matrix to int
        vcomp_type = vcomp_type.astype(int)
        hcomp_type = hcomp_type.astype(int)
        vcomp_label = vcomp_label.astype(int)
        hcomp_label = hcomp_label.astype(int)
        vcomp_value = vcomp_value.astype(int)
        hcomp_value = hcomp_value.astype(int)
        vcomp_value_unit = vcomp_value_unit.astype(int)
        hcomp_value_unit = hcomp_value_unit.astype(int)
        vcomp_measure = vcomp_measure.astype(int)
        hcomp_measure = hcomp_measure.astype(int)
        vcomp_measure_label = vcomp_measure_label.astype(int)
        hcomp_measure_label = hcomp_measure_label.astype(int)
        vcomp_measure_direction = vcomp_measure_direction.astype(int)
        hcomp_measure_direction = hcomp_measure_direction.astype(int)
        vcomp_control_meas_label = vcomp_control_meas_label.astype(int)
        hcomp_control_meas_label = hcomp_control_meas_label.astype(int)

        print("#"*100)
        print("Generate a random grid for circuit ... ")
        print(f"has_vedge: {has_vedge}\n\nhas_hedge: {has_hedge}")
        print(f"vertical_dis: {vertical_dis}\n\nhorizontal_dis: {horizontal_dis}")
        print(f"m:{m}, n:{n}\n\ncomp_cnt: {json.dumps(comp_cnt, indent=4)}")
        print(f"use_value_annotation: {use_value_annotation}\nlabel_numerical_subscript: {label_numerical_subscript}")

        print(f"vcomp_type: {vcomp_type}\n\nhcomp_type: {hcomp_type}")
        print(f"vcomp_label: {vcomp_label}\n\nhcomp_label: {hcomp_label}")
        print(f"vcomp_value: {vcomp_value}\n\nhcomp_value: {hcomp_value}")
        print(f"vcomp_value_unit: {vcomp_value_unit}\n\nhcomp_value_unit: {hcomp_value_unit}")
        print(f"vcomp_measure: {vcomp_measure}\n\nhcomp_measure: {hcomp_measure}")
        print(f"vcomp_measure_label: {vcomp_measure_label}\n\nhcomp_measure_label: {hcomp_measure_label}")
        print(f"vcomp_measure_direction: {vcomp_measure_direction}\n\nhcomp_measure_direction: {hcomp_measure_direction}")
        print(f"vcomp_control_meas_label: {vcomp_control_meas_label}\n\nhcomp_control_meas_label: {hcomp_control_meas_label}")

        # print(f"Generating a circuit grid of size {m}x{n} with {num_volsrs} voltage sources, {num_cursrs} current sources, and {num_r} resistors.")
        circ = Circuit(m, n, vertical_dis, horizontal_dis, has_vedge, has_hedge, vcomp_type, hcomp_type, vcomp_label, hcomp_label, \
                        vcomp_value=vcomp_value, hcomp_value=hcomp_value, \
                        vcomp_value_unit=vcomp_value_unit, hcomp_value_unit=hcomp_value_unit, \
                        vcomp_measure=vcomp_measure, hcomp_measure=hcomp_measure, \
                        vcomp_measure_label=vcomp_measure_label, hcomp_measure_label=hcomp_measure_label, \
                        use_value_annotation=use_value_annotation, note=note, id=id,
                        vcomp_direction=vcomp_direction, hcomp_direction=hcomp_direction,
                        vcomp_measure_direction=vcomp_measure_direction, hcomp_measure_direction=hcomp_measure_direction,
                        vcomp_control_meas_label=vcomp_control_meas_label, hcomp_control_meas_label=hcomp_control_meas_label,
                        label_numerical_subscript=label_numerical_subscript)


    else:
        circ = Circuit()
    return circ
