"""资料目录与文件枚举；Python 3.10+，仅标准库。"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]

def catalog():
    return json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))['items']

def safe_path(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError(f'路径超出资料目录：{relative}')
    return path

def sources(base):
    # README、图表和数据都属于当前公开物料，隐式忽略仅限运行缓存。
    ignored = {'.git', '.venv', '__pycache__', '运行结果', 'private', 'node_modules'}
    return sorted(p for p in base.rglob('*') if p.is_file()
                  and not ignored.intersection(p.relative_to(base).parts)
                  and p.suffix not in {'.pyc', '.tmp', '.bak'})

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
