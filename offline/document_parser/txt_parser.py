import os

from utils.offline_utils import Document, gen_id


class TxtParser:
    def __init__(self):
        pass

    def parse(self, txt_path: str, output_dir: str = None):
        """
        支持txt_path为文件或文件夹，返回Document列表
        """
        parse_result_list = []

        # 判断是文件还是文件夹
        if os.path.isfile(txt_path) and txt_path.lower().endswith('.txt'):
            txt_files = [txt_path]
        elif os.path.isdir(txt_path):
            txt_files = [os.path.join(txt_path, f) for f in os.listdir(txt_path)
                         if f.lower().endswith('.txt')]
        else:
            raise ValueError(f"txt_path {txt_path} 不是有效的TXT文件或文件夹路径")

        for input_file in txt_files:
            try:
                with open(input_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = ""
                print(f"读取TXT文件失败: {e}")

            filename = os.path.basename(input_file)
            try:
                file_size = os.path.getsize(input_file)
            except Exception:
                file_size = None

            doc_id = gen_id()
            doc = Document(
                doc_id=doc_id,
                content=content,
                metadata=[{"file_size": file_size, "file_type": ".txt"}],
                file_name=filename
            )
            parse_result_list.append(doc)

        return parse_result_list


if __name__ == "__main__":
    txt_path = "./Awesome_RAG/offline/document_parser/output/test.txt"
    txt_parser = TxtParser()
    documents = txt_parser.parse(txt_path)
    print(documents)
