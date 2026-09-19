# -*- coding: utf-8 -*-
"""生成公众号封面（2.35:1，1200x510），金银主题。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "配图" / "封面_v1.0.0.png"
W, H = 1200, 510
BG = "#14100A"
GOLD = "#C8961E"
GOLD_LIGHT = "#F2D9A0"
SILVER = "#AEB9C6"
INK_LIGHT = "#F5EFE4"
GREY = "#8A8579"

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT = r"C:\Windows\Fonts\msyh.ttc"


def f(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # 右侧装饰：金银双线走势
    import math
    gold_points = []
    silver_points = []
    for i in range(28):
        x = 700 + i * 18
        t = i / 27
        gold_y = 360 - (t ** 2.1) * 260 - math.sin(i * 0.9) * 9
        silver_y = 400 - (t ** 2.5) * 250 - math.sin(i * 1.1 + 1) * 13
        gold_points.append((x, gold_y))
        silver_points.append((x, silver_y))
    d.line(silver_points, fill=SILVER, width=4)
    d.line(gold_points, fill=GOLD, width=5)
    for px, py in (gold_points[-1], silver_points[-1]):
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=INK_LIGHT)

    # 左侧文案
    d.text((84, 92), "黄金白银这10年", font=f(FONT_BOLD, 92), fill=INK_LIGHT)
    d.text((88, 216), "从上金所到周大福柜台", font=f(FONT_BOLD, 46), fill=GOLD_LIGHT)
    d.rectangle([90, 292, 306, 298], fill=GOLD)
    d.text((88, 322), "公开数据实测 · 6 家金店近两年挂牌价 · 9 张图",
           font=f(FONT, 28), fill=GREY)

    d.text((W - 302, H - 76), "可以叫我才哥", font=f(FONT_BOLD, 34), fill=GREY)

    im.save(OUT, "PNG")
    print(OUT, im.size)


if __name__ == "__main__":
    main()
