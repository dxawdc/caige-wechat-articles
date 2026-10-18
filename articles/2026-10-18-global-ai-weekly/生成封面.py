"""全球AI周报封面：AI底图+文字的横版/方版主封面，矢量可编辑模板，及缩略图预览。

周报系列固定版式：左上「全球AI周报 + 日期」标签，主标题两行（第一行带关键数字），底部三条主线小字。
每周只需改 COPY 中的文字与底图文件，其余版式保持一致，便于读者识别。
"""
from pathlib import Path
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, Rectangle
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '配图'
BOLD, REG = r'C:\Windows\Fonts\msyhbd.ttc', r'C:\Windows\Fonts\msyh.ttc'
font_manager.fontManager.addfont(REG)
font_manager.fontManager.addfont(BOLD)
plt.rcParams.update({'font.family': 'Microsoft YaHei', 'svg.fonttype': 'none'})

INK, INDIGO, CORAL, VIOLET, DOWN, MUTED = '#202B54', '#4457C4', '#DB655A', '#9471BE', '#13895E', '#6B7290'
THEME = {  # 浅色底图 / 深色底图 两套文字配色
    'light': dict(bg='#F4F5FB', ink=INK, l2=CORAL, num=DOWN, muted=MUTED, tag=INDIGO, tagtext='#FFFFFF'),
    'dark': dict(bg='#1B2350', ink='#FFFFFF', l2='#FF8A7E', num='#3FD08F', muted='#B9C0E6', tag='#FFFFFF', tagtext='#1B2350'),
}
# 本期文案：第一行 (前缀, 数字)，第二行，日期，底部主线
COPY = dict(series='全球AI周报', date='10.18', l1=('芯片股一周跌', '24%'), l2='美欧出手管AI', foot='模型 · 监管 · 资本')


def font(path, size):
    return ImageFont.truetype(path, size)


def draw_copy(img, x, y, scale, t):
    """在 PIL 图上按系列版式写字；返回文字块右边界，便于检查是否压到主体。"""
    d = ImageDraw.Draw(img)
    # 标签：实心「全球AI周报」+ 描边日期
    f_tag = font(BOLD, int(38 * scale))
    tw = d.textlength(COPY['series'], font=f_tag)
    pad, th = int(18 * scale), int(62 * scale)
    d.rounded_rectangle((x, y, x + tw + pad * 2, y + th), radius=th // 2, fill=t['tag'])
    d.text((x + pad, y + th / 2), COPY['series'], font=f_tag, fill=t['tagtext'], anchor='lm')
    dx = x + tw + pad * 2 + int(14 * scale)
    dw = d.textlength(COPY['date'], font=f_tag)
    d.rounded_rectangle((dx, y, dx + dw + pad * 2, y + th), radius=th // 2, outline=t['tag'], width=max(2, int(3 * scale)))
    d.text((dx + pad, y + th / 2), COPY['date'], font=f_tag, fill=t['tag'], anchor='lm')
    # 主标题两行
    f_main = font(BOLD, int(104 * scale))
    y1 = y + th + int(48 * scale)
    pre, num = COPY['l1']
    d.text((x, y1), pre, font=f_main, fill=t['ink'], anchor='lt')
    pw = d.textlength(pre, font=f_main)
    d.text((x + pw, y1), num, font=f_main, fill=t['num'], anchor='lt')
    y2 = y1 + int(138 * scale)
    d.text((x, y2), COPY['l2'], font=f_main, fill=t['l2'], anchor='lt')
    # 底部主线
    y3 = y2 + int(168 * scale)
    d.text((x + 4, y3), COPY['foot'], font=font(REG, int(36 * scale)), fill=t['muted'], anchor='lt')
    return max(x + pw + d.textlength(num, font=f_main), x + d.textlength(COPY['l2'], font=f_main))


def ai_cover(art_file, theme, name):
    """AI原图(16:9)右对齐放入 2.35:1 画布，左侧补底色；方版改为上文下图重新排布。"""
    t = THEME[theme]
    art = Image.open(OUT / art_file).convert('RGB')
    # 横版 1800×766
    h = 766
    a = art.resize((round(art.width * h / art.height), h), Image.LANCZOS)
    wide = Image.new('RGB', (1800, h), a.getpixel((8, h // 2)))
    wide.paste(a, (1800 - a.width, 0))
    right = draw_copy(wide, 96, 120, 1.0, t)
    wide.save(OUT / f'{name}_横版.png', optimize=True)
    # 方版 1200×1200：上半文字，下半取底图右侧主体
    sq = Image.new('RGB', (1200, 1200), art.getpixel((8, art.height // 2)))
    crop = art.crop((int(art.width * .42), 0, art.width, art.height))
    crop = crop.resize((round(crop.width * 760 / crop.height), 760), Image.LANCZOS)
    # 主体左缘做渐隐，和纯色底自然衔接
    import numpy as np
    xs = np.clip(np.arange(crop.width) / 160, 0, 1)
    ys = np.clip(np.arange(crop.height) / 160, 0, 1)
    mask = Image.fromarray((np.minimum.outer(ys, xs) * 255).astype('uint8'), 'L')
    sq.paste(crop, (1200 - crop.width, 1200 - crop.height), mask)
    draw_copy(sq, 84, 70, 0.98, t)
    sq.save(OUT / f'{name}_方版.png', optimize=True)
    # 缩略图验收：横版300px宽，方版100px
    wide.resize((300, 128), Image.LANCZOS).save(OUT / f'{name}_预览300.png')
    sq.resize((100, 100), Image.LANCZOS).save(OUT / f'{name}_预览100.png')
    return right


def vector_art(ax, cx, cy, s):
    """矢量主体：芯片 + 下滑绿色折线 + 两只放大镜（美、欧监管）。"""
    ax.add_patch(FancyBboxPatch((cx - 150 * s, cy - 150 * s), 300 * s, 300 * s, boxstyle=f'round,pad=0,rounding_size={24 * s}',
                                fc=INDIGO, ec='none'))
    ax.add_patch(FancyBboxPatch((cx - 90 * s, cy - 90 * s), 180 * s, 180 * s, boxstyle=f'round,pad=0,rounding_size={12 * s}',
                                fc='#6F80E0', ec='none'))
    for k in range(-2, 3):
        for side in (-1, 1):
            ax.add_patch(Rectangle((cx + k * 50 * s - 8 * s, cy + side * 150 * s + (0 if side > 0 else -40 * s)), 16 * s, 40 * s, fc=INDIGO, ec='none'))
            ax.add_patch(Rectangle((cx + side * 150 * s + (0 if side > 0 else -40 * s), cy + k * 50 * s - 8 * s), 40 * s, 16 * s, fc=INDIGO, ec='none'))
    xs = [cx - 260 * s, cx - 140 * s, cx - 60 * s, cx + 60 * s, cx + 180 * s, cx + 250 * s]
    ys = [cy + 300 * s, cy + 330 * s, cy + 250 * s, cy + 270 * s, cy + 150 * s, cy + 60 * s]
    ax.plot(xs, ys, color=DOWN, lw=12 * s, solid_capstyle='round', solid_joinstyle='round')
    ax.add_patch(Polygon([(cx + 250 * s, cy + 10 * s), (cx + 210 * s, cy + 90 * s), (cx + 290 * s, cy + 90 * s)], fc=DOWN, ec='none'))
    for (mx, my, c, dirx) in [(cx - 260 * s, cy - 120 * s, CORAL, 1), (cx + 300 * s, cy - 210 * s, VIOLET, -1)]:
        ax.add_patch(Circle((mx, my), 78 * s, fc='white', ec=c, lw=14 * s, alpha=.95))
        ax.plot([mx - dirx * 55 * s, mx - dirx * 140 * s], [my - 55 * s, my - 140 * s], color=c, lw=22 * s, solid_capstyle='round')


def template(w, h, name):
    """可编辑模板：文字为 SVG 文本，主体为矢量形状。"""
    t = THEME['light']
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100, facecolor=t['bg'])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis('off')
    pt = 72 / 100  # 像素 → 磅
    if w > h:
        x, top, s = 96, h - 120, 1.0
        vector_art(ax, 1360, 360, 0.95)
    else:
        x, top, s = 84, h - 70, 0.98
        vector_art(ax, 640, 360, 0.82)
    tag_h = 62 * s
    ax.add_patch(FancyBboxPatch((x, top - tag_h), 236 * s, tag_h, boxstyle=f'round,pad=0,rounding_size={tag_h / 2}', fc=INDIGO, ec='none'))
    ax.text(x + 18 * s, top - tag_h / 2, COPY['series'], fontsize=38 * s * pt, weight='bold', color='white', va='center')
    ax.add_patch(FancyBboxPatch((x + 250 * s, top - tag_h), 150 * s, tag_h, boxstyle=f'round,pad=0,rounding_size={tag_h / 2}',
                                fc='none', ec=INDIGO, lw=2))
    ax.text(x + 268 * s, top - tag_h / 2, COPY['date'], fontsize=38 * s * pt, weight='bold', color=INDIGO, va='center')
    y1 = top - tag_h - 48 * s
    pre, num = COPY['l1']
    t1 = ax.text(x, y1, pre, fontsize=104 * s * pt, weight='bold', color=INK, va='top')
    fig.canvas.draw()
    bb = t1.get_window_extent()
    ax.text(x + bb.width, y1, num, fontsize=104 * s * pt, weight='bold', color=DOWN, va='top')
    ax.text(x, y1 - 138 * s, COPY['l2'], fontsize=104 * s * pt, weight='bold', color=CORAL, va='top')
    ax.text(x + 4, y1 - 306 * s, COPY['foot'], fontsize=36 * s * pt, color=MUTED, va='top')
    fig.savefig(OUT / f'{name}.svg', facecolor=t['bg'])
    fig.savefig(OUT / f'{name}.png', facecolor=t['bg'])
    plt.close(fig)


def main():
    res = {}
    # 默认生成定稿：浅色方案（本期用户选定方案A）；也可传 底图:主题:名称 试制新方案
    for arg in sys.argv[1:] or ['封面底图.png:light:封面']:
        f, theme, name = arg.split(':')
        res[name] = ai_cover(f, theme, name)
    template(1800, 766, '封面_横版模板')
    template(1200, 1200, '封面_方版模板')
    print(json.dumps({'文字块右边界': res, **{p.name: Image.open(p).size for p in OUT.glob('封面*.png')}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
