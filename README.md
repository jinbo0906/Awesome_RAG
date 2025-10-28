# awesome_rag
在检索增强生成（RAG）技术飞速发展的当下，传统一体化链路设计逐渐暴露出**灵活性不足、迭代效率低、场景适配难**等关键问题，难以满足多样化的业务需求和快速的技术迭代节奏。为解决这一痛点，本项目提出**模块化 RAG 链路设计方案**，将完整的 RAG 链路解耦为可独立运行、即插即用的子模块，通过标准化接口实现模块间的灵活组合，最终构建兼具稳定性与扩展性的检索增强系统。

模块化解耦的核心思路在于 “拆分复杂系统、明确模块职责、标准化接口交互”。这种设计不仅能让 RAG 链路更好地适应技术迭代（如替换更优的 embedding 模型、检索算法）、业务变化（如适配文档问答、知识库问答等不同场景）和规模化需求（如分布式部署、多数据源接入），也是构建灵活、高效、可扩展检索增强系统的关键基础。

## 核心链路设计

本项目将 RAG 链路分为**离线链路**（数据预处理与存储）和**在线链路**（查询处理与生成）两大模块，各模块包含多个可替换的算子，所有算子均遵循统一的输入输出接口规范，确保 “即插即用”。

### 1. 离线链路（数据预处理与存储）

离线链路主要负责将原始文档转化为可检索的向量数据，存入向量数据库，为在线检索提供数据支撑。

|算子名称|核心功能|主流实现方法|代码实现与接口规范|
|-|-|-|-|
|文档解析|将多种格式的原始文档（如 PDF、Word、TXT、Markdown 等）解析为结构化文本数据|MinerU（多格式文档解析工具）、  DeepSeek-OCR（图文混合文档 OCR 解析）、  PaddleOCR（开源 OCR 工具）、  PyPDF2（PDF 解析）等|文档解析模块目录  **输入**：原始文档文件路径 / 二进制流  **输出**：结构化文本（JSON 格式，包含段落 ID、文本内容、页码等元信息）|
|文档切片|将长文本拆分为适合 embedding 的短文本片段（Chunk），平衡检索精度与召回率|递归切片（Recursive Chunking，按段落 / 句子递归拆分）、  语义切片（基于语义相似度拆分，如 Sentence-BERT、LumberChunk）、  固定长度切片（按字符 /token 数拆分）|文档切片模块目录  **输入**：结构化文本（文档解析模块输出）  **输出**：切片列表（JSON 格式，包含切片 ID、文本内容、所属文档 ID 等元信息）|
|文本向量化|将切片后的文本转化为低维稠密向量，捕捉文本语义信息|Bge-embedding（开源高效 embedding 模型）、  Qwen-embedding（通义千问系列 embedding 模型）、  OpenAI Embeddings（闭源 API）|文本向量化模块目录  **输入**：切片列表（文档切片模块输出）  **输出**：向量列表（JSON 格式，包含切片 ID、向量数据、文本内容等）|
|向量数据库存储|将文本向量与元信息存入向量数据库，支持高效的相似性检索|Elasticsearch（搜索引擎，支持向量检索与关键词检索混合）、  FAISS（Facebook 开源向量检索库，适合单机场景）、  Milvus（分布式向量数据库，适合大规模场景）、  Chroma（轻量级开源向量数据库）|向量存储模块目录  **输入**：向量列表（文本向量化模块输出）  **输出**：存储成功 / 失败状态（含索引 ID、存储耗时等元信息）|
|...|...|...|...|


### 2. 在线链路（查询处理与生成）

在线链路主要负责接收用户查询（Query），通过检索、重排序等操作获取相关上下文，最终结合 LLM 生成精准回答。

|算子名称|核心功能|主流实现方法|代码实现与接口规范|
|-|-|-|-|
|Query 优化|对用户原始 Query 进行改写、拆解或扩展，提升后续检索的召回率与精度|Query 改写（基于 LLM 优化表述，如 “怎么用 RAG？”→“如何构建检索增强生成（RAG）系统并应用于文档问答场景？”）、  Query 拆解（将复杂 Query 拆分为子 Query，如 “RAG 和 Fine-tuning 的区别与适用场景”→拆分为 “RAG 和 Fine-tuning 的区别”“RAG 的适用场景”“Fine-tuning 的适用场景”）、  关键词提取（提取 Query 中的核心关键词，辅助关键词检索）|Query 优化模块目录  **输入**：用户原始 Query（字符串）  **输出**：优化后的 Query 列表 / 关键词列表（JSON 格式）|
|文本召回|根据优化后的 Query 从向量数据库中检索相关文本切片，获取候选上下文|关键词检索（基于 Elasticsearch 等搜索引擎的全文匹配）、  向量化检索（基于向量相似度的近邻检索，如 FAISS 的 IVF_FLAT、Milvus 的 HNSW）、  混合检索（融合关键词检索与向量化检索结果，提升召回率）；  关键词检索优化（如 BM25 算法、同义词扩展、停用词过滤）|文本召回模块目录  **输入**：优化后的 Query / 关键词（Query 优化模块输出）  **输出**：召回结果列表（JSON 格式，包含切片 ID、文本内容、相似度得分等）|
|重排序|对召回的候选文本进行二次排序，筛选出与 Query 最相关的文本，提升精度|Bge-rerank（开源重排序模型）、  Qwen-rerank（通义千问系列重排序模型）|重排序模块目录  **输入**：召回结果列表（文本召回模块输出）、原始 Query  **输出**：重排序后的结果列表（JSON 格式，包含排序后的切片、最终得分等）|
|生成|结合重排序后的上下文与 LLM，生成准确、简洁的回答，优化生成策略|生成策略（如 “上下文 + Query”prompt 构造、  少样本提示（Few-shot Prompting）、  思维链提示（Chain of Thought））；  LLM 支持（如 ChatGLM、Qwen、Llama、GPT 系列）|生成模块目录  **输入**：重排序后的结果列表（重排序模块输出）、原始 Query  **输出**：最终回答（字符串）、生成日志（含 LLM 调用信息、耗时等）|
|...|...|...|...|


## RAG 策略实现

基于上述算子的灵活组合，本项目将实现多种主流 RAG 策略，后续将持续扩展：

|策略名称|核心逻辑|适用场景|实现代码目录|
|-|-|-|-|
|基础 RAG|Query 优化 → 向量化检索 → 重排序 → LLM 生成|通用文档问答、知识库查询|基础 RAG 策略|
|混合检索 RAG|Query 优化 → 关键词检索 + 向量化检索（并行） → 结果融合 → 重排序 → LLM 生成|长文档问答、多数据源检索|混合检索 RAG 策略|
|多轮对话 RAG|历史对话记忆 → Query 优化（结合历史上下文） → 文本召回 → 重排序 → LLM 生成|多轮连续问答、上下文依赖场景|多轮对话 RAG 策略|
|子 Query 拆分 RAG|复杂 Query 拆解 → 子 Query 召回 → 子结果汇总 → 重排序 → LLM 生成|复杂问题拆解、多维度查询|子 Query 拆分 RAG 策略|
|...|...|...|...|


## ToDo List

### 一、项目准备

- [x] [RAG 介绍](RAG技术深度总结.md)
- [ ] 环境配置
- [x] [接口规范说明](接口规范说明.md)

### 二、离线链路模块

#### 1. 文档解析模块

- [ ] 文档解析模块README—简介、主流文档解析方法调研、对比
- [ ] 部署MinerU 教程
- [ ] 部署PaddleOCR  教程
- [ ] 实现 MinerU 、PaddleOCR等 解析工具的封装代码
- [ ] 给出MinerU  与 PaddleOCR 等的对比测试
- [ ] Word 解析（markitdown）、Markdown 解析等方法的实现
- [ ] 完善模块 README，添加各解析工具的参数配置说明（如 MinerU 的格式支持范围、OCR 精度参数）

...

#### 2. 文本分块模块

- [ ] 文本分块模块README—简介、主流文本分块方法调研、对比
- [ ] 开发递归切片算法，支持自定义段落分隔符（如 \n\n、。、；#/##等标题）、支持固定长度
- [ ] 实现语义切片
    - [ ] LumberChunker
    - [ ] Late Chunking
    - [ ] Dense X Retrieval
    - [ ] Small2big
    - [ ] HiChunk

    ...
- [ ] 开发切片效果评估工具，例如，计算切片的语义完整性
- [ ] 补充切片模块的接口文档，明确各参数的默认值、可选范围及使用场景（如长文档用递归切片，短文档用固定长度切片）、不同切片方法与向量数据库的配合等

...

#### 3. 文本向量化模块

- [ ] 文本向量化模块README—简介、主流embedding调研、对比、各自的训练微调推理方法介绍
- [ ] 部署bge-m3-embedding 模型
- [ ] 部署qwen3-embedding模型
- [ ] 封装embedding模型的加载，支持本地加载、Hugging Face 远程加载、API调用等方式
- [ ] 集成 闭源 API

...

#### 4. 向量数据库存储模块

- [ ] 向量数据库README—简介、主流向量数据库调研、对比
- [ ] Elasticsearch部署，配置 IK 分词器（中文分词）与向量字段映射（float 数组类型），kibana
- [ ] 实现Elasticsearch封装，支持索引创建、持久化存储与加载等
- [ ] 实现 FAISS 向量库封装，支持索引创建（IVF_FLAT、HNSW 索引）、添加向量、持久化存储与加载
- [ ] 集成 Milvus 分布式客户端，支持集群地址配置、数据分区（按文档类型分区）与索引优化

...

### 三、在线链路模块

#### 1. 文本召回模块

- [ ] 文本召回README—简介、召回策略介绍
- [ ] 开发 Elasticsearch 关键词检索、向量检索、混合检索功能
- [ ] 开发Elasticsearch 关键词检索优化策略，支持不同字段设置查询权重、query关键词提取设置权重等
- [ ] 实现 FAISS 向量化检索，支持设置检索数量（top_k，默认 20）与相似度阈值（默认 0.5，低于阈值不返回）等

...

#### 2. 重排序模块

- [ ] 重排序模块README—简介、主流rerank调研、对比、各自的训练微调推理方法介绍
- [ ] 部署Bge-rerank 模型
- [ ] 部署qwen3-rerank 模型
- [ ] 封装rerank 模型的加载，支持本地加载、Hugging Face 远程加载、API调用等方式
- [ ] 集成 闭源 API

#### 3. 生成模块

- [ ] 开发通用 prompt 模板，支持动态插入上下文
- [ ] 闭源 API 调用
- [ ] 集成本地模型

...

#### 4. Query 优化模块

- [ ] 向量数据库README—简介、主流向量数据库调研、对比
- [ ] 基于 LLM 实现 Query 改写 prompt 模板，支持自定义改写方向（更详细、更简洁、更正式）
- [ ] Query2doc
- [ ] HyDE
- [ ] 开发Query 拆解算法
- [ ] 新增 Query 优化效果评估工具，对比优化前后的检索召回率（基于标准测试集的 Query - 文档匹配对）
- [ ] 多轮对话场景下的 Query 上下文融合逻辑，支持将历史对话摘要与当前 Query 合并优化

...

### 四、RAG 策略实现

#### 1. 基础 RAG 策略

- [ ] 基础RAG链路实现，支持命令行输入 Query，输出回答与上下文来源
- [ ] 实现算子失败降级策略（如重排序失败则直接使用召回结果生成）
- [ ] 实现 YAML 配置文件支持，可通过 config.yaml 配置算子参数（如 embedding 模型路径、检索 top_k）与策略流程

...

#### 2. 混合检索 RAG 策略

- [ ] 在基础RAG链路基础上，实现混合检索
- [ ] 实现YAML 配置文件支持，可通过 config.yaml 配置算子参数

#### 3. 多轮对话 RAG 策略（待优化）

- [ ] 开发对话历史管理功能，支持设置历史轮次上限（默认 5 轮），超出部分自动截断最早轮次
- [ ] 实现 Query 与历史上下文的融合重构逻辑，支持将历史对话摘要（LLM 生成摘要）与当前 Query 合并
- [ ] 开发多轮对话场景下的上下文相关性校验功能，过滤与当前 Query 无关的历史对话内容

...

#### 4. 子 Query 拆分 RAG 策略（待优化）

- [ ] 优化子 Query 拆解算法，支持根据问题类型（如 “是什么”“为什么”“怎么做”）调整拆解粒度（细粒度 / 粗粒度）
- [ ] 实现子 Query 并行召回，使用多线程同时检索多个子 Query，提升复杂问题处理效率
- [ ] 补充子 Query 结果冲突处理策略，当不同子 Query 召回的上下文冲突时，优先选择高相似度（得分 top 30%）结果并标注冲突点

...

#### 5.GraphRAG策略


#### 6.Agentic RAG策略


#### 7. 多模态RAG策略


RAG策略持续更新...

### 五、评估

- [ ] 评估README—简介、主流评估策略调研、对比
- [ ] 评估方法实现

### 六、通用工具与文档任务

#### 1. 通用工具开发（待优化）

- [ ] 开发链路各算子输出监控，用于分析链路节点问题
- [ ] 开发链路可视化工具，基于 Streamlit 实现算子运行状态、数据流向、耗时的实时展示
- [ ] 新增日志管理工具，支持按模块（离线 / 在线）、日志级别（INFO/ERROR/WARN）输出与存储日志
- [ ] 实现配置中心功能，支持通过 Web 界面修改算子参数、策略流程，无需修改代码
- [ ] 开发数据清洗工具，处理文档中的特殊字符、空白行、重复内容，提升数据质量
- [ ] 前端web界面实现

#### 2. 文档完善（待优化）

- [ ] 补充项目快速入门视频教程，演示离线链路数据处理、在线链路问答的完整流程
- [ ] 编写算子开发指南，明确新算子接入的接口规范、测试要求、文档格式
- [ ] 整理常见问题手册（FAQ），覆盖环境配置、算子报错、策略效果优化等场景
- [ ] 生成 API 文档，基于 Sphinx 自动提取代码注释，支持在线查阅各函数参数与返回值

## 项目结构

```Markdown
rag-architecture-learning/
├── offline/                  # 离线链路模块
│   ├── document_parsing/     # 文档解析（MinerU、DeepSeek-OCR等）
│   │   ├── __init__.py
│   │   ├── mineru_parser.py  # MinerU解析实现
│   │   └── ...
│   ├── document_chunking/    # 文档切片（递归、语义等）
│   ├── text_embedding/       # 文本向量化（Bge-embedding等）
│   └── vector_storage/       # 向量数据库存储（FAISS、Elasticsearch等）
├── online/                   # 在线链路模块
│   ├── query_optimization/   # Query优化（改写、拆解等）
│   ├── text_retrieval/       # 文本召回（关键词、向量化等）
│   ├── text_reranking/       # 重排序（Bge-rerank等）
│   └── text_generation/      # 生成（LLM调用、prompt策略等）
├── strategies/               # RAG策略实现
│   ├── basic_rag/            # 基础RAG策略
│   ├── hybrid_retrieval_rag/ # 混合检索RAG策略
│   ├── multi_turn_rag/       # 多轮对话RAG策略
│   └── subquery_rag/         # 子Query拆分RAG策略
├── common/                   # 通用工具模块
│   ├── log_manager.py        # 日志管理
│   ├── config_center.py      # 配置中心
│   └── data_cleaner.py       # 数据清洗
├── docs/                     # 项目文档
│   ├── api_docs/             # API文档
│   ├── dev_guide/            # 开发指南
│   ├── faq.md                # 常见问题
│   └── interface_specification.md # 接口规范
├── tests/                    # 测试代码
│   ├── test_offline/         # 离线链路测试
│   ├── test_online/          # 在线链路测试
│   └── test_strategies/      # 策略测试
├── config/
│   ├── ...
├── requirements.txt          # 项目依赖
└── README.md                 # 项目说明（本文档）
```

## 快速开始

### 1. 环境准备

```Markdown
# 克隆项目
git clone https://github.com/xxx.git
cd xxx

# 安装基础依赖
pip install -r requirements.txt

# 安装可选依赖（根据使用的算子选择，如xxx）

```

### 2. 配置文件设置（待优化）

修改 config.yaml 关键配置（根据实际需求调整）：

```Markdown
# 离线链路配置
offline:
  document_parsing:
    parser_type: "mineru"  # 可选：mineru、paddle_ocr、deepseek_ocr
    batch_size: 10         # 批量解析文档数量
  text_embedding:
    model_name: "BAAI/bge-base-zh"  # embedding模型
    device: "cuda"  # 可选：cuda、cpu
  vector_storage:
    db_type: "faiss"  # 可选：faiss、elasticsearch、milvus
    faiss_index_path: "./vector_index/faiss_index"  # FAISS索引存储路径

# 在线链路配置
online:
  query_optimization:
    enable_rewrite: True  # 是否开启Query改写
    enable_split: True    # 是否开启Query拆分
  text_retrieval:
    top_k: 20  # 召回数量
    similarity_threshold: 0.5  # 相似度阈值
  text_generation:
    llm_type: "qwen"  # 可选：qwen、chatglm、openai
    qwen_model_path: "./models/qwen-7b-chat"  # 本地LLM路径
```

### 3. 离线链路运行（数据预处理）

```Python

```

### 4. 在线链路运行（问答示例）

```Python

```
