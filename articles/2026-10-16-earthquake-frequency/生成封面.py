"""封面：Codex生成的无文字“地球火环”插画，裁成2.35:1横版与1:1方版，不叠加文字。"""
from pathlib import Path
import json

from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '配图'
SRC = OUT / '封面_AI原图.png'   # 1672×941，主体在 y≈135—755
TOP = 90                        # 横版裁切起点
SQ_X = 365                      # 方版裁切起点（以地球为中心）


def main():
    im = Image.open(SRC).convert('RGB')
    w = im.width
    h = round(w / 2.35)
    im.crop((0, TOP, w, TOP + h)).resize((1800, 766), Image.LANCZOS).save(OUT / '封面_AI.png', optimize=True)
    side = im.height
    im.crop((SQ_X, 0, SQ_X + side, side)).resize((1200, 1200), Image.LANCZOS).save(OUT / '封面_AI方版.png', optimize=True)
    print(json.dumps({p.name: Image.open(p).size for p in OUT.glob('封面_*.png')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
