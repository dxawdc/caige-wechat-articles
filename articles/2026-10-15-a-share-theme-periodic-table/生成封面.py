"""封面：AI插画+文字的横版主封面，及矢量绘制的可编辑横版/方版模板（SVG+PNG）。"""
from pathlib import Path
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '配图'
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyhbd.ttc')
plt.rcParams.update({'font.family': 'Microsoft YaHei', 'svg.fonttype': 'none'})
BG, INK, INDIGO, MUTED, GOLD = '#FAFAFE', '#202B54', '#4457C4', '#6B7290', '#E0A43A'
PALETTE = ['#4457C4', '#9471BE', '#2B8DB0', '#C8813B', '#202B54', '#C2649A']
MAIN, SUB, NOTE = '冠军从不连任', '10年A股主题"元素周期表"', '25个主题 · 2017—2026'


def ai_cover():
    """AI原图(1672×941) → 2.35:1 裁切 → 1800×766，左侧留白处叠加标题。"""
    art = Image.open(OUT / '封面_AI原图.png').convert('RGB')
    w = art.width
    h = round(w / 2.35)
    top = 95
    art = art.crop((0, top, w, top + h)).resize((1800, 766), Image.LANCZOS)
    d = ImageDraw.Draw(art)
    d.text((110, 215), MAIN, font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', 122), fill=INK)
    d.text((114, 385), SUB, font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', 60), fill=INDIGO)
    d.text((116, 490), NOTE, font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', 38), fill=MUTED)
    art.save(OUT / '封面_AI.png', optimize=True)


def tiles(ax, x0, y0, cols, rows, size, gap, seed=3):
    """彩色方块周期表：顶格放皇冠，右上一块推上来、一块滑下去。"""
    rng = np.random.default_rng(seed)
    for c in range(cols):
        for r in range(rows):
            if r == 0 and c > 3:
                continue
            ax.add_patch(plt.Rectangle((x0 + c * (size + gap), y0 - r * (size + gap)), size, size,
                                       color=rng.choice(PALETTE), lw=0))
    cx = x0 + 3 * (size + gap) + size / 2
    ax.add_patch(plt.Polygon([(cx - 30, y0 + size + 8), (cx - 34, y0 + size + 46), (cx - 14, y0 + size + 26),
                              (cx, y0 + size + 52), (cx + 14, y0 + size + 26), (cx + 34, y0 + size + 46),
                              (cx + 30, y0 + size + 8)], color=GOLD, lw=0))
    for (dx, dy, ang, col) in [(4.6, .25, -8, '#2B8DB0'), (5.8, -1.9, 18, '#9471BE')]:
        px, py = x0 + dx * (size + gap), y0 + dy * (size + gap)
        rect = plt.Rectangle((px, py), size, size, color=col, lw=0)
        rect.set_transform(matplotlib.transforms.Affine2D().rotate_deg_around(px, py, ang) + ax.transData)
        ax.add_patch(rect)


def template(w, h, name, layout):
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis('off')
    ax.set_facecolor(BG)
    if layout == 'wide':
        tiles(ax, 1000, 560, 6, 7, 62, 12)
        ax.text(110, 430, MAIN, fontsize=88, weight='bold', color=INK, va='baseline')
        ax.text(114, 320, SUB, fontsize=44, weight='bold', color=INDIGO, va='baseline')
        ax.text(116, 250, NOTE, fontsize=28, color=MUTED, va='baseline')
    else:
        tiles(ax, 330, 610, 6, 7, 70, 14)
        ax.text(90, 1010, MAIN, fontsize=100, weight='bold', color=INK, va='baseline')
        ax.text(94, 890, SUB, fontsize=50, weight='bold', color=INDIGO, va='baseline')
        ax.text(96, 820, NOTE, fontsize=30, color=MUTED, va='baseline')
    fig.savefig(OUT / f'{name}.svg', facecolor=BG)
    fig.savefig(OUT / f'{name}.png', facecolor=BG)
    plt.close(fig)


def main():
    ai_cover()
    template(1800, 766, '封面_横版模板', 'wide')
    template(1200, 1200, '封面_方版', 'square')
    print(json.dumps({p.name: Image.open(p).size for p in OUT.glob('封面_*.png')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
