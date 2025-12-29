# MAPS项目工作介绍 - Mermaid版本

> 本文档包含所有Mermaid图表代码，可直接复制使用

---

## 1. 核心工作架构（统一视图）

```mermaid
flowchart TB
    subgraph Work1[工作一：数据生成脚本]
        Config[配置参数<br/>版本号/数量/编辑数]
        GenBase[生成基础电路<br/>gen_circuit]
        GenEdit[生成编辑操作<br/>EditGenerator]
        ApplyEdit[应用编辑<br/>ParameterEditOperation]
        GenDesc[生成描述<br/>stat_to_natural_language]
    end
    
    subgraph Work2[工作二：原理图搭建工具]
        GUI[图形界面<br/>Tkinter]
        Edit[可视化编辑<br/>GridCanvas]
        Property[属性编辑<br/>PropertyPanel]
    end
    
    subgraph GridCore[Grid数据格式核心]
        Circuit[Circuit类<br/>grid_rules.py]
        GridModel[GridModel类<br/>grid_model.py]
        GridJSON[Grid JSON格式<br/>统一数据表示]
    end
    
    subgraph Output[输出格式]
        LaTeX[LaTeX原理图<br/>circuit.tex]
        SPICE[SPICE代码<br/>circuit.sp]
        PNG[渲染图像<br/>circuit.png]
        Desc[电路描述<br/>description.txt]
        EditDesc[编辑描述<br/>edit_instruction.txt]
    end
    
    Config --> GenBase
    GenBase --> Circuit
    GenEdit --> ApplyEdit
    ApplyEdit --> Circuit
    GenBase --> GenDesc
    
    GUI --> Edit
    Edit --> GridModel
    Property --> GridModel
    GridModel --> Circuit
    
    Circuit --> GridJSON
    GridJSON --> LaTeX
    GridJSON --> SPICE
    GridJSON --> GenDesc
    GenDesc --> Desc
    GenDesc --> EditDesc
    
    LaTeX --> PNG
    
    style Work1 fill:#e1f5ff
    style Work2 fill:#fff4e1
    style GridCore fill:#e8f5e9
    style Output fill:#f3e5f5
    style Circuit fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style GridJSON fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
```

---

## 2. 完整数据流图

```mermaid
flowchart LR
    subgraph AutoGen[自动生成路径]
        A1[配置参数] --> A2[gen_circuit<br/>生成基础电路]
        A2 --> A3[Circuit对象<br/>Grid格式]
        A3 --> A4[生成编辑操作]
        A4 --> A5[应用编辑]
        A5 --> A3
    end
    
    subgraph ManualEdit[手动编辑路径]
        M1[启动GUI工具] --> M2[可视化编辑]
        M2 --> M3[GridModel对象]
        M3 --> M4[保存Grid JSON]
        M4 --> M5[转换为Circuit对象]
    end
    
    subgraph GridFormat[Grid数据格式<br/>统一核心]
        G1[Grid JSON格式<br/>circuit.json]
        G2[Circuit类<br/>内存对象]
    end
    
    subgraph Convert[格式转换]
        C1[to_latex<br/>LaTeX转换]
        C2[_to_SPICE<br/>SPICE转换]
        C3[编译渲染<br/>PNG生成]
        C4[描述生成<br/>自然语言]
    end
    
    subgraph FinalOutput[最终输出]
        F1[circuit.tex<br/>LaTeX原理图]
        F2[circuit.sp<br/>SPICE代码]
        F3[circuit.png<br/>渲染图像]
        F4[description.txt<br/>电路描述]
        F5[edit_instruction.txt<br/>编辑描述]
    end
    
    A3 --> G2
    M5 --> G2
    G2 --> G1
    G1 --> G2
    
    G2 --> C1
    G2 --> C2
    G2 --> C4
    
    C1 --> C3
    C3 --> F3
    C1 --> F1
    C2 --> F2
    C4 --> F4
    C4 --> F5
    
    style GridFormat fill:#ffeb3b,stroke:#f57f17,stroke-width:4px
    style G1 fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style G2 fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style AutoGen fill:#e1f5ff
    style ManualEdit fill:#fff4e1
    style FinalOutput fill:#e8f5e9
```

---

## 3. 工作一：数据生成脚本流程

```mermaid
flowchart TD
    Start[开始] --> Config[配置参数<br/>--note v11<br/>--gen_num 100<br/>--num_edits 3]
    
    Config --> GenBase[生成基础电路<br/>gen_circuit]
    GenBase --> Circuit1[Circuit对象<br/>Grid格式]
    
    Circuit1 --> GenDesc1[生成基础描述<br/>stat_to_natural_language]
    Circuit1 --> Export1[导出格式]
    
    Export1 --> LaTeX1[circuit.tex]
    Export1 --> SPICE1[circuit.sp]
    Export1 --> PNG1[circuit.png]
    Export1 --> Desc1[description.txt]
    
    Circuit1 --> GenEdit[生成编辑操作<br/>EditGenerator]
    GenEdit --> ApplyEdit[应用编辑<br/>ParameterEditOperation]
    ApplyEdit --> Circuit2[修改后的Circuit对象]
    
    Circuit2 --> GenDesc2[生成编辑描述]
    Circuit2 --> Export2[导出格式]
    
    Export2 --> LaTeX2[circuit.tex]
    Export2 --> SPICE2[circuit.sp]
    Export2 --> PNG2[circuit.png]
    Export2 --> EditDesc[edit_instruction.txt]
    
    GenDesc1 --> SaveBase[保存base/目录]
    GenDesc2 --> SaveEdit[保存edit_1/目录]
    SaveBase --> SaveMeta[保存metadata.json]
    SaveEdit --> SaveMeta
    SaveMeta --> End[完成]
    
    style Circuit1 fill:#ffeb3b,stroke:#f57f17,stroke-width:2px
    style Circuit2 fill:#ffeb3b,stroke:#f57f17,stroke-width:2px
    style GenBase fill:#e1f5ff
    style Export1 fill:#e8f5e9
    style Export2 fill:#e8f5e9
```

---

## 4. 工作二：原理图搭建工具流程

```mermaid
flowchart TD
    Start[启动工具] --> GUI[打开图形界面]
    GUI --> Edit[可视化编辑电路]
    
    Edit --> AddComp[添加元件<br/>组件面板选择]
    Edit --> SetProp[设置属性<br/>属性面板编辑]
    Edit --> Connect[连接节点<br/>网格画布操作]
    
    AddComp --> GridModel[GridModel对象<br/>内存数据]
    SetProp --> GridModel
    Connect --> GridModel
    
    GridModel --> SaveGrid[保存Grid格式<br/>circuit.json]
    GridModel --> ToCircuit[转换为Circuit对象]
    
    ToCircuit --> AutoConvert[自动转换]
    
    AutoConvert --> ToLaTeX[to_latex<br/>LaTeX转换]
    AutoConvert --> ToSPICE[_to_SPICE<br/>SPICE转换]
    
    ToLaTeX --> Compile[编译LaTeX<br/>pdflatex]
    Compile --> PDF[circuit.pdf]
    PDF --> Convert[转换PNG<br/>ImageMagick]
    Convert --> PNG[circuit.png]
    
    ToSPICE --> SPICEFile[circuit.sp]
    ToLaTeX --> LaTeXFile[circuit.tex]
    
    SaveGrid --> End[完成]
    SPICEFile --> End
    LaTeXFile --> End
    PNG --> End
    
    style GridModel fill:#ffeb3b,stroke:#f57f17,stroke-width:2px
    style ToCircuit fill:#ffeb3b,stroke:#f57f17,stroke-width:2px
    style SaveGrid fill:#ffeb3b,stroke:#f57f17,stroke-width:2px
    style Edit fill:#e1f5ff
    style AutoConvert fill:#fff4e1
    style End fill:#e8f5e9
```

---

## 5. Grid数据格式结构

```mermaid
graph TB
    subgraph GridFormat[Grid数据格式]
        JSON[Grid JSON文件<br/>circuit.json]
        Circuit[Circuit类对象<br/>内存表示]
        GridModel[GridModel类对象<br/>编辑器使用]
    end
    
    subgraph GridData[Grid数据结构]
        Size[网格尺寸<br/>m × n]
        Nodes[节点数组<br/>grid_nodes]
        Edges[边数组<br/>has_hedge/has_vedge]
        Components[元件信息<br/>类型/值/单位/标签]
        NodeComps[节点元件<br/>三极管/二极管/运放]
    end
    
    subgraph Conversion[格式转换]
        ToCircuit[GridModel → Circuit]
        FromCircuit[Circuit → GridModel]
        ToJSON[Circuit → JSON]
        FromJSON[JSON → Circuit]
    end
    
    JSON --> Circuit
    GridModel --> Circuit
    Circuit --> GridData
    
    GridModel <--> ToCircuit <--> Circuit
    Circuit <--> ToJSON <--> JSON
    
    style GridFormat fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style Circuit fill:#ffeb3b,stroke:#f57f17,stroke-width:2px
    style JSON fill:#ffeb3b,stroke:#f57f17,stroke-width:2px
```

---

## 6. Grid格式连接两个工作

```mermaid
flowchart TB
    subgraph Work1[工作一：数据生成]
        Gen[gen_circuit函数] --> Circuit1[Circuit对象<br/>Grid格式]
        Circuit1 --> Export1[导出LaTeX/SPICE/PNG]
    end
    
    subgraph Work2[工作二：搭建工具]
        Edit[GUI编辑] --> GridModel[GridModel对象]
        GridModel --> Save[保存JSON]
        GridModel --> Circuit2[转换为Circuit对象]
        Circuit2 --> Export2[导出LaTeX/SPICE/PNG]
    end
    
    subgraph Common[共同核心]
        GridJSON[Grid JSON格式<br/>circuit.json]
        CircuitClass[Circuit类<br/>grid_rules.py]
        Convert[格式转换<br/>to_latex/_to_SPICE]
    end
    
    Circuit1 --> CircuitClass
    Circuit2 --> CircuitClass
    CircuitClass --> GridJSON
    CircuitClass --> Convert
    
    Export1 --> Output[多格式输出]
    Export2 --> Output
    
    style Common fill:#ffeb3b,stroke:#f57f17,stroke-width:4px
    style CircuitClass fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style GridJSON fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style Work1 fill:#e1f5ff
    style Work2 fill:#fff4e1
    style Output fill:#e8f5e9
```

---

## 7. 完整数据流

```mermaid
flowchart LR
    subgraph Source1[数据源1：自动生成]
        S1[配置] --> S2[gen_circuit]
        S2 --> S3[Circuit对象]
    end
    
    subgraph Source2[数据源2：手动编辑]
        M1[GUI编辑] --> M2[GridModel]
        M2 --> M3[Circuit对象]
    end
    
    subgraph Grid[Grid统一格式]
        G1[Circuit对象]
        G2[Grid JSON]
    end
    
    subgraph Process[处理转换]
        P1[to_latex]
        P2[_to_SPICE]
        P3[描述生成]
        P4[编译渲染]
    end
    
    subgraph Output[输出文件]
        O1[circuit.tex]
        O2[circuit.sp]
        O3[circuit.png]
        O4[description.txt]
        O5[edit_instruction.txt]
    end
    
    S3 --> G1
    M3 --> G1
    G1 --> G2
    G2 --> G1
    
    G1 --> P1
    G1 --> P2
    G1 --> P3
    
    P1 --> P4
    P1 --> O1
    P2 --> O2
    P3 --> O4
    P3 --> O5
    P4 --> O3
    
    style Grid fill:#ffeb3b,stroke:#f57f17,stroke-width:4px
    style G1 fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style G2 fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
```

---

## 8. Grid格式转换能力（思维导图）

```mermaid
mindmap
  root((Grid数据格式))
    数据表示
      JSON格式存储
      Circuit类对象
      GridModel类对象
    转换能力
      Grid → LaTeX
      Grid → SPICE
      Grid → PNG
      Grid ↔ JSON
    统一接口
      两个工作共用
      Circuit类核心
      grid_rules.py引擎
    数据完整性
      元件信息
      拓扑结构
      参数值
      连接关系
```

---

## 9. 简化版：核心架构图

```mermaid
flowchart TB
    subgraph Work1[工作一：数据生成脚本]
        A1[批量生成线性电路]
        A2[生成电路描述]
        A3[生成修改电路]
        A4[生成修改描述]
        A1 --> A2
        A1 --> A3
        A3 --> A4
    end
    
    subgraph Work2[工作二：原理图搭建工具]
        B1[可视化编辑]
        B2[Grid格式保存]
        B1 --> B2
    end
    
    subgraph GridCore[Grid数据格式核心]
        C1[Circuit类<br/>grid_rules.py]
        C2[Grid JSON格式]
    end
    
    subgraph Output[输出格式]
        D1[LaTeX原理图]
        D2[SPICE代码]
        D3[PNG图像]
        D4[描述文本]
    end
    
    A1 --> C1
    A3 --> C1
    B2 --> C1
    C1 --> C2
    C2 --> C1
    
    C1 --> D1
    C1 --> D2
    C1 --> D3
    C1 --> D4
    
    style GridCore fill:#ffeb3b,stroke:#f57f17,stroke-width:4px
    style C1 fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style C2 fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style Work1 fill:#e1f5ff
    style Work2 fill:#fff4e1
    style Output fill:#e8f5e9
```

---

## 使用说明

### 方式一：在Markdown中使用
直接复制上述任意Mermaid代码块到Markdown文件中，支持Mermaid的编辑器会自动渲染。

### 方式二：在线渲染
1. 访问 [Mermaid Live Editor](https://mermaid.live/)
2. 复制Mermaid代码
3. 实时预览和导出

### 方式三：在文档中使用
- GitHub/GitLab：直接支持Mermaid渲染
- VS Code：安装Mermaid插件
- Notion/Obsidian：支持Mermaid语法

---

## 图表说明

1. **核心工作架构图**：展示两个工作如何通过Grid格式连接
2. **完整数据流图**：展示从输入到输出的完整流程
3. **工作一流程**：数据生成脚本的详细步骤
4. **工作二流程**：搭建工具的详细步骤
5. **Grid格式结构**：Grid数据格式的组成和转换
6. **Grid连接图**：展示Grid如何连接两个工作
7. **完整数据流**：简化的数据流向图
8. **思维导图**：Grid格式的能力总结
9. **简化架构图**：最简洁的核心架构

---

*最后更新: 2025年*


