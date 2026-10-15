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
PALETTE = ['#4457C4', '#9471BE', '#2B8DB0', '#C8813B', '#202B54', '#C2649A']
MAIN, SUB, NOTE = '半年翻倍', '3个月几乎清零', '25个A股主题 · 10年"元素周期表"'
DOWN = '#13895E'
# 方形小卡片裁切区域（相对横版宽度的比例），需完整包含左侧标题
CROP_1_1 = (0.025, 0.4506)


def ai_cover():
    """AI原图(1672×941)左侧补同色背景到2.35:1，保留完整画面，再缩放到1800×766并叠加标题。"""
    art = Image.open(OUT / '封面_AI原图.png').convert('RGB')
    w = round(art.height * 2.35)
    canvas = Image.new('RGB', (w, art.height), art.getpixel((20, 20)))
    canvas.paste(art, (w - art.width - 150, 0))  # 右侧留一点边，插画整体左移，与标题更紧凑
    canvas.paste(Image.new('RGB', (150, art.height), art.getpixel((20, 20))), (w - 150, 0))
    canvas = canvas.resize((1800, 766), Image.LANCZOS)
    d = ImageDraw.Draw(canvas)
    d.text((80, 150), MAIN, font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', 150), fill=INK)
    d.text((84, 345), SUB, font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', 104), fill=DOWN)
    d.text((88, 510), NOTE, font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', 34), fill=MUTED)
    canvas.save(OUT / '封面_AI.png', optimize=True)
    # 预览：信息流缩略图（约300px宽）与方形小卡片（约100px）
    canvas.resize((300, 128), Image.LANCZOS).save(OUT / '封面_预览_横版300.png')
    x1, x2 = (round(v * 1800) for v in CROP_1_1)
    canvas.crop((x1, 0, x2, 766)).resize((100, 100), Image.LANCZOS).save(OUT / '封面_预览_方形100.png')
    canvas.crop((x1, 0, x2, 766)).save(OUT / '封面_预览_方形裁切.png')


def wall(ax, x0, y0, cols, rows, size, gap, peak, seed=3):
    """矮方块墙 + 先红后绿的虚线山峰 + 下落的芯片方块（与AI封面同一概念的矢量版）。"""
    rng = np.random.default_rng(seed)
    step = size + gap
    for c in range(cols):
        for r in range(rows):
            ax.add_patch(plt.Rectangle((x0 + c * step, y0 - (r + 1) * step), size, size, color=rng.choice(PALETTE), lw=0))
    width = cols * step - gap
    t = np.linspace(0, 1, 200)
    xs = x0 + t * width
    ys = y0 + 8 + (peak - y0) * np.exp(-((t - .52) / .14) ** 2)
    up = t <= .52
    ax.plot(xs[up], ys[up], color='#D63A2F', lw=5, ls=(0, (4, 3)), solid_capstyle='round')
    ax.plot(xs[~up], ys[~up], color=DOWN, lw=5, ls=(0, (4, 3)), solid_capstyle='round')
    ax.scatter([xs[0], xs[104], xs[-1]], [ys[0], ys[104], ys[-1]], s=90, color=[INDIGO, '#D63A2F', DOWN], zorder=3)
    cx, cy = xs[-25], ys[-25] + 30
    chip = plt.Rectangle((cx, cy), size * 1.1, size * 1.1, color=INDIGO, lw=0)
    chip.set_transform(matplotlib.transforms.Affine2D().rotate_deg_around(cx, cy, 15) + ax.transData)
    ax.add_patch(chip)


def template(w, h, name, layout):
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis('off')
    ax.set_facecolor(BG)
    if layout == 'wide':
        wall(ax, 960, 250, 12, 3, 46, 8, peak=700)
        ax.text(80, 470, MAIN, fontsize=108, weight='bold', color=INK, va='baseline')
        ax.text(84, 330, SUB, fontsize=74, weight='bold', color=DOWN, va='baseline')
        ax.text(88, 250, NOTE, fontsize=25, color=MUTED, va='baseline')
    else:
        wall(ax, 150, 300, 14, 3, 56, 10, peak=740)
        ax.text(90, 1020, MAIN, fontsize=112, weight='bold', color=INK, va='baseline')
        ax.text(94, 880, SUB, fontsize=78, weight='bold', color=DOWN, va='baseline')
        ax.text(96, 800, NOTE, fontsize=30, color=MUTED, va='baseline')
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
