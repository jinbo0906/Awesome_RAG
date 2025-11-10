import re
import string
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Callable

ZH_PUNCTUATION = (
        "＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､"
        + "\u3000、〃〈〉《》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏﹑﹔·．！？｡。"
)
BLOCK_SEPARATORS = ["\n\n", "\n", "####", "###", "##", "#", "```", "。", "，", ";"]
SEGMENT_SEPARATORS = ["\n", "。", "!", "！", "?", "？", "……", "…", "."]
ZH_SEGMENT_SEPARATORS = ["\n", "。", "!", "！", "?", "？", "……", "…", "；", ";"]
SENTENCE_SEPARATORS = ["\n", "。", "!", "！", "?", "？", "……", "…", "；", ";", "，", ".,", " "]
ZH_SENTENCE_SEPARATORS = ["\n", "。", "!", "！", "?", "？", "……", "…", "；", ";", ","]
PUNCTUATIONS = string.punctuation + ZH_PUNCTUATION
MAX_BLOCK_LENGTH = 10240
LLM_API_URL = ""
LLM_API_KEY = ""
LUMBERCHUNKER_SYSTEM_PROMPT = """
你将收到一份文档，文档中的段落以“ID XXXX: <文本>”的格式标识。

任务：找到第一个内容明显与前面段落发生变化的段落（不是第一个段落）。

输出：返回发生内容变化的段落ID，格式必须为：“Answer: ID XXXX”。

注意：
1. 你需要理解多个连续句子上下文，保持分段后整段内容的完整性、上下文的连贯性。
2. 标题（如"ID X: # xxx"、"ID X: # 一、xxx"等）必须与其下属内容合并为一个内容块，不能单独分块。
3. 小标题（如"ID X: 1. xxx"）也必须与其下属内容合并为一个内容块。
4. 表格说明（如"ID X: 其中，xxx"、"ID X: 表1说明"等）必须与其后的表格（如"ID X: | ... |"或"ID X: [TABLE_PLACEHOLDER]"）合并为一个内容块。
5. 图片（如"ID X: ![](xxx)"）必须与其前后的说明性文本合并为一个内容块。
6. 请避免将相关内容拆分到不同块，保证每个内容块的语义完整。
7. 避免将过多段落分为一组。请在识别内容变化和保持分组合理之间取得平衡。
"""


def is_char_chinese(ch: str) -> bool:
    return 0x4E00 <= ord(ch) <= 0x9FFF


def is_text_chinese(text: str) -> bool:
    if not text:
        return False
    ch_cnt = sum(1 for ch in text if is_char_chinese(ch))
    return ch_cnt / max(len(text), 1) > 0.2


def is_blank_or_punct(text: str) -> bool:
    return not re.sub(rf"[{re.escape(PUNCTUATIONS)}\s]", "", text)


def merge_broken_markdown_links_in_doc(doc: str) -> str:
    """
    在整个文档中合并被换行符分割的 markdown 图片和链接 url,防止url被切断
    """
    pattern = re.compile(r'(!?\[.*?\]\()([^\)]*?)(\))', re.DOTALL)

    def replacer(match):
        prefix = match.group(1)
        url = match.group(2).replace('\n', '')  # 去掉 url 内部的换行
        suffix = match.group(3)
        return prefix + url + suffix

    return pattern.sub(replacer, doc)


def extract_html_tables(doc: str):
    """
    提取所有html表格及其在原文中的位置
    返回: tables, table_spans
    tables: [表格html字符串, ...]
    table_spans: [(start, end), ...]
    防止表格被切断
    """
    table_pattern = re.compile(r'(<table[\s\S]*?</table>)', re.IGNORECASE)
    tables = []
    table_spans = []
    for match in table_pattern.finditer(doc):
        tables.append(match.group(1))
        table_spans.append(match.span(1))
    return tables, table_spans


def split_text_chunk(text: str, separators: list, chunk_size: int, chunk_overlap: int = 0) -> List[str]:
    """
    智能分块，适配 markdown 文档，防止分隔符截断，自动去除多余空白
    """
    splitter = RecursiveCharacterTextSplitter(
        separators=separators,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        keep_separator="end",
        length_function=len,
    )
    res = splitter.split_text(text)
    adjusted = []
    for i, chunk in enumerate(res):
        chunk = chunk.strip()
        # 检查是否以标题分隔符结尾，防止分隔符被截断
        matched_sep = next((sep for sep in ["####", "###", "##", "#"]
                            if chunk.endswith(sep)), None)
        if matched_sep:
            sep_with_space = matched_sep + " "
            chunk = chunk[: -len(sep_with_space)].strip()
            adjusted.append(chunk)
            # 把分隔符合并到下一个块
            if i + 1 < len(res):
                res[i + 1] = sep_with_space + res[i + 1]
            else:
                adjusted.append(sep_with_space)
        else:
            adjusted.append(chunk)
    # 去除空块
    return [item for item in adjusted if item]


def merge_headers(md_header_splits) -> List[Dict]:
    merged_content = []
    for doc in md_header_splits:
        header_1 = doc.metadata.get("Header 1", "")
        header_2 = doc.metadata.get("Header 2", "")
        new_page_content = doc.page_content

        if merged_content:
            last_doc_dict = merged_content[-1]
            last_metadata = last_doc_dict["metadata"]
            last_header_1 = last_metadata.get("Header 1", "")
            last_header_2 = last_metadata.get("Header 2", "")

            if not header_1 and not header_2 and not last_header_1 and not last_header_2:
                merged_content.append({"metadata": doc.metadata, "page_content": new_page_content})
            elif last_header_1 == header_1 and last_header_2 == header_2:
                last_doc_dict["page_content"] += "\n" + new_page_content.strip()
                last_doc_dict["metadata"] = doc.metadata
            else:
                merged_content.append({"metadata": doc.metadata, "page_content": new_page_content})
        else:
            merged_content.append({"metadata": doc.metadata, "page_content": new_page_content})
    for doc in merged_content:
        doc["page_content"] = doc["page_content"].replace("[[DOUBLE_NEWLINE]]", "\n")
    return merged_content


def split_table_and_text(merged_content) -> List[Dict]:
    parsed_chunks = []
    table_pattern = re.compile(r"(^\|.*\|$)|(<table[\s\S]*?</table>)", re.IGNORECASE)

    for doc in merged_content:
        lines = doc["page_content"].split("\n")
        process_lines(lines, table_pattern, parsed_chunks)
    return parsed_chunks


def process_lines(lines, table_pattern, parsed_chunks):
    """
    复杂版：支持多行表格、标题与表格/文本关联
    """
    is_table = False
    table_list = []
    text_list = []
    title = ""

    def extract_title_and_add_text_chunk(text_list, parsed_chunks):
        title = ""
        if text_list:
            # 确定标题候选
            if len(text_list) > 1 and text_list[-1] == "\n":
                title_candidate = text_list[-2].strip()
            else:
                title_candidate = text_list[-1].strip()

            # 提取标题
            if title_candidate:
                title = title_candidate
                # 移除标题部分
                if len(text_list) > 1 and text_list[-1] == "\n":
                    text_list = text_list[:-2]
                else:
                    text_list = text_list[:-1]

            # 添加文本块
            parsed_chunks.append({
                "type": "text",
                "content": re.sub(r'\n{3,}', '\n\n', "\n".join(text_list)).strip()
            })
            text_list = []

        return title, text_list

    def add_table_chunk(table_list, title, parsed_chunks):
        table_content = "\n".join(table_list)
        parsed_chunks.append({"type": "table", "content": table_content, "title": title})

    def process_remaining_content(is_table, table_list, text_list, title, parsed_chunks):
        if is_table and table_list:
            add_table_chunk(table_list, title, parsed_chunks)
        elif text_list:
            text_chunk = "\n".join(text_list)
            if text_chunk.strip():
                parsed_chunks.append({"type": "text", "content": text_chunk})

    for line in lines:
        line = line.strip() or "\n"
        if table_pattern.match(line):
            # 遇到表格行
            if not is_table:
                # 表格块开始，先处理前面的文本块和标题
                title, text_list = extract_title_and_add_text_chunk(text_list, parsed_chunks)
                is_table = True
                table_list = []
            table_list.append(line)
        else:
            # 遇到文本行
            if is_table:
                # 表格块结束，处理表格块
                add_table_chunk(table_list, title, parsed_chunks)
                is_table = False
                table_list = []
                title = ""
            text_list.append(line)

    # 处理最后剩余内容
    process_remaining_content(is_table, table_list, text_list, title, parsed_chunks)


def merge_chunks(parsed_chunks, chunk_params, separators) -> List[Dict]:
    final_result = []
    buffer = {"type": "text", "content": ""}
    chunk_size = chunk_params.get("chunk_size", 1000)
    chunk_overlap = chunk_params.get("chunk_overlap", 0)

    def flush_buffer():
        nonlocal buffer
        if buffer["content"].strip():
            final_result.append(buffer.copy())
        buffer = {"type": "text", "content": ""}

    for chunk in parsed_chunks:
        if chunk["type"] == "table":
            chunk_str = f"{chunk.get('title', '')}\n{chunk['content']}" if chunk.get('title') else chunk['content']
        else:
            text = chunk["content"]
            chunks = [text]
            if len(text) > chunk_size:
                chunks = split_text_chunk(text, separators, chunk_size, chunk_overlap)
            for chunk in chunks:
                if len(buffer["content"]) + len(chunk) > chunk_size:
                    flush_buffer()
                buffer["content"] += ("\n" + chunk if buffer["content"] else chunk)
            continue
        if len(buffer["content"]) + len(chunk_str) > chunk_size:
            flush_buffer()
        buffer["content"] += ("\n" + chunk_str if buffer["content"] else chunk_str)
    flush_buffer()
    for i in range(len(final_result)):
        final_result[i]["content"] = re.sub(r'\n{2,}', '\n', final_result[i]["content"].strip())
    return final_result
