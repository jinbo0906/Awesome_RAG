# README

## 模块简介

Document Parser 是 Awesome\_RAG 项目离线链路中的核心模块，负责将多种格式的原始文档解析为结构化文本数据，为后续的文档切片、向量化等流程提供基础。该模块支持多种主流文档格式（如 Word、Markdown、TXT 等），并集成了多种解析工具，能够高效、准确地提取文档内容及元信息。

## 功能特点

- **多格式支持**：支持 `.doc`、`.docx`、`.md`、`.txt` 等常见文档格式解析
- **模块化设计**：不同格式对应独立解析器，便于扩展和维护
- **图片处理**：对 Word 文档中的图片进行提取和路径替换（支持本地保存）
- **批量处理**：支持单文件和文件夹批量解析

## 核心解析器

### 1. PdfParser &#x20;

**功能**：专门用于解析 PDF 格式文件，同时支持 PNG、JPG、JPEG 等图片格式（通过 OCR 技术提取内容）。 &#x20;

**实现特点** &#x20;

- 基于配置文件（`parser_config.yaml`）选择解析工具（默认使用 MinerU） &#x20;
- 集成 MinerU 解析能力，支持复杂 PDF 布局（含表格、公式、图片等）的解析 &#x20;
- 将解析结果转换为 Markdown 格式，保留文档结构信息 &#x20;
- 支持批量处理文件夹中的 PDF 文件 &#x20;

**依赖** &#x20;

- MinerU 解析框架（用于 PDF 内容提取与结构化） &#x20;

  MinerU的代码已经在当前的代码仓库里，可以直接拉取当前代码，则不需要再单独拉取MinerU的项目代码。

  本代码中，MinerU默认pipeline方式，涉及到的模型可以手动下载到指定目录，然后修改mineru.json中的配置。也可以直接运行代码，如果检测到没有模型，则会下载到默认路径，并自动配置。

### 2. DocParser &#x20;

**功能**：处理 Word 文档格式，包括 `.doc` 和 `.docx` 两种后缀的文件。 &#x20;

**实现特点** &#x20;

- 对 `.docx` 直接解析，对 `.doc` 先通过 `libreoffice` 转换为 `.docx` 再处理 &#x20;
- 使用 `mammoth` 和 `markitdown` 工具提取文本内容并转换为 Markdown 格式 &#x20;
- 支持提取文档中的图片并保存到指定目录，同时更新图片引用路径 &#x20;
- 保留文档原有的标题、列表等结构信息 &#x20;

### 3. TxtParser &#x20;

**功能**：解析纯文本文件（`.txt`），提取文件内容及元信息。 &#x20;

**实现特点**

- 极简设计，直接以 UTF-8 编码读取文本内容 &#x20;
- 提取文件大小、文件名等元数据 &#x20;
- 支持单文件和文件夹批量处理 &#x20;
- 无额外格式转换，保留原始文本内容 &#x20;

### 4. MarkdownParser &#x20;

**功能**：处理 Markdown 格式文件（`.md`），提取文本内容及文件元信息。 &#x20;

**实现特点** &#x20;

- 直接读取 Markdown 文件原始内容，不进行额外格式转换 &#x20;
- 支持批量处理单个 Markdown 文件或包含多个 `.md` 文件的文件夹 &#x20;
- 提取文件大小、文件名等元数据 &#x20;
- 保留 Markdown 原有的语法结构（如标题、列表、链接等） &#x20;

### 5. JsonParser &#x20;

**功能**：解析 JSON 格式文件（`.json`），提取结构化数据并转换为文档对象。 &#x20;

**实现特点** &#x20;

- 读取 JSON 文件内容并解析为 Python 字典/列表结构 &#x20;
- 将结构化数据转换为适合 RAG 处理的文本格式 &#x20;
- 支持提取 JSON 文件的元信息（如文件大小、名称等） &#x20;
- 适配包含嵌套结构的复杂 JSON 数据 &#x20;

## 解析器协同工作（AutoParser） &#x20;

各核心解析器通过 `AutoParser` 实现统一调度，`AutoParser` 会根据文件后缀自动选择对应的解析器： &#x20;

- 自动识别文件格式（如 `.pdf`、`.docx`、`.txt` 等） &#x20;
- 支持递归遍历文件夹，批量处理多种格式文件 &#x20;
- 通过配置文件灵活切换解析工具（如 PDF 解析工具可配置） &#x20;
- 统一输出 `Document` 对象列表，包含文档 ID、内容、元数据等信息 &#x20;

这种设计确保了不同格式文档的解析流程标准化，同时保留了各解析器的特性，为 RAG 系统提供了灵活且全面的文档处理能力。

## 接口说明

所有解析器均实现统一的 `parse` 方法，接口规范如下：

### 输入参数

- `path`：文档路径（可以是单个文件路径或文件夹路径）
- `output_dir`（可选）：解析结果输出目录，用于保存图片或转换后的文件

### 输出结果

返回 `Document` 对象列表，每个对象包含：

- `doc_id`：文档唯一标识
- `content`：解析后的文本内容
- `file_name`：文件名
- `metadata`：元信息字典，包含 `file_size`（文件大小）和 `file_type`（文件类型）

## 使用示例

如果只想解析文档并存储到指定位置，可参考如下：

### Pdf 文档解析

```python 
from offline.document_parser.pdf_parser import PdfParser

doc_path = "/path/to/your/pdfs"
output_dir = "/path/to/save/results"
parser = PdfParser()
documents = parser.parse(doc_path, output_dir)
print(f"解析完成，共处理 {len(documents)} 个文件")
```


### Word 文档解析

```python 
from offline.document_parser.doc_parser import DocParser

doc_path = "/path/to/your/documents"
output_dir = "/path/to/save/results"
parser = DocParser()
documents = parser.parse(doc_path, output_dir)
print(f"解析完成，共处理 {len(documents)} 个文件")
```
