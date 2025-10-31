# MinerU 2.0部署

## 目录

- [MinerU简介](#MinerU简介)
- [MinerU私有化部署](#MinerU私有化部署)
  - [1. 软硬件环境准备](#1-软硬件环境准备)
  - [2. 安装依赖包](#2-安装依赖包)
- [API封装](#API封装)
- [调用示例代码](#调用示例代码)

## MinerU简介

MinerU 2带来了诸多重要更新，主要涵盖架构、性能、体验、模型、兼容性等方面。在架构上，深度重构代码组织与交互方式，去除对`pymupdf`的依赖，无需手动编辑JSON配置文件，新增模型自动下载与更新机制。性能优化显著，大幅提升特定分辨率文档的预处理速度、`pipeline`后端批量处理少量页数文档时的后处理速度以及layout分析速度，在满足一定配置的设备上整体解析速度提升超50%。体验上，内置`fastapi service`和`gradio webui`，适配`sglang` 0.4.8版本降低显存要求，支持参数透传和基于配置文件的功能扩展。集成了小参数量、高性能多模态文档解析模型，解析精度超越传统72B级别的VLM，单卡NVIDIA 4090上推理速度峰值吞吐量超10,000 token/s。此外，还解决了一些兼容性问题，支持Python 3.13等，同时优化了多方面的解析效果和在线demo功能。  &#x20;

[https://gitee.com/myhloli/MinerU](https://gitee.com/myhloli/MinerU "https://gitee.com/myhloli/MinerU")

## MinerU私有化部署

由于MinerU官方提供的API14天要更换一次，下面是对MinerU的基于源码方式私有化部署：

### 1. 软硬件环境准备

在开始安装之前，需要确保你的系统满足以下软硬件要求：

| 解析后端      | pipeline                            | vlm-transformers     | vlm-sglang                 |
| --------- | ----------------------------------- | -------------------- | -------------------------- |
| 操作系统      | Linux / Windows / macOS             | Linux / Windows      | Linux / Windows (via WSL2) |
| CPU 推理支持  | ✅                                   | ❌                    | ❌                          |
| GPU 要求    | Turing 及以后架构，6G 显存以上或 Apple Silicon | Turing 及以后架构，8G 显存以上 | Turing 及以后架构，8G 显存以上       |
| 内存要求      | 最低 16G 以上，推荐 32G 以上                 | 最低 16G 以上，推荐 32G 以上  | 最低 16G 以上，推荐 32G 以上        |
| 磁盘空间要求    | 20G 以上，推荐使用 SSD                     | 20G 以上，推荐使用 SSD      | 20G 以上，推荐使用 SSD            |
| Python 版本 | 3.10 - 3.13                         | 3.10 - 3.13          | 3.10 - 3.13                |

### 2. 安装依赖包

1. 安装mineru
   ```bash 
   conda create -n mineru python=3.10 
   conda activate mineru
   pip install uv -i https://mirrors.aliyun.com/pypi/simple
   uv pip install -U "mineru[core]" -i https://mirrors.aliyun.com/pypi/simple 
   ```

   **提示**：`mineru[core]` 包含除 `sglang` 加速外的所有核心功能，兼容 Windows / Linux / macOS 系统，适合绝大多数用户。如果你有使用 `sglang` 加速 VLM 模型推理，或是在边缘设备安装轻量版 client 端等需求，可以参考文档[扩展模块安装指南](https://opendatalab.github.io/MinerU/zh/quick_start/extension_modules/ "扩展模块安装指南")。
2. 使用本地模型
   1. 模型权重下载

      方法一：从 ModelScope下载模型

      将MinerU代码clone到本地，使用python脚本 从ModelScope下载模型文件
      ```python 
      python mineru/cli/models_download.py
      ```

      方法二：使用交互式命令行工具选择模型下载：

      详细参考[如何下载模型文件](https://opendatalab.github.io/MinerU/zh/usage/model_source/#2 "如何下载模型文件")
   2. 配置文件
      - 下载完成后，模型路径会在当前终端窗口输出，并自动写入用户目录下的 `mineru.json`。
      - 您也可以通过将[配置模板文件](https://github.com/opendatalab/MinerU/blob/master/mineru.template.json "配置模板文件")复制到用户目录下并重命名为 `mineru.json` 来创建配置文件。
      - 模型下载到本地后，您可以自由移动模型文件夹到其他位置，同时需要在 `mineru.json` 中更新模型路径。
      - 如您将模型文件夹部署到其他服务器上，请确保将 `mineru.json`文件一同移动到新设备的用户目录中并正确配置模型路径。
      - 如您需要更新模型文件，可以再次运行 `mineru-models-download` 命令，模型更新暂不支持自定义路径，如您没有移动本地模型文件夹，模型文件会增量更新；如您移动了模型文件夹，模型文件会重新下载到默认位置并更新`mineru.json`。
      > windows的用户目录为 "C:\Users\用户名", linux用户目录为 "/home/用户名", macOS用户目录为 "/Users/用户名"
3. 解析代码

   `process_pdf`是核心解析函数，主要功能包括：
   - 自动识别 PDF 类型（普通文本 PDF 或扫描版 PDF），支持多种文件格式，包括 `.pdf`、`.png`、`.jpeg`、`.jpg` 等，可自动将图片文件转换为 PDF 进行处理。
   - 提取文本内容和图片资源，能够根据设置的起始和结束页码进行精准解析，支持多语言识别，可提高 OCR 识别的准确性。
   - 生成 Markdown 格式的输出，支持 LaTeX 公式和表格的解析与输出，能够根据不同的后端和模式进行灵活处理。
   - 可选生成可视化分析结果，提供布局和文本块的可视化分析结果，方便用户进行调试和检查。[http://127.0.0.1:30000\`](`)
   ```markdown 
   output/
     ├── [PDF文件名]/
     │   ├── images/            # 存放提取的图片
     │   ├── [PDF文件名].md     # 生成的Markdown文件
     │   ├── [PDF文件名]_origin.pdf  # 原始 PDF 文件（完整模式）
     │   ├── [PDF文件名]_content_list.json  # 内容列表JSON文件
     │   ├── [PDF文件名]_model.pdf   # 模型可视化结果（完整模式）
     │   ├── [PDF文件名]_middle.pdf   # 模型中间处理结果（完整模式）
     │   ├── [PDF文件名]_layout.pdf  # 布局可视化结果（完整模式）
     │   └── [PDF文件名]_spans.pdf   # 文本块可视化结果（完整模式）

   ```

   ```python 
   import os
   os.environ['MINERU_MODEL_SOURCE'] = "local"

   from pathlib import Path
   from loguru import logger

   from mineru.cli.common import convert_pdf_bytes_to_bytes_by_pypdfium2, prepare_env, read_fn
   from mineru.data.data_reader_writer import FileBasedDataWriter
   from mineru.utils.draw_bbox import draw_layout_bbox, draw_span_bbox
   from mineru.utils.enum_class import MakeMode
   from mineru.backend.vlm.vlm_analyze import doc_analyze as vlm_doc_analyze
   from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
   from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
   from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
   from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make


   def process_pdf(pdf_file_name, output_dir="output", image_subdir="images", simple_output=True, backend="pipeline", method="auto", lang="ch", server_url=None, start_page_id=0, end_page_id=None):
       """
       处理PDF文件，将其转换为Markdown格式并保存相关资源
       :param pdf_file_name: PDF文件名
       :param output_dir: 输出目录，默认为'output'
       :param image_subdir: 图片子目录名，默认为'images'
       :param simple_output: 是否使用简单输出模式，默认为False
       :param backend: 解析PDF的后端，默认为'pipeline'
       :param method: 解析PDF的方法，默认为'auto'
       :param lang: 输入PDF中的语言，默认为'ch'
       :param server_url: 当后端为`vlm-sglang-client`时需要指定的服务器URL
       :param start_page_id: 解析的起始页码，默认为0
       :param end_page_id: 解析的结束页码，默认为None
       """
       # 获取不带后缀的文件名
       name_without_suff = os.path.splitext(os.path.basename(pdf_file_name))[0]
       # 构建图片目录和markdown目录的路径
       local_image_dir = os.path.join(output_dir, output_subdir, image_subdir)
       local_md_dir = output_dir
       # 创建必要的目录
       os.makedirs(local_image_dir, exist_ok=True)
       os.makedirs(local_md_dir, exist_ok=True)

       # 创建文件写入器
       image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
       # 读取PDF文件
       pdf_bytes = read_fn(pdf_file_name)

       pdf_file_names = [name_without_suff]
       pdf_bytes_list = [pdf_bytes]
       p_lang_list = [lang]

       if backend == "pipeline":
           new_pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page_id, end_page_id)
           pdf_bytes_list[0] = new_pdf_bytes

           infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = pipeline_doc_analyze(pdf_bytes_list, p_lang_list, parse_method=method, formula_enable=True, table_enable=True)

           model_list = infer_results[0]
           model_json = model_list.copy()

           images_list = all_image_lists[0]
           pdf_doc = all_pdf_docs[0]
           _lang = lang_list[0]
           _ocr_enable = ocr_enabled_list[0]

           middle_json = pipeline_result_to_middle_json(model_list, images_list, pdf_doc, image_writer, _lang, _ocr_enable, True)

           pdf_info = middle_json["pdf_info"]

           pdf_bytes = pdf_bytes_list[0]

           # 生成Markdown文件和内容列表（无论哪种模式都需要）
           md_content_str = pipeline_union_make(pdf_info, MakeMode.MM_MD, image_dir)
           md_writer.write_string(
               f"{name_without_suff}.md",
               md_content_str,
           )
           content_list = pipeline_union_make(pdf_info, MakeMode.CONTENT_LIST, image_dir)
           md_writer.write_string(
               f"{name_without_suff}_content_list.json",
               str(content_list),
           )
           
           # 仅在完整输出模式下生成额外文件
           if not simple_output:
               # 生成布局可视化文件
               draw_layout_bbox(pdf_info, pdf_bytes, local_md_dir, f"{name_without_suff}_layout.pdf")
               
               # 生成文本块可视化文件
               draw_span_bbox(pdf_info, pdf_bytes, local_md_dir, f"{name_without_suff}_span.pdf")
               
               # 保存原始PDF文件
               md_writer.write(
                   f"{name_without_suff}_origin.pdf",
                   pdf_bytes,
               )
               
               # 保存中间JSON和模型输出
               md_writer.write_string(
                   f"{name_without_suff}_middle.json",
                   str(middle_json),
               )
               md_writer.write_string(
                   f"{name_without_suff}_model.json",
                   str(model_json),
               )
           
           logger.info(f"local output dir is {local_md_dir}")
       else:
           if backend.startswith("vlm-"):
               backend = backend[4:]

           f_draw_span_bbox = False
           parse_method = "vlm"

           pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page_id, end_page_id)

           middle_json, infer_result = vlm_doc_analyze(pdf_bytes, image_writer=image_writer, backend=backend, server_url=server_url)

           pdf_info = middle_json["pdf_info"]

           if not simple_output:
               if True:
                   draw_layout_bbox(pdf_info, pdf_bytes, local_md_dir, f"{name_without_suff}_layout.pdf")

               if f_draw_span_bbox:
                   draw_span_bbox(pdf_info, pdf_bytes, local_md_dir, f"{name_without_suff}_span.pdf")

               if True:
                   md_writer.write(
                       f"{name_without_suff}_origin.pdf",
                       pdf_bytes,
                   )

           image_dir = str(os.path.basename(local_image_dir))

           if simple_output:
               # 简单输出模式：只输出markdown和内容列表
               md_content_str = vlm_union_make(pdf_info, MakeMode.MM_MD, image_dir)
               md_writer.write_string(
                   f"{name_without_suff}.md",
                   md_content_str,
               )
               content_list = vlm_union_make(pdf_info, MakeMode.CONTENT_LIST, image_dir)
               md_writer.write_string(
                   f"{name_without_suff}_content_list.json",
                   str(content_list),
               )
           else:
               # 完整输出模式：输出所有内容
               md_content_str = vlm_union_make(pdf_info, MakeMode.MM_MD, image_dir)
               md_writer.write_string(
                   f"{name_without_suff}.md",
                   md_content_str,
               )
               content_list = vlm_union_make(pdf_info, MakeMode.CONTENT_LIST, image_dir)
               md_writer.write_string(
                   f"{name_without_suff}_content_list.json",
                   str(content_list),
               )

               md_writer.write_string(
                   f"{name_without_suff}_middle.json",
                   str(middle_json),
               )

               model_output = ("\n" + "-" * 50 + "\n").join(infer_result)
               md_writer.write_string(
                   f"{name_without_suff}_model_output.txt",
                   model_output,
               )

           logger.info(f"local output dir is {local_md_dir}")

       # 构建markdown文件的完整路径
       md_file_path = os.path.join(os.getcwd(), local_md_dir, f"{name_without_suff}.md")
       abs_md_file_path = os.path.abspath(md_file_path)

       return abs_md_file_path


   if __name__ == "__main__":
       # 指定要处理的PDF文件名
       pdf_file_name = "/home/hisense/forAI/mjb/MinerU/demo/pdfs/demo1.pdf"
       # 处理PDF文件并获取生成的markdown文件路径
       md_file_path = process_pdf(pdf_file_name, output_dir="/home/hisense/forAI/mjb/MinerU/demo/output", simple_output=False, backend="pipeline")
       # 打印生成的markdown文件路径
       print(md_file_path)
   ```


## API封装

```python 
from flask import Flask, request, send_file, jsonify
import os
os.environ['MINERU_MODEL_SOURCE'] = "local"

import shutil
import zipfile
from scripts.process_pdf import process_pdf
from pathlib import Path
from mineru.cli.common import read_fn, pdf_suffixes, image_suffixes

app = Flask(__name__)


def create_zip_from_directory(directory_path, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, directory_path)
                zipf.write(file_path, arcname)


@app.route('/process_file', methods=['POST'])
def process_file_api():
    # 检查请求中是否包含文件
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = Path(file.filename)
    # 检查文件类型是否支持
    if file_path.suffix.lower() not in pdf_suffixes + image_suffixes:
        return jsonify({'error': f"Unsupported file type: {file_path.suffix}"}), 400

    # 获取文件名（不含扩展名）用于创建子文件夹
    file_stem = file_path.stem
    
    # 创建以文件名命名的临时子文件夹
    temp_subdir = os.path.join('temp', file_stem)
    os.makedirs(temp_subdir, exist_ok=True)
    
    # 保存上传的文件到临时子文件夹
    input_file_path = os.path.join(temp_subdir, file.filename)
    file.save(input_file_path)

    try:
        # 读取文件内容
        pdf_bytes = read_fn(input_file_path)

        # 仅当输入不是PDF时，保存转换后的PDF
        temp_pdf_path = None
        if file_path.suffix.lower() not in pdf_suffixes:
            temp_pdf_path = os.path.join(temp_subdir, f"{file_stem}.pdf")
            with open(temp_pdf_path, 'wb') as f:
                f.write(pdf_bytes)
        else:
            # 输入是PDF，直接使用原文件路径
            temp_pdf_path = input_file_path

        # 处理文件
        markdown_file_path = process_pdf(
            temp_pdf_path,
            output_dir=temp_subdir,
        )

        # 直接在temp_subdir下创建ZIP文件
        name_without_suff = os.path.splitext(os.path.basename(input_file_path))[0]
        zip_file_path = os.path.join(temp_subdir, f"{name_without_suff}.zip")
        create_zip_from_directory(temp_subdir, zip_file_path)

        # 发送ZIP文件作为响应
        return send_file(zip_file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # 仅清理ZIP文件，保留其他临时文件
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6601)
```


1. API 端点 &#x20;
   - URL: `http://localhost:6601/process_file` &#x20;
   - 方法: POST &#x20;
   - 内容类型: multipart/form-data &#x20;
2. 请求参数 &#x20;
   | 参数               | 类型  | 描述                                                 |
   | ---------------- | --- | -------------------------------------------------- |
   | file             | 文件  | 要解析的文件，支持 \`.pdf\`、\`.png\`、\`.jpeg\`、\`.jpg\` 等格式 |
   | output\\\_dir    | 字符串 | 输出目录，默认为 "output"                                  |
   | image\\\_subdir  | 字符串 | 图片子目录，默认为 "images"                                 |
   | simple\\\_output | 布尔值 | 是否使用简单输出，默认为 \`False\`                             |
   | backend          | 字符串 | 解析 PDF 的后端，默认为 "pipeline"                          |
   | method           | 字符串 | 解析 PDF 的方法，默认为 "auto"                              |
   | lang             | 字符串 | 文档语言，默认为 "ch"                                      |
   | server\\\_url    | 字符串 | 服务器 URL，默认为 \`None\`                               |
   | start\_page\_ id | 整数  | 开始解析的页码，默认为 0                                      |
   | end\_page\_ id   | 整数  | 结束解析的页码，默认为 \`None\`                               |
3. 响应 &#x20;
   - 成功: 返回包含所有解析结果的 ZIP 文件 &#x20;
   - 失败: 返回 JSON 格式的错误信息 &#x20;
4. 状态码 &#x20;
   | 状态码 | 描述                     |
   | --- | ---------------------- |
   | 200 | 成功处理并返回 ZIP 文件         |
   | 400 | 请求参数错误，如未提供文件、文件类型不支持等 |
   | 500 | 服务器内部错误                |

## 调用示例代码

工具提供了三种调用示例，可以根据需要选择使用：

```python 
import requests
import os
import zipfile
import io


def parse_pdf_api_to_path(pdf_file_path, output_dir):
    url = "http://localhost:6601/process_pdf"

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 获取 PDF 文件的基础名称（不带扩展名）
    base_filename = os.path.splitext(os.path.basename(pdf_file_path))[0]

    with open(pdf_file_path, 'rb') as pdf_file:
        files = {'pdf_file': pdf_file}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        # 保存返回的 zip 文件到指定目录，使用与 PDF 相同的基础文件名
        output_zip_path = os.path.join(output_dir, f'{base_filename}.zip')
        with open(output_zip_path, 'wb') as f:
            f.write(response.content)
        print(f"Test passed: Received zip file and saved to {output_zip_path}.")
    else:
        print(f"Test failed: {response.status_code} - {response.json()}")


def parse_pdf_api_to_content(pdf_file_path):
    url = "http://localhost:6601/process_pdf"

    # 获取 PDF 文件的基础名称（不带扩展名）
    base_filename = os.path.splitext(os.path.basename(pdf_file_path))[0]

    with open(pdf_file_path, 'rb') as pdf_file:
        files = {'pdf_file': pdf_file}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        # 返回压缩包内容
        print(f"Request successful: Received zip file for {base_filename}.")
        return response.content
    else:
        error_message = f"Request failed: {response.status_code} - {response.json()}"
        print(error_message)
        raise Exception(error_message)


def save_zip_content_to_directory(zip_content, output_dir):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 使用 zipfile 模块解压缩内容
    with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
        z.extractall(output_dir)
    print(f"Files extracted to {output_dir}")


def save_zip_and_content_to_directory(zip_content, output_dir, zip_filename):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 保存压缩包到指定目录
    zip_path = os.path.join(output_dir, zip_filename)
    with open(zip_path, 'wb') as f:
        f.write(zip_content)
    print(f"Zip file saved to {zip_path}")

    # 使用 zipfile 模块解压缩内容
    with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
        z.extractall(output_dir)
    print(f"Files extracted to {output_dir}")


if __name__ == "__main__":
    pdf_file_path = "/path/to/your.pdf"
    output_unzip_dir = "/path/to/output/dir"
    try:
        # 获取压缩包内容
        zip_content = parse_pdf_api_to_content(pdf_file_path)

        # 定义压缩包文件名
        zip_filename = os.path.splitext(os.path.basename(pdf_file_path))[0] + ".zip"

        # 解压并保存到指定目录
        # save_zip_content_to_directory(zip_content, output_unzip_dir)
        # 保存压缩包到指定目录并解压
        save_zip_and_content_to_directory(zip_content, output_unzip_dir, zip_filename)
    except Exception as e:
        print(f"An error occurred: {e}")
    # 将解析内容保存到本地
    # output_dir = "/home/hisense/forAI/mjb/MinerU/demo/test"
    # parse_pdf_api_to_path(pdf_file_path, output_dir)
```


用例1: 直接解压并保存到指定目录

```python 
pdf_file_path = "/path/to/your.pdf"
output_unzip_dir = "/path/to/output/dir"

# 获取压缩包内容
zip_content = parse_pdf_api_to_content(pdf_file_path)

# 解压并保存到指定目录
save_zip_content_to_directory(zip_content, output_unzip_dir)
```


用例2: 保存压缩包到指定目录并解压

```python 
pdf_file_path = "/path/to/your.pdf"
output_unzip_dir = "/path/to/output/dir"

# 获取压缩包内容
zip_content = parse_pdf_api_to_content(pdf_file_path)

# 定义压缩包文件名
zip_filename = os.path.splitext(os.path.basename(pdf_file_path))[0] + ".zip"

# 保存压缩包并解压
save_zip_and_content_to_directory(zip_content, output_unzip_dir, zip_filename)
```


用例3: 将解析内容保存到本地

```python 
pdf_file_path = "/path/to/your.pdf"
output_dir = "/path/to/output/dir"

# 直接调用API并将结果保存到指定目录
parse_pdf_api_to_path(pdf_file_path, output_dir)
```
