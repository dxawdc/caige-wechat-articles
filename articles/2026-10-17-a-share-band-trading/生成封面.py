"""封面：AI插画+文字的横版主封面，矢量绘制的可编辑横版/方版模板，及缩略图与方形裁切预览。"""
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
BG, INK, INDIGO, MUTED, DOWN = '#FAFAFE', '#202B54', '#4457C4', '#6B7290', '#13895E'
PALETTE = ['#4457C4', '#9471BE', '#2B8DB0', '#C8813B', '#202B54']
MAIN, SUB, NOTE = '越是长牛', '做波段越吃亏', '32个指数 · 24条规则 · 10年回测'
CROP_1_1 = (0.025, 0.4506)   # 方形小卡片裁切区域（相对横版宽度），需完整包含左侧标题


def ai_cover():
    """AI原图(1672×941)左侧补同色背景到2.35:1，保留完整画面，再缩放到1800×766并叠加标题。"""
    art = Image.open(OUT / '封面_AI原图.png').convert('RGB')
    w = round(art.height * 2.35)
    canvas = Image.new('RGB', (w, art.height), art.getpixel((20, 20)))
    canvas.paste(art, (w - art.width, 0))
    canvas = canvas.resize((1800, 766), Image.LANCZOS)
    d = ImageDraw.Draw(canvas)
    d.text((80, 165), MAIN, font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', 150), fill=INK)
    d.text((84, 355), SUB, font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc', 112), fill=DOWN)
    d.text((88, 520), NOTE, font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc', 34), fill=MUTED)
    canvas.save(OUT / '封面_AI.png', optimize=True)
    canvas.resize((300, 128), Image.LANCZOS).save(OUT / '封面_预览_横版300.png')
    x1, x2 = (round(v * 1800) for v in CROP_1_1)
    canvas.crop((x1, 0, x2, 766)).resize((100, 100), Image.LANCZOS).save(OUT / '封面_预览_方形100.png')


def scene(ax, x0, y0, width, height):
    """矢量版：右侧稳步升高的方块阶梯 + 前景几层起伏的波浪。"""
    steps = 6
    sw = width * .42 / steps
    for k in range(steps):
        h = height * (.25 + .7 * (k + 1) / steps)
        ax.add_patch(plt.Rectangle((x0 + width * .55 + k * sw, y0), sw * .92, h, color=PALETTE[k % len(PALETTE)], lw=0))
    fx = x0 + width * .55 + (steps - .5) * sw
    ax.plot([fx, fx], [y0 + height * .95, y0 + height * 1.12], color=INK, lw=3)
    ax.add_patch(plt.Polygon([(fx, y0 + height * 1.12), (fx + 60, y0 + height * 1.08), (fx, y0 + height * 1.04)], color='#D63A2F', lw=0))
    xs = np.linspace(x0, x0 + width, 300)
    for i, col in enumerate(['#2B8DB0', '#4457C4', '#9471BE']):
        ys = y0 + height * (.32 - i * .09) + height * .12 * np.sin((xs - x0) / width * 4 * np.pi + i)
        ax.fill_between(xs, y0 - height * .3, ys, color=col, lw=0, alpha=.95)


def template(w, h, name, layout):
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis('off')
    ax.set_facecolor(BG)
    if layout == 'wide':
        scene(ax, 900, 120, 840, 480)
        ax.text(80, 470, MAIN, fontsize=108, weight='bold', color=INK, va='baseline')
        ax.text(84, 330, SUB, fontsize=80, weight='bold', color=DOWN, va='baseline')
        ax.text(88, 250, NOTE, fontsize=25, color=MUTED, va='baseline')
    else:
        scene(ax, 100, 140, 1000, 480)
        ax.text(90, 1020, MAIN, fontsize=112, weight='bold', color=INK, va='baseline')
        ax.text(94, 880, SUB, fontsize=82, weight='bold', color=DOWN, va='baseline')
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
