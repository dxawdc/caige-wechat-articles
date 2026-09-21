# -*- coding: utf-8 -*-
"""生成公众号封面（2.35:1，1200x510），A股资金流向主题，红涨绿跌配色。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "配图" / "封面_v1.0.0.png"
W, H = 1200, 510
BG = "#141821"
RED = "#E5484D"        # A股涨 = 红
GREEN = "#1DB978"      # A股跌 = 绿
INK_LIGHT = "#F3F6F8"
GREY = "#8B93A1"
GOLD = "#F0B429"

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT = r"C:\Windows\Fonts\msyh.ttc"


def f(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # 右侧装饰：资金流分时曲线（红区在上、绿区在下，中间一条累计线）
    import math
    # 累计净额曲线（N 字形：早盘冲高、午后回吐、尾盘抢回）
    pts = []
    for i in range(60):
        x = 560 + i * 10
        t = i / 59
        # N 形：0->高 ->低 ->中
        if t < 0.25:
            y = 300 - t / 0.25 * 120
        elif t < 0.55:
            y = 180 + (t - 0.25) / 0.30 * 150
        elif t < 0.85:
            y = 330 - (t - 0.55) / 0.30 * 60
        else:
            y = 270 - (t - 0.85) / 0.15 * 50
        pts.append((x, y))
    # 红绿双带：曲线上下各一条方向色带
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        # 上带（红，净流入区）
        d.line([(x0, y0 - 26), (x1, y1 - 26)], fill=RED, width=16)
        # 下带（绿，净流出区）
        d.line([(x0, y0 + 26), (x1, y1 + 26)], fill=GREEN, width=16)
    # 中间累计线
    d.line(pts, fill=INK_LIGHT, width=4)
    # 末端亮点
    ex, ey = pts[-1]
    d.ellipse([ex - 8, ey - 8, ex + 8, ey + 8], fill=GOLD)
    # 图例
    d.ellipse([560, 396, 574, 410], fill=RED)
    d.text((582, 390), "主力净流入", font=f(FONT, 24), fill=GREY)
    d.ellipse([700, 396, 714, 410], fill=GREEN)
    d.text((722, 390), "主力净流出", font=f(FONT, 24), fill=GREY)

    # 左侧文案
    d.text((84, 84), "我把A股一天的资金流向", font=f(FONT_BOLD, 72), fill=INK_LIGHT)
    d.text((88, 190), "做成了一组图", font=f(FONT_BOLD, 72), fill=INK_LIGHT)
    d.rectangle([90, 292, 430, 298], fill=RED)
    d.text((88, 322), "5195 只票 · 四档资金 · 10 张图",
           font=f(FONT, 30), fill=GREY)

    d.text((W - 312, H - 76), "可以叫我才哥", font=f(FONT_BOLD, 34), fill=GREY)

    im.save(OUT, "PNG")
    print("saved", OUT, im.size)


if __name__ == "__main__":
    main()
