import os
from typing import List

from recursive_chunker import RecursiveChunker
from semantic_chunker import SemanticChunker
from self_defined_chunker import SelfDefinedChunker
from small2big_chunker import Small2bigChunker

from utils.offline_utils import load_yaml_config, Document, gen_id


class AutoChunker:
    def __init__(self, config_path: str = "config/chunker_config.yaml"):
        self.config = load_yaml_config(config_path)
        self.chunkers = {
            "fixed": RecursiveChunker(),
            "self_defined": SelfDefinedChunker(),
            "semantic": SemanticChunker(),
            "small2big": Small2bigChunker(),
        }

    def chunk(
        self,
        parser_results: List[Document],
        chunk_method: str = None,
        **kwargs
    ) -> List[dict]:
        """
        输入解析后内容（List[Document]），根据切片方法返回切片后内容
        :param parser_results: 文档解析模块的输出（List[Document]）
        :param chunk_method: 切片方法（如 'fixed'、'semantic' 等）
        :param kwargs: 其他切片参数（只需传入需要覆盖的部分）
        :return: List[dict]，每个 dict 是一个切片
        """
        # 1. 选择切片方法
        method = chunk_method or self.config.get("chunk_method", "fixed")
        chunker = self.chunkers.get(method)
        if not chunker:
            raise ValueError(f"不支持的切片方法: {method}")

        # 2. 获取该方法的默认参数
        method_params = self.config.get(method, {})
        # 3. 用户传入的参数覆盖默认参数
        method_params.update(kwargs)

        # 4. 支持批量文档切片
        results = []
        for doc in parser_results:
            # 使用 doc.content 作为切片输入
            chunks = chunker.chunk(doc.content, method_params)
            for idx, chunk in enumerate(chunks):
                # 针对 small2big 方法，获取 segment_text 和 sentence_text
                if method == "small2big":
                    segment_text = chunk.get("segment_text", "")
                    sentence_text = chunk.get("sentence_text", "")
                else:
                    segment_text = ""
                    sentence_text = ""
                results.append({
                    "chunk_method": method,
                    "doc_id": doc.doc_id,
                    "chunk_id": gen_id(),
                    "chunk_index": chunk.get("index", ""),
                    "text": chunk.get("text", ""),
                    "segment_text": segment_text,
                    "sentence_text": sentence_text,
                    "file_name": doc.file_name,
                    "metadata": doc.metadata,
                })
        return results


if __name__ == "__main__":
    from offline.document_parser.auto_parser import AutoParser
    parser_config_path = "/home/hisense/forAI/mjb/Awesome_RAG/config/parser_config.yaml"
    chunker_config_path = "/home/hisense/forAI/mjb/Awesome_RAG/config/chunker_config.yaml"
    input_dir = "/home/hisense/forAI/mjb/Awesome_RAG/data/test"
    parser = AutoParser(parser_config_path)
    parser_result = parser.parse(input_dir, output_dir="output")
    chunker = AutoChunker(chunker_config_path)
    chunk_result = chunker.chunk(parser_result)
    for chunk in chunk_result:
        print(chunk.get("text"))
        print("="*50)



