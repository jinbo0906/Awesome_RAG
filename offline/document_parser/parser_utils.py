import yaml
import uuid

from pydantic import BaseModel
from typing import Dict, Any, List


class Document(BaseModel):
    """表示处理后的文档"""
    content: str
    metadata: List[Dict[str, Any]]
    file_name: str
    doc_id: str


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """加载YAML配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def gen_id() -> str:
    return uuid.uuid4().hex


if __name__ == '__main__':
    print(gen_id())
