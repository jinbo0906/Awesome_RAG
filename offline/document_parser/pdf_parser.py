from utils.offline_utils import Document, gen_id
from offline.document_parser.MinerU.demo.mineru_parser import MineruParser


class PdfParser:
    def __init__(self, pdf_parser_tool: str = None):
        self.pdf_parser_tool = pdf_parser_tool if pdf_parser_tool else "mineru"

    def parse(self, pdf_path: str, output_dir: str = None):

        parse_result_list = []

        if self.pdf_parser_tool == "mineru":
            parser = MineruParser(pdf_files_path=pdf_path, output_dir=output_dir)
            parse_results = parser.run()

        for parse_result in parse_results:
            doc_id = gen_id()
            doc = Document(
                doc_id=doc_id,
                content=parse_result['md_content'],
                metadata=parse_result['pdf_info'],
                file_name=parse_result['pdf_name'],
            )
            parse_result_list.append(doc)

        return parse_result_list


if __name__ == "__main__":
    # Example usage
    pdf_path = "./Awesome_RAG/offline/document_parser/MinerU/demo/test1"
    pdf_parser = PdfParser()
    document = pdf_parser.parse(pdf_path)
    print(document)
