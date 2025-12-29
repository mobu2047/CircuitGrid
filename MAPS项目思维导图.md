# MAPS项目工作思维导图

## 项目概述

**MAPS** (Multi-modal Reasoning in Physical Science) - 多模态物理科学推理项目，专注于电路图理解、生成和转换。

---

## 整体架构图

```mermaid
mindmap
  root((MAPS项目))
    电路编辑器
      主窗口
      网格画布
      组件渲染器
      组件面板
      属性面板
      网格模型
      组件注册表
    数据生成系统
      Grid规则引擎
      电路生成器
      编辑操作框架
      自然语言生成
      LaTeX编译
      SPICE验证
    VLM微调系统
      模型微调
      LoRA/QLoRA
      PTuning
      推理接口
      SPICE评估
      数据处理
    工具模块
      模型封装
      数据处理
      模拟工具
      LaTeX工具
    电路识别Pipeline
      YOLO检测
      VLM拓扑理解
      Grid构建器
      主Pipeline
```

---

## 核心模块详细架构

### 1. 电路编辑器模块

```mermaid
graph TB
    subgraph Editor[电路编辑器 circuit_editor/]
        Main[main.py<br/>应用入口]
        MainWindow[main_window.py<br/>主窗口]
        GridCanvas[grid_canvas.py<br/>网格画布]
        ComponentRenderer[component_renderer.py<br/>组件渲染器]
        ComponentPalette[component_palette.py<br/>组件面板]
        PropertyPanel[property_panel.py<br/>属性面板]
        GridModel[grid_model.py<br/>网格模型]
        ComponentRegistry[component_registry.py<br/>组件注册表]
    end
    
    Main --> MainWindow
    MainWindow --> GridCanvas
    MainWindow --> ComponentPalette
    MainWindow --> PropertyPanel
    GridCanvas --> GridModel
    GridCanvas --> ComponentRenderer
    ComponentRenderer --> ComponentRegistry
    PropertyPanel --> GridModel
```

**功能特性**:
- ✅ 可视化编辑电路网格
- ✅ 添加/删除边和元件
- ✅ 设置元件类型和参数
- ✅ 导出LaTeX和SPICE格式

---

### 2. 数据生成系统

```mermaid
graph LR
    subgraph DataGen[数据生成系统 data_syn/]
        GridRules[grid_rules.py<br/>Grid规则引擎]
        Generate[generate.py<br/>数据生成器]
        EditOp[EditOperation<br/>编辑操作抽象]
        ParamEdit[ParameterEditOperation<br/>参数编辑]
        EditGen[EditGenerator<br/>编辑生成器]
    end
    
    subgraph Output[输出流程]
        Base[基础电路]
        Edit1[编辑变体1]
        Edit2[编辑变体2]
        LaTeX[LaTeX代码]
        SPICE[SPICE代码]
        PNG[PNG图像]
        Desc[自然语言描述]
    end
    
    GridRules --> Generate
    EditOp --> ParamEdit
    ParamEdit --> EditGen
    Generate --> Base
    EditGen --> Edit1
    EditGen --> Edit2
    Base --> LaTeX
    Base --> SPICE
    LaTeX --> PNG
    Generate --> Desc
```

**数据流程**:
```
基础电路生成 → 应用编辑操作 → 生成变体 → 导出LaTeX/SPICE → 编译渲染
```

**输出结构**:
```
edit_dataset/
  ├── circuit_id/
  │   ├── base/          # 基础电路
  │   ├── edit_1/        # 编辑变体1
  │   ├── edit_2/        # 编辑变体2
  │   └── metadata.json  # 元数据
```

---

### 3. VLM微调系统

```mermaid
graph TB
    subgraph VLM[VLM微调系统 ft_vlm/]
        FineTune[finetune_cogagent.py<br/>模型微调]
        Inference[inference_cogagent.py<br/>推理接口]
        EvalSpice[evaluate_spice.py<br/>SPICE评估]
        DataProc[data_process/<br/>数据处理]
    end
    
    subgraph Training[训练流程]
        Dataset[数据集]
        LoRA[LoRA/QLoRA]
        PTuning[PTuning]
        DeepSpeed[DeepSpeed]
    end
    
    subgraph Eval[评估流程]
        Accuracy[准确率]
        Compile[编译成功率]
        Sim[仿真准确率]
    end
    
    Dataset --> FineTune
    LoRA --> FineTune
    PTuning --> FineTune
    DeepSpeed --> FineTune
    FineTune --> Inference
    Inference --> EvalSpice
    EvalSpice --> Accuracy
    EvalSpice --> Compile
    EvalSpice --> Sim
    DataProc --> Dataset
```

**训练配置**:
- 支持DeepSpeed分布式训练
- 可训练参数：encoder, cross_attention, linear_proj, mlp.vision, rotary.vision, vit等
- 学习率缩放策略

---

### 4. 工具模块

```mermaid
graph TB
    subgraph Utils[工具模块 utils/]
        Models[models/<br/>模型封装]
        DataUtils[utils/<br/>数据处理]
        Simulation[simulation/<br/>模拟工具]
        Other[其他工具]
    end
    
    subgraph ModelsDetail[模型模块]
        CogAgent[cogagent_model.py]
        CogVLM[cogvlm_model.py]
        EVACLIP[eva_clip_model.py]
        Mixin[mixin.py]
    end
    
    subgraph DataUtilsDetail[数据处理]
        Dataset[dataset.py]
        Vision[vision.py]
        Language[language.py]
        CircuitUtils[circuit_utils.py]
    end
    
    subgraph SimDetail[模拟模块]
        AutoSpice[auto_spice.py]
        SpiceUtils[spice_utils.py]
        Spice2Py[spice2pyspice.py]
    end
    
    Models --> ModelsDetail
    DataUtils --> DataUtilsDetail
    Simulation --> SimDetail
```

---

### 5. 计划中的电路识别Pipeline

```mermaid
flowchart TD
    Input[电路原理图图像] --> YOLO[YOLO元件检测<br/>yolo_detector.py]
    Input --> VLM[VLM拓扑理解<br/>vlm_topology.py]
    
    YOLO --> Elements[元件列表<br/>+ bbox坐标]
    Elements --> VLM
    
    VLM --> Topology[连接关系<br/>JSON]
    
    Elements --> GridBuilder[Grid构建器<br/>grid_builder.py]
    Topology --> GridBuilder
    
    GridBuilder --> Grid[Grid结构]
    Grid --> Circuit[Circuit对象]
    
    Circuit --> LaTeX[to_latex<br/>LaTeX代码]
    Circuit --> SPICE[_to_SPICE<br/>SPICE代码]
    
    style Input fill:#e1f5ff
    style YOLO fill:#fff4e1
    style VLM fill:#fff4e1
    style GridBuilder fill:#fff4e1
    style LaTeX fill:#e8f5e9
    style SPICE fill:#e8f5e9
```

**状态**: 🚧 规划中

---

## 数据流和依赖关系

### 完整数据流图

```mermaid
flowchart TB
    subgraph Generation[数据生成流程]
        GridRules[grid_rules.py<br/>定义规则] --> Gen[generate.py<br/>生成电路]
        Gen --> BaseCircuit[基础电路]
        Gen --> EditOps[编辑操作]
        EditOps --> Variants[编辑变体]
        BaseCircuit --> LaTeXGen[生成LaTeX]
        Variants --> LaTeXGen
        LaTeXGen --> PDF[编译PDF]
        PDF --> PNG[转PNG图像]
        BaseCircuit --> SPICEGen[生成SPICE]
        Gen --> DescGen[自然语言描述]
    end
    
    subgraph Training[模型训练流程]
        Dataset[数据集<br/>图像+标签] --> FineTune[finetune_cogagent.py<br/>模型微调]
        FineTune --> Model[训练好的模型]
        Model --> Inference[inference_cogagent.py<br/>推理]
        Inference --> Eval[evaluate_spice.py<br/>SPICE验证]
    end
    
    subgraph Editor[编辑器流程]
        GUI[GUI编辑] --> GridModel[grid_model.py<br/>管理数据]
        GridModel --> Render[component_renderer.py<br/>渲染]
        GridModel --> Export[导出LaTeX/SPICE]
    end
    
    PNG --> Dataset
    SPICEGen --> Eval
    Export --> Dataset
```

---

## 技术栈

```mermaid
mindmap
  root((技术栈))
    深度学习框架
      PyTorch
      SAT
      DeepSpeed
    视觉模型
      CogAgent
      CogVLM
      EVA-CLIP
    电路相关
      CircuitTikZ
      SPICE
      PySpice
    GUI框架
      Tkinter
    数据处理
      NumPy
      PIL
      JSON
```

---

## 项目特点

1. **多模态**: 结合视觉和语言理解
2. **双向转换**: Grid ↔ LaTeX ↔ SPICE
3. **可扩展**: 支持多种编辑操作类型
4. **验证机制**: SPICE仿真验证代码正确性
5. **可视化**: GUI编辑器提供直观的电路编辑体验

---

## 未来规划

1. ✅ 实现电路识别Pipeline（YOLO + VLM）
2. ✅ 支持更多元件类型
3. ✅ 增强拓扑理解能力
4. ✅ 优化模型性能
5. ✅ 扩展数据集规模

---

## 文件结构总览

```
MAPS-master/
├── ppm_construction/
│   ├── circuit_editor/          # 电路编辑器
│   │   ├── main.py
│   │   ├── views/               # 视图层
│   │   ├── models/              # 数据模型
│   │   └── registry/            # 组件注册
│   ├── data_syn/                # 数据生成
│   │   ├── grid_rules.py        # Grid规则引擎
│   │   ├── generate.py          # 数据生成器
│   │   └── data/                # 生成的数据
│   └── ft_vlm/                  # VLM微调
│       ├── finetune_cogagent.py
│       ├── inference_cogagent.py
│       ├── evaluate_spice.py
│       └── data_process/       # 数据处理
├── utils/                       # 工具模块
│   ├── models/                  # 模型封装
│   ├── utils/                   # 数据处理
│   └── simulation/              # 模拟工具
└── data/                        # 数据集
```

---

## 模块间依赖关系

```mermaid
graph TD
    GridRules[grid_rules.py] --> Generate[generate.py]
    GridRules --> CircuitEditor[circuit_editor/]
    Generate --> Dataset[数据集]
    Dataset --> FineTune[ft_vlm/]
    FineTune --> Inference[inference_cogagent.py]
    Inference --> EvalSpice[evaluate_spice.py]
    Utils[utils/] --> FineTune
    Utils --> Inference
    Utils --> Generate
    Utils --> CircuitEditor
```

---

*最后更新: 2025年*
