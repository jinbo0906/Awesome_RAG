import os

from utils.offline_utils import Document, gen_id  # 如果你有gen_id方法


class JsonParser:
    def __init__(self):
        pass

    def parse(self, json_path: str, output_dir: str = None):
        """
        支持json_path为文件或文件夹，返回Document列表
        """
        parse_result_list = []

        # 判断是文件还是文件夹
        if os.path.isfile(json_path) and json_path.lower().endswith('.json'):
            json_files = [json_path]
        elif os.path.isdir(json_path):
            json_files = [os.path.join(json_path, f) for f in os.listdir(json_path)
                          if f.lower().endswith('.json')]
        else:
            raise ValueError(f"json_path {json_path} 不是有效的JSON文件或文件夹路径")

        for input_file in json_files:
            try:
                with open(input_file, "r", encoding="utf-8") as f:
                    content_str = f.read()
                    # content_json = json.loads(content_str)  # 如需解析可用
            except Exception as e:
                content_str = ""
                print(f"读取JSON文件失败: {e}")

            filename = os.path.basename(input_file)
            try:
                file_size = os.path.getsize(input_file)
            except Exception:
                file_size = None

            doc_id = gen_id()  # 或 uuid.uuid4().hex

            doc = Document(
                doc_id=doc_id,
                content=content_str,
                metadata=[{"file_size": file_size, "file_type": ".json"}],
                file_name=filename
            )
            parse_result_list.append(doc)

        return parse_result_list


if __name__ == "__main__":
    json_path = "./Awesome_RAG/data/test/dev.json"
    json_parser = JsonParser()
    documents = json_parser.parse(json_path)
    print(documents)
