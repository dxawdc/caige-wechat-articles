"""用同一组绘图指令生成 PNG 和可编辑 SVG：3 张正文示意图 + 横版/方版封面模板。依赖 Pillow。"""
from pathlib import Path
import argparse, html, json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG, INK, MUTED = '#FAFAFE', '#202B54', '#5D6485'
INDIGO, CORAL, VIOLET, GRID = '#4457C4', '#DB655A', '#9471BE', '#E4E6F1'
SOFT_I, SOFT_C = '#EEF0FB', '#FBEDEB'
FONT = None


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new('RGB', (w, h), BG)
        self.d = ImageDraw.Draw(self.im)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="{BG}"/>']

    def rect(self, x, y, w, h, fill, r=0, stroke=None):
        self.d.rounded_rectangle((x, y, x + w, y + h), radius=r, fill=fill, outline=stroke, width=2)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="2"' if stroke else '') + '/>')

    def circle(self, cx, cy, r, fill):
        self.d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)
        self.svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>')

    def line(self, x1, y1, x2, y2, fill=INDIGO, width=3):
        self.d.line((x1, y1, x2, y2), fill=fill, width=width)
        self.svg.append(f'<path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="{fill}" stroke-width="{width}"/>')

    def text(self, x, y, s, size=40, color=INK, bold=False, limit=None):
        font = ImageFont.truetype(FONT, size)
        box = self.d.textbbox((x, y), s, font=font, anchor='lt')
        assert box[2] <= (limit or self.w - 30), (s, box, self.w)
        self.d.text((x, y), s, font=font, fill=color, anchor='lt', stroke_width=1 if bold else 0, stroke_fill=color)
        self.svg.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(s)}</text>')
        return box[2]

    def header(self, n, title, sub):
        self.rect(64, 56, 96, 10, CORAL, 5)
        self.text(64, 92, title, 58, bold=True)
        self.text(66, 176, sub, 30, color=MUTED)

    def footer(self):
        self.line(64, self.h - 92, self.w - 64, self.h - 92, GRID, 2)
        self.text(64, self.h - 64, 'WorkBuddy 好用的 11 个技能 · 示意图', 26, color=MUTED)
        self.text(self.w - 240, self.h - 64, '可以叫我才哥', 27, color=INDIGO)

    def save(self, name):
        out = ROOT / '配图'; out.mkdir(exist_ok=True)
        self.im.save(out / (name + '.png'), optimize=True)
        (out / (name + '.svg')).write_text('\n'.join(self.svg + ['</svg>']), encoding='utf-8')


def fig1(lib):
    c = Canvas(1200, 1500)
    c.header(1, '11 个技能，分成两组', '先装 3 个管家，再按任务装流水线上的 8 个')
    sk = lib['skills']
    c.rect(64, 250, 1072, 330, SOFT_C, 22)
    c.text(96, 276, '管家 · 先装这 3 个', 32, color=CORAL, bold=True)
    for i, s in enumerate(sk[:3]):
        x = 96 + i * 344
        c.rect(x, 336, 320, 214, '#FFFFFF', 18, stroke=GRID)
        c.text(x + 22, 356, f"{s['id']:02d}", 26, color=CORAL, bold=True)
        c.text(x + 22, 396, s['name'], 32 if len(s['name']) < 14 else 27, bold=True, limit=x + 310)
        c.text(x + 22, 452, ['帮你找', '帮你查', '帮你记'][i], 28, color=MUTED)
        c.text(x + 22, 498, s['install'], 22, color=INDIGO, limit=x + 310)
    c.rect(64, 612, 1072, 760, SOFT_I, 22)
    c.text(96, 638, '流水线 · 按任务装这 8 个', 32, color=INDIGO, bold=True)
    for i, s in enumerate(sk[3:]):
        col, row = i % 2, i // 2
        x, y = 96 + col * 524, 698 + row * 166
        c.rect(x, y, 500, 146, '#FFFFFF', 18, stroke=GRID)
        c.text(x + 22, y + 20, f"第 {i+1} 步 · {s['step']}", 24, color=INDIGO, bold=True)
        c.text(x + 22, y + 58, s['name'], 32, bold=True, limit=x + 490)
        c.text(x + 22, y + 104, s['source'] + ' · ' + s['install'], 21, color=MUTED, limit=x + 490)
    c.footer(); c.save('图1_技能总览')


def fig2():
    c = Canvas(1200, 1220)
    c.header(2, '找、查、装、记', '装任何技能，都可以按这个顺序')
    steps = [('找', 'Find Skills', '说出要做的事，让它列候选、讲区别', INDIGO),
             ('查', 'Skill Scanner', '看它读写哪些目录、会不会联网、依赖什么', VIOLET),
             ('装', '自己确认后再安装', '装好先做一件小事，打开结果看看', CORAL),
             ('记', 'self-improvement', '纠正过的偏好记下来，下次少说一遍', INK)]
    for i, (k, name, ex, col) in enumerate(steps):
        y = 250 + i * 206
        c.rect(64, y, 1072, 180, '#FFFFFF', 20, stroke=GRID)
        c.rect(92, y + 40, 100, 100, col, 22)
        c.text(118, y + 58, k, 56, color='#FFFFFF', bold=True)
        c.text(226, y + 36, name, 40, bold=True)
        c.text(226, y + 104, ex, 29, color=MUTED)
        if i < 3:
            c.line(142, y + 180, 142, y + 206, GRID, 4)
    c.footer(); c.save('图2_安装顺序')


def fig3(lib):
    c = Canvas(1200, 1720)
    c.header(3, '一节视频课，到一篇笔记', '8 个技能各管一步，缺哪步装哪个')
    outs = ['字幕和音频', '转写稿', '最新资料和链接', '展开后的内容和截图', '一篇 Obsidian 笔记', '我的 Writing-DNA.md', '去掉模板腔的初稿', '可以分享的网页']
    for i, s in enumerate(lib['skills'][3:]):
        y = 250 + i * 160
        col = CORAL if s['source'] == 'GitHub' else INDIGO
        c.rect(64, y, 1072, 138, '#FFFFFF', 18, stroke=GRID)
        c.circle(122, y + 69, 32, col)
        c.text(111, y + 48, str(i + 1), 36, color='#FFFFFF', bold=True)
        c.text(182, y + 22, s['step'], 34, bold=True)
        c.text(182, y + 80, s['name'], 27, color=col)
        c.text(640, y + 22, '得到', 24, color=MUTED)
        c.text(640, y + 62, outs[i], 30, bold=True, limit=1120)
    c.text(64, 1546, '珊瑚色的两步是 GitHub 上的社区技能，其余来自 SkillHub', 24, color=MUTED)
    c.footer(); c.save('图3_内容流水线')


def covers():
    for square in (False, True):
        w, h = (1200, 1200) if square else (1800, 766)
        c = Canvas(w, h)
        c.rect(84, 80, 110, 12, CORAL, 6)
        c.text(84, 124, 'WorkBuddy', 50, color=INDIGO, bold=True)
        c.text(84, 214, '好用的 11 个技能', 92 if square else 104, bold=True)
        c.text(84, 352, '先装这 3 个', 84 if square else 88, color=CORAL, bold=True)
        bx, by = (120, 600) if square else (1120, 160)
        for i in range(3):
            c.rect(bx + i * 180, by, 150, 150, [CORAL, INDIGO, VIOLET][i], 26)
        for i in range(8):
            c.rect(bx + (i % 4) * 135, by + 200 + (i // 4) * 120, 110, 90, '#FFFFFF', 18, stroke=GRID)
        c.save('封面_方版模板' if square else '封面_横版模板')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--font', default='C:/Windows/Fonts/msyh.ttc')
    FONT = ap.parse_args().font
    if not Path(FONT).exists():
        raise SystemExit('请通过 --font 指定本机中文字体文件')
    lib = json.loads((ROOT / '技能清单.json').read_text(encoding='utf-8'))
    fig1(lib); fig2(); fig3(lib); covers()
    print('done')
