import json
import os
import sys
import click
import requests
from loguru import logger

from mineru.utils.enum_class import ModelPath
from mineru.utils.models_download_utils import auto_download_and_get_model_root_path


def download_json(url):
    """下载JSON文件"""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def download_and_modify_json(url, local_filename, modifications):
    """下载JSON并修改内容"""
    if os.path.exists(local_filename):
        data = json.load(open(local_filename))
        config_version = data.get('config_version', '0.0.0')
        if config_version < '1.3.1':
            data = download_json(url)
    else:
        data = download_json(url)

    # 修改内容
    for key, value in modifications.items():
        if key in data:
            if isinstance(data[key], dict):
                # 如果是字典，合并新值
                data[key].update(value)
            else:
                # 否则直接替换
                data[key] = value

    # 保存修改后的内容
    with open(local_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def configure_model(model_dir, model_type):
    """配置模型"""
    json_url = 'https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/mineru.template.json'
    config_file_name = os.getenv('MINERU_TOOLS_CONFIG_JSON', 'mineru.json')
    home_dir = os.path.expanduser('~')
    config_file = os.path.join(home_dir, config_file_name)

    json_mods = {
        'models-dir': {
            f'{model_type}': model_dir
        }
    }

    download_and_modify_json(json_url, config_file, json_mods)
    logger.info(f'The configuration file has been successfully configured, the path is: {config_file}')


def download_pipeline_models():
    """下载Pipeline模型"""
    model_paths = [
        ModelPath.doclayout_yolo,
        ModelPath.yolo_v8_mfd,
        ModelPath.unimernet_small,
        ModelPath.pytorch_paddle,
        ModelPath.layout_reader,
        ModelPath.slanet_plus,
        ModelPath.vlm_root_hf,
        ModelPath.vlm_root_modelscope,
        ModelPath.pipeline_root_modelscope,
        ModelPath.pipeline_root_hf,
        ModelPath.doclayout_yolo,
    ]
    download_finish_path = ""
    for model_path in model_paths:
        logger.info(f"Downloading model: {model_path}")
        download_finish_path = auto_download_and_get_model_root_path(model_path, repo_mode='pipeline')
    logger.info(f"Pipeline models downloaded successfully to: {download_finish_path}")
    configure_model(download_finish_path, "pipeline")


def download_vlm_models():
    """下载VLM模型"""
    download_finish_path = auto_download_and_get_model_root_path("/", repo_mode='vlm')
    logger.info(f"VLM models downloaded successfully to: {download_finish_path}")
    configure_model(download_finish_path, "vlm")


def download_models(model_source, model_type):
    """自动化下载模型"""
    if os.getenv('MINERU_MODEL_SOURCE', None) is None:
        os.environ['MINERU_MODEL_SOURCE'] = model_source

    logger.info(f"Downloading {model_type} model from {os.getenv('MINERU_MODEL_SOURCE', None)}...")

    try:
        if model_type == 'pipeline':
            download_pipeline_models()
        elif model_type == 'vlm':
            download_vlm_models()
        elif model_type == 'all':
            download_pipeline_models()
            download_vlm_models()
        else:
            print(f"Unsupported model type: {model_type}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        logger.exception(f"An error occurred while downloading models: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    download_models(model_source="modelscope", model_type="all")
