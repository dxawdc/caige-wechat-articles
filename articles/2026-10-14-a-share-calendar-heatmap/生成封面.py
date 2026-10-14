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
BG, INK, INDIGO, MUTED = '#FAFAFE', '#202B54', '#4457C4', '#6B7290'
MAIN, SUB, NOTE = '上证跌8%', '你的账户呢？', 'A股 · 韩国 · 美股｜日历热力图'


def ai_cover():
    """AI原图(1672×941) → 2.35:1 裁切 → 1800×766，左侧留白处叠加标题。"""
    art = Image.open(OUT / '封面_AI原图.png').convert('RGB')
    w = art.width
    h = round(w / 2.35)
    top = 100
    art = art.crop((0, top, w, top + h)).resize((1800, 766), Image.LANCZOS)
    d = ImageDraw.Draw(art)
    bold = ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', 132)
    bold2 = ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', 104)
    reg = ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', 38)
    x = 120
    d.text((x, 196), MAIN, font=bold, fill=INK)
    d.text((x, 370), SUB, font=bold2, fill=INDIGO)
    d.text((x + 4, 540), NOTE, font=reg, fill=MUTED)
    art.save(OUT / '封面_AI.png', optimize=True)
    return art


def grid(ax, x0, y0, cols, rows, size, gap, seed=7):
    """按"上浅下深、越往右下越绿"的规则画日历方格，部分方块松动下落。"""
    rng = np.random.default_rng(seed)
    greens = ['#E3EEE8', '#B9DCC8', '#8FD0B1', '#4FAE82', '#13895E', '#0B6B49']
    for c in range(cols):
        for r in range(rows):
            depth = (r / rows) * .7 + (c / cols) * .5 + rng.normal(0, .12)
            if r == 0 and rng.random() < .55:
                col = rng.choice(['#F6C9C2', '#ECEEF4', '#F1A096'])
            else:
                col = greens[int(np.clip(depth * len(greens), 0, len(greens) - 1))]
            ax.add_patch(plt.Rectangle((x0 + c * (size + gap), y0 - r * (size + gap)), size, size, color=col, lw=0))
    for k in range(6):
        cx = x0 + rng.uniform(.25, .95) * cols * (size + gap)
        cy = y0 - rows * (size + gap) - rng.uniform(.2, 1.4) * (size + gap)
        rect = plt.Rectangle((cx, cy), size * .9, size * .9, color='#13895E', lw=0, alpha=.9)
        rect.set_transform(matplotlib.transforms.Affine2D().rotate_deg_around(cx, cy, rng.uniform(-30, 30)) + ax.transData)
        ax.add_patch(rect)


def template(w, h, name, layout):
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis('off')
    ax.set_facecolor(BG)
    if layout == 'wide':
        grid(ax, 900, 640, 13, 8, 52, 10)
        ax.plot([880, 1100, 1300, 1500, 1720], [690, 560, 470, 330, 210], color=INDIGO, lw=6, solid_capstyle='round')
        ax.text(120, 470, MAIN, fontsize=96, weight='bold', color=INK, va='baseline')
        ax.text(120, 330, SUB, fontsize=76, weight='bold', color=INDIGO, va='baseline')
        ax.text(124, 240, NOTE, fontsize=28, color=MUTED, va='baseline')
    else:
        grid(ax, 420, 650, 11, 6, 62, 10)
        ax.plot([400, 620, 820, 1020, 1180], [710, 600, 520, 400, 260], color=INDIGO, lw=6, solid_capstyle='round')
        ax.text(90, 1010, MAIN, fontsize=110, weight='bold', color=INK, va='baseline')
        ax.text(90, 850, SUB, fontsize=86, weight='bold', color=INDIGO, va='baseline')
        ax.text(94, 770, NOTE, fontsize=30, color=MUTED, va='baseline')
    fig.savefig(OUT / f'{name}.svg', facecolor=BG)
    fig.savefig(OUT / f'{name}.png', facecolor=BG)
    plt.close(fig)


def main():
    ai_cover()
    template(1800, 766, '封面_横版模板', 'wide')
    template(1200, 1200, '封面_方版', 'square')
    sizes = {p.name: Image.open(p).size for p in OUT.glob('封面_*.png')}
    print(json.dumps(sizes, ensure_ascii=False))


if __name__ == '__main__':
    main()
