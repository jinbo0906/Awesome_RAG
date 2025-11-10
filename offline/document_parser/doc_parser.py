import os
import re
import subprocess
from bs4 import BeautifulSoup
import mammoth
from markitdown import MarkItDown
import base64

from utils.offline_utils import Document, gen_id


class DocParser:
    def __init__(self):
        self.markitdown = MarkItDown()

    def process_markdown(self, text_content, img_list_urls):
        pattern = r'!\[(.*?)\]\((.*?)\s*(?:"(.*?)")?\)'
        image_counter = 0

        def replace_image_match(match):
            nonlocal image_counter
            replacement, new_counter = self.replace_image_url(match, img_list_urls, image_counter)
            image_counter = new_counter
            return replacement

        text_content = re.sub(pattern, replace_image_match, text_content)
        return text_content

    def replace_image_url(self, match, img_list_urls, image_counter):
        alt_text = match.group(1)
        old_url = match.group(2)
        title = match.group(3) if match.group(3) else ""
        # 用本地图片路径替换
        if image_counter < len(img_list_urls) and img_list_urls[image_counter]:
            new_url = img_list_urls[image_counter]
        else:
            new_url = ""
        replacement = f'![{alt_text}]({new_url} "{title}")' if title else f'![{alt_text}]({new_url})'
        return replacement, image_counter + 1

    def parse(self, doc_path: str, output_dir: str = None):
        parse_result_list = []

        # 判断是文件还是文件夹
        if os.path.isfile(doc_path) and doc_path.lower().endswith(('.doc', '.docx')):
            doc_files = [doc_path]
        elif os.path.isdir(doc_path):
            doc_files = [os.path.join(doc_path, f) for f in os.listdir(doc_path)
                         if f.lower().endswith(('.doc', '.docx'))]
        else:
            raise ValueError(f"doc_path {doc_path} 不是有效的文件或文件夹路径")

        for input_file in doc_files:
            raw_file_name = os.path.basename(input_file)
            sf = ".doc" if input_file.lower().endswith(".doc") else ".docx"
            img_list_urls = []

            try:
                file_size = os.path.getsize(input_file)
            except Exception:
                file_size = None

            try:
                if sf == ".doc":
                    output_directory = "./tmp/"
                    os.makedirs(output_directory, exist_ok=True)
                    subprocess.run(
                        ['libreoffice', '--headless', '--convert-to', 'docx', '--outdir', output_directory, input_file],
                        check=True
                    )
                    temp_file_path = os.path.join(output_directory, os.path.splitext(raw_file_name)[0] + ".docx")
                    text_content = self.markitdown.convert(temp_file_path).text_content
                    result = mammoth.convert_to_html(temp_file_path, style_map=None)
                else:
                    text_content = self.markitdown.convert(input_file).text_content
                    result = mammoth.convert_to_html(input_file, style_map=None)

                html_content = result.value
                soup = BeautifulSoup(html_content, "html.parser")
                images = soup.find_all("img")

                if output_dir:
                    # 保存图片到本地，并生成本地路径
                    img_output_dir = os.path.join(output_dir, os.path.splitext(raw_file_name)[0], "images")
                    os.makedirs(img_output_dir, exist_ok=True)
                    for idx, img in enumerate(images):
                        if "src" in img.attrs and img["src"].startswith("data:image"):
                            img_data = img["src"].split(",", 1)[1]
                            img_bytes = base64.b64decode(img_data)
                            img_path = os.path.join(img_output_dir, f"{os.path.splitext(raw_file_name)[0]}_{idx}.png")
                            with open(img_path, 'wb') as f:
                                f.write(img_bytes)
                            img_list_urls.append(img_path)
                        else:
                            img_list_urls.append("")
                else:
                    # 不保存图片，仅保留文本内容
                    img_list_urls = [""] * len(images)

                md_content = self.process_markdown(text_content, img_list_urls)

                doc_id = gen_id()
                doc = Document(
                    doc_id=doc_id,
                    content=md_content,
                    metadata=[{"file_size": file_size, "file_type": sf}],
                    file_name=raw_file_name,
                )
                parse_result_list.append(doc)

                # 如果需要保存md到本地
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    md_file_path = os.path.join(output_dir, f"{os.path.splitext(raw_file_name)[0]}.md")
                    with open(md_file_path, "w", encoding="utf-8") as f:
                        f.write(md_content)

            except Exception as e:
                print(f"解析 {input_file} 失败: {e}")
            finally:
                if sf == ".doc":
                    temp_file_path = os.path.join("./tmp/", os.path.splitext(raw_file_name)[0] + ".docx")
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)

        return parse_result_list


if __name__ == "__main__":
    # Example usage
    doc_path = "./Awesome_RAG/data/decrypt"
    output_dir = "./Awesome_RAG/offline/document_parser/output"
    doc_parser = DocParser()
    documents = doc_parser.parse(doc_path, output_dir)
    print(documents)
