import os
from pdf_parser import PdfParser
from doc_parser import DocParser
from txt_parser import TxtParser
from md_parser import MarkdownParser
from json_parser import JsonParser
from parser_utils import load_yaml_config

from typing import List


class AutoParser:
    """自动根据文件后缀选择解析器，复用parser_config.yaml配置"""

    def __init__(self, config_path: str = "config/parser_config.yaml"):
        # 加载parser_config.yaml配置
        self.config = load_yaml_config(config_path)
        self.pdf_config = self.config["pdf"]

        # 初始化各类解析器
        self.parsers = {
            ".pdf": PdfParser(pdf_parser_tool=self.pdf_config["parser_tool"]),
            ".doc": DocParser(),
            ".docx": DocParser(),
            ".txt": TxtParser(),
            ".md": MarkdownParser(),
            ".json": JsonParser(),
            ".png": PdfParser(pdf_parser_tool=self.pdf_config["parser_tool"]),
            ".jpg": PdfParser(pdf_parser_tool=self.pdf_config["parser_tool"]),
            ".jpeg": PdfParser(pdf_parser_tool=self.pdf_config["parser_tool"]),
        }

    def parse(self, input_path: str, output_dir: str = None) -> List:
        """解析文件或文件夹，返回Document列表"""
        all_docs = []

        if os.path.isfile(input_path):
            ext = os.path.splitext(input_path)[1].lower()
            if ext not in self.parsers:
                raise ValueError(f"不支持的文件格式: {ext}，文件路径: {input_path}")
            docs = self.parsers[ext].parse(input_path, output_dir)
            all_docs.extend(docs)
        elif os.path.isdir(input_path):
            # 递归遍历文件夹
            for root, dirs, files in os.walk(input_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.parsers:
                        file_path = os.path.join(root, file)
                        docs = self.parsers[ext].parse(file_path, output_dir)
                        all_docs.extend(docs)
        else:
            raise ValueError(f"输入路径 {input_path} 不是有效的文件或文件夹路径")

        return all_docs


if __name__ == "__main__":
    config_path = "./Awesome_RAG/config/parser_config.yaml"
    input_dir = "./Awesome_RAG/data/test"
    parser = AutoParser(config_path)
    docs = parser.parse(input_dir, output_dir="output")
    for doc in docs:
        print(doc)
        print("="*50)
