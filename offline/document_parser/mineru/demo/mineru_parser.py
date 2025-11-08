import copy
import json
import os
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
from mineru.utils.guess_suffix_or_lang import guess_suffix_by_path


class MineruParser:
    def __init__(self, pdf_files_path, output_dir=None, lang="ch", method="auto", start_page_id=0, end_page_id=None):
        """
        pdf_files_path: 可以是文件夹路径，也可以是单个文件路径
        """
        self.pdf_files_path = Path(pdf_files_path)
        self.output_dir = output_dir
        self.lang = lang
        self.method = method
        self.start_page_id = start_page_id
        self.end_page_id = end_page_id
        self.pdf_suffixes = ["pdf"]
        self.image_suffixes = ["png", "jpeg", "jp2", "webp", "gif", "bmp", "jpg"]

    def do_parse(
            self,
            pdf_file_names,
            pdf_bytes_list,
            p_lang_list,
            parse_method="auto",
            formula_enable=True,
            table_enable=True,
            f_draw_layout_bbox=True,
            f_draw_span_bbox=True,
            f_dump_middle_json=True,
            f_dump_model_output=True,
            f_dump_orig_pdf=True,
            f_dump_content_list=True,
            f_make_md_mode=MakeMode.MM_MD,
            start_page_id=0,
            end_page_id=None,
    ):
        parse_output = []

        for idx, pdf_bytes in enumerate(pdf_bytes_list):
            new_pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page_id, end_page_id)
            pdf_bytes_list[idx] = new_pdf_bytes

        infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = pipeline_doc_analyze(
            pdf_bytes_list, p_lang_list, parse_method=parse_method, formula_enable=formula_enable,
            table_enable=table_enable
        )

        for idx, model_list in enumerate(infer_results):
            pdf_info_dict = {}
            model_json = copy.deepcopy(model_list)
            pdf_file_name = pdf_file_names[idx]
            pdf_info_dict["pdf_name"] = pdf_file_name
            if self.output_dir is None:
                local_image_dir, local_md_dir = None, None
                image_writer, md_writer = None, None
            else:
                local_image_dir, local_md_dir = prepare_env(self.output_dir, pdf_file_name, parse_method)
                image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)

            images_list = all_image_lists[idx]
            pdf_doc = all_pdf_docs[idx]
            _lang = lang_list[idx]
            _ocr_enable = ocr_enabled_list[idx]
            middle_json = pipeline_result_to_middle_json(model_list, images_list, pdf_doc, image_writer, _lang,
                                                         _ocr_enable, formula_enable)

            pdf_info = middle_json["pdf_info"]

            pdf_info_dict["pdf_info"] = pdf_info

            pdf_bytes = pdf_bytes_list[idx]
            md_content = self._process_output(
                pdf_info, pdf_bytes, pdf_file_name, local_md_dir, local_image_dir,
                md_writer, f_draw_layout_bbox, f_draw_span_bbox, f_dump_orig_pdf,
                f_dump_content_list, f_dump_middle_json, f_dump_model_output,
                f_make_md_mode, middle_json, model_json, is_pipeline=True
            )
            pdf_info_dict["md_content"] = md_content
            parse_output.append(pdf_info_dict)
        return parse_output

    def _process_output(
            self,
            pdf_info,
            pdf_bytes,
            pdf_file_name,
            local_md_dir,
            local_image_dir,
            md_writer,
            f_draw_layout_bbox,
            f_draw_span_bbox,
            f_dump_orig_pdf,
            f_dump_content_list,
            f_dump_middle_json,
            f_dump_model_output,
            f_make_md_mode,
            middle_json,
            model_output=None,
            is_pipeline=True,
            f_dump_md=True,
    ):
        """处理输出文件"""
        make_func = pipeline_union_make if is_pipeline else vlm_union_make
        image_dir = str(os.path.basename(local_image_dir)) if local_image_dir else ""
        md_content_str = make_func(pdf_info, f_make_md_mode, image_dir)

        # 如果没有md_writer，说明不需要保存文件
        if md_writer is None:
            return md_content_str

        if f_draw_layout_bbox:
            draw_layout_bbox(pdf_info, pdf_bytes, local_md_dir, f"{pdf_file_name}_layout.pdf")

        if f_draw_span_bbox:
            draw_span_bbox(pdf_info, pdf_bytes, local_md_dir, f"{pdf_file_name}_span.pdf")

        if f_dump_orig_pdf:
            md_writer.write(
                f"{pdf_file_name}_origin.pdf",
                pdf_bytes,
            )

        if f_dump_md:
            md_writer.write_string(
                f"{pdf_file_name}.md",
                md_content_str,
            )

        if f_dump_content_list:
            content_list = make_func(pdf_info, MakeMode.CONTENT_LIST, image_dir)
            md_writer.write_string(
                f"{pdf_file_name}_content_list.json",
                json.dumps(content_list, ensure_ascii=False, indent=4),
            )

        if f_dump_middle_json:
            md_writer.write_string(
                f"{pdf_file_name}_middle.json",
                json.dumps(middle_json, ensure_ascii=False, indent=4),
            )

        if f_dump_model_output:
            md_writer.write_string(
                f"{pdf_file_name}_model.json",
                json.dumps(model_output, ensure_ascii=False, indent=4),
            )

        logger.info(f"local output dir is {local_md_dir}")
        return md_content_str

    def parse_doc(self, path_list):
        try:
            file_name_list = []
            pdf_bytes_list = []
            lang_list = []
            for path in path_list:
                file_name = str(Path(path).stem)
                pdf_bytes = read_fn(path)
                file_name_list.append(file_name)
                pdf_bytes_list.append(pdf_bytes)
                lang_list.append(self.lang)
            parse_result = self.do_parse(
                pdf_file_names=file_name_list,
                pdf_bytes_list=pdf_bytes_list,
                p_lang_list=lang_list,
                parse_method=self.method,
                start_page_id=self.start_page_id,
                end_page_id=self.end_page_id
            )
            return parse_result
        except Exception as e:
            logger.exception(e)
            return None

    def run(self):
        doc_path_list = []

        if self.pdf_files_path.is_dir():
            # 输入为文件夹，遍历所有文件
            for doc_path in self.pdf_files_path.glob('*'):
                if guess_suffix_by_path(doc_path) in self.pdf_suffixes + self.image_suffixes:
                    doc_path_list.append(doc_path)
        elif self.pdf_files_path.is_file():
            # 输入为单个文件
            if guess_suffix_by_path(self.pdf_files_path) in self.pdf_suffixes + self.image_suffixes:
                doc_path_list.append(self.pdf_files_path)
            else:
                logger.warning(f"File {self.pdf_files_path} is not a supported type.")
        else:
            logger.error(f"Input path {self.pdf_files_path} does not exist.")
            return []

        os.environ['MINERU_MODEL_SOURCE'] = "modelscope"
        parse_results = self.parse_doc(doc_path_list)
        return parse_results


if __name__ == '__main__':
    pdf_files_dir = "/home/hisense/forAI/mjb/Awesome_RAG/offline/document_parser/MinerU/demo/test1/demo2.pdf"
    # output_dir = "/home/hisense/forAI/mjb/Awesome_RAG/offline/document_parser/MinerU/output"
    parser = MineruParser(pdf_files_dir)
    parse_results = parser.run()
    for i, parse_result_item in enumerate(parse_results):
        print(f"{i}th parse result:")
        print(parse_result_item)
