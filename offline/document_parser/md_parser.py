import os

from offline.document_parser.parser_utils import Document, gen_id


class MarkdownParser:
    def __init__(self):
        pass

    def parse(self, md_path: str, output_dir: str = None):
        """
        支持md_path为文件或文件夹，返回Document列表
        """
        parse_result_list = []

        # 判断是文件还是文件夹
        if os.path.isfile(md_path) and md_path.lower().endswith('.md'):
            md_files = [md_path]
        elif os.path.isdir(md_path):
            md_files = [os.path.join(md_path, f) for f in os.listdir(md_path)
                        if f.lower().endswith('.md')]
        else:
            raise ValueError(f"md_path {md_path} 不是有效的Markdown文件或文件夹路径")

        for input_file in md_files:
            try:
                with open(input_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = ""
                print(f"读取Markdown文件失败: {e}")

            filename = os.path.basename(input_file)
            try:
                file_size = os.path.getsize(input_file)
            except Exception:
                file_size = None

            doc_id = gen_id()
            doc = Document(
                doc_id=doc_id,
                content=content,
                metadata=[{"file_size": file_size, "file_type": ".md"}],
                file_name=filename
            )
            parse_result_list.append(doc)

        return parse_result_list


if __name__ == "__main__":
    md_path = "/home/hisense/forAI/mjb/Awesome_RAG/offline/document_parser/output/test.md"
    md_parser = MarkdownParser()
    document = md_parser.parse(md_path)
    print(document)
