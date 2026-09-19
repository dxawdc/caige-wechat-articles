# -*- coding: utf-8 -*-
"""
生成文章对比拼图：原图 / 方案一渐变 / 方案二numpy / 方案三blend，2x2 四宫格带标签。
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(BASE), "素材")
FONT = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑


def load(name, size):
    for folder in (BASE, OUT):
        p = os.path.join(folder, name)
        if os.path.exists(p):
            img = Image.open(p).convert("RGB")
            return img.resize((size, size))
    raise FileNotFoundError(name)


def main():
    S = 500          # 每格图片尺寸
    PAD = 16         # 格间距
    LABEL_H = 56     # 标签高
    cols, rows = 2, 2
    W = cols * S + (cols + 1) * PAD
    H = rows * (S + LABEL_H) + (rows + 1) * PAD

    canvas = Image.new("RGB", (W, H), (250, 250, 252))
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(FONT, 26)
    except OSError:
        font = ImageFont.load_default()

    items = [
        ("头像.jpg",          "① 原始头像"),
        ("五星红旗.png",       "② 国旗素材（规范比例绘制）"),
        ("方案一_putalpha渐变.png", "③ 方案一：PIL 渐变覆盖（经典款）"),
        ("方案三_blend半透明.png",  "④ 方案三：整体半透明（可调透明度）"),
    ]

    for idx, (fname, label) in enumerate(items):
        r, c = divmod(idx, 2)
        x = PAD + c * (S + PAD)
        y = PAD + r * (S + LABEL_H + PAD)
        img = load(fname, S)
        canvas.paste(img, (x, y))
        d.rectangle([x, y + S, x + S, y + S + LABEL_H], fill=(255, 255, 255))
        bbox = d.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        d.text((x + (S - tw) // 2, y + S + 12), label, fill=(60, 60, 66), font=font)

    out = os.path.join(OUT, "对比图_方案总览.png")
    canvas.save(out)
    print("已生成:", out, canvas.size)


if __name__ == "__main__":
    main()
