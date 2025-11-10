import os
import json
import re

from chunker_utils import merge_headers, split_table_and_text, merge_chunks, BLOCK_SEPARATORS
from langchain_text_splitters import MarkdownHeaderTextSplitter


class RecursiveChunker:
    def __init__(self):
        pass

    def chunk(self, content: str, chunk_params: dict = None):
        chunk_params = chunk_params or {}
        # 预处理
        page_content = re.sub(r'\n{2,}', '\n\n', content)
        page_content = page_content.replace("\n\n", "[[DOUBLE_NEWLINE]]\n")
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False,
        )
        md_header_splits = markdown_splitter.split_text(page_content)
        merged_content = merge_headers(md_header_splits)
        parsed_chunks = split_table_and_text(merged_content)
        final_result = merge_chunks(parsed_chunks, chunk_params, BLOCK_SEPARATORS)

        return [
            {"text": chunk["content"], "index": idx}
            for idx, chunk in enumerate(final_result)
        ]

