"""用同一组绘图指令生成 PNG 和可编辑 SVG：4 张正文示意图 + 横版/方版封面模板。依赖 Pillow。"""
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
        self.text(64, self.h - 64, 'WorkBuddy 提示词 100 例 · 示意图', 26, color=MUTED)
        self.text(self.w - 240, self.h - 64, '可以叫我才哥', 27, color=INDIGO)

    def save(self, name):
        out = ROOT / '配图'; out.mkdir(exist_ok=True)
        self.im.save(out / (name + '.png'), optimize=True)
        (out / (name + '.svg')).write_text('\n'.join(self.svg + ['</svg>']), encoding='utf-8')


def fig1(lib):
    c = Canvas(1200, 1430)
    c.header(1, '100 个提示词，分成 10 类', '找到自己最常做的那一类，先挑两三条试试')
    examples = {
        1: '周报 · 邮件 · 会议纪要', 2: '按模板排版 · 做 PPT · 读合同',
        3: '数据体检 · 合并表格 · 看板', 4: '整理下载 · 发票 · 找重复',
        5: '行业简报 · 竞品对比 · 核查', 6: '学习计划 · 资料库问答',
        7: '选题 · 封面 · 小红书图文', 8: '早报 · 周报 · 收盘速览',
        9: '旅行 · 账单 · 体检报告', 10: '先出计划 · 自查 · 存成技能',
    }
    for i, cat in enumerate(lib['categories']):
        col, row = i % 2, i // 2
        x, y = 64 + col * 546, 250 + row * 214
        accent = CORAL if cat['id'] in (8, 10) else INDIGO
        c.rect(x, y, 526, 190, '#FFFFFF', 20, stroke=GRID)
        first, last = cat['prompts'][0]['id'], cat['prompts'][-1]['id']
        c.text(x + 26, y + 24, f'{first:02d}—{last:02d}', 28, color=accent, bold=True)
        c.text(x + 26, y + 68, cat['name'], 40, bold=True, limit=x + 510)
        c.text(x + 26, y + 130, examples[cat['id']], 26, color=MUTED, limit=x + 510)
    c.footer(); c.save('图1_分类导航')


def fig2():
    c = Canvas(1200, 1330)
    c.header(2, '同一件事，两种说法', '写清四样东西，它就不用再猜')
    c.rect(64, 250, 1072, 190, SOFT_C, 20)
    c.text(96, 278, '只说了目标', 30, color=CORAL, bold=True)
    c.text(96, 336, '“帮我整理一下这个表格。”', 40)
    c.text(96, 394, '整理成什么样？给谁看？哪些不能动？都得它自己猜', 26, color=MUTED)
    c.text(64, 482, '四样都写清楚', 30, color=INDIGO, bold=True)
    items = [
        ('目标', '要做什么', '把销售表按月份汇总', INDIGO),
        ('输入', '材料在哪', '附件这份销售表', VIOLET),
        ('输出', '最后要什么', '做成 Excel，保留公式', CORAL),
        ('约束', '有什么要求', '日期统一成年月日格式', INK),
    ]
    for i, (k, q, ex, col) in enumerate(items):
        y = 540 + i * 168
        c.rect(64, y, 1072, 148, '#FFFFFF', 20, stroke=GRID)
        c.rect(92, y + 32, 130, 84, col, 18)
        c.text(118, y + 50, k, 40, color='#FFFFFF', bold=True)
        c.text(256, y + 30, q, 30, color=MUTED)
        c.text(256, y + 78, ex, 38, bold=True)
    c.footer(); c.save('图2_四要素')


def fig3():
    c = Canvas(1200, 1300)
    c.header(3, '定时任务的提示词要写全', '它运行时看不到你当前的对话')
    items = [
        ('去哪里找', '联网搜索、某个网址，或工作空间里的文件', INDIGO),
        ('找什么范围', '过去 24 小时、本周修改过的、前 10 个', VIOLET),
        ('输出成什么样', '几条、什么字段、存成什么文件', CORAL),
        ('特殊情况怎么办', '没有变化写“无变化”，不删除任何文件', INK),
    ]
    for i, (k, ex, col) in enumerate(items):
        y = 250 + i * 190
        c.rect(64, y, 1072, 166, '#FFFFFF', 20, stroke=GRID)
        c.circle(124, y + 83, 34, col)
        c.text(112, y + 61, str(i + 1), 40, color='#FFFFFF', bold=True)
        c.text(190, y + 32, k, 40, bold=True)
        c.text(190, y + 98, ex, 29, color=MUTED)
    c.rect(64, 1040, 1072, 130, SOFT_I, 20)
    c.text(96, 1066, '执行时间填在定时规则里，不用写进提示词', 30, color=INDIGO, bold=True)
    c.text(96, 1116, '电脑上的 WorkBuddy 客户端保持运行，任务才会按时触发', 26, color=MUTED)
    c.footer(); c.save('图3_定时任务')


def fig4():
    c = Canvas(1200, 1220)
    c.header(4, '从一条提示词，到自己的技能', '同一句话用到第三次，就值得存下来')
    steps = [
        ('复制一条', '从 10 类里找到最接近的那条'),
        ('换掉【】', '填上自己的文件、读者和要求'),
        ('先看计划', '复杂任务先用第 91 条，确认后再做'),
        ('检查结果', '用第 95 条让它自查，再自己打开看'),
        ('存成技能', '用第 94 条整理成技能，下次一句话调用'),
    ]
    for i, (k, ex) in enumerate(steps):
        y = 250 + i * 172
        col = CORAL if i == 4 else INDIGO
        c.rect(64, y, 1072, 148, '#FFFFFF', 20, stroke=GRID)
        c.rect(92, y + 34, 80, 80, col, 18)
        c.text(118, y + 50, str(i + 1), 40, color='#FFFFFF', bold=True)
        c.text(204, y + 26, k, 40, bold=True)
        c.text(204, y + 88, ex, 29, color=MUTED)
        if i < 4:
            c.line(132, y + 148, 132, y + 172, GRID, 4)
    c.footer(); c.save('图4_使用路径')


def covers():
    for square in (False, True):
        w, h = (1200, 1200) if square else (1800, 766)
        c = Canvas(w, h)
        c.rect(84, 80, 110, 12, CORAL, 6)
        c.text(84, 124, 'WorkBuddy', 50, color=INDIGO, bold=True)
        c.text(84, 214, '100 个提示词', 104 if square else 112, bold=True)
        c.text(84, 364, '复制就能用', 88 if square else 92, color=CORAL, bold=True)
        # 右侧（方版为下方）：一叠提示词卡片，【】用珊瑚色块表示
        bx, by = (150, 620) if square else (1080, 170)
        for i in range(3):
            x, y = bx + i * 46, by + i * 46
            c.rect(x, y, 520, 330 if square else 360, '#FFFFFF', 26, stroke=GRID)
        x, y = bx + 92, by + 92
        c.rect(x + 40, y + 46, 150, 18, INDIGO, 9)
        for j, (wd, mark) in enumerate([(380, 120), (420, 0), (300, 150), (360, 0)]):
            yy = y + 104 + j * 50
            c.rect(x + 40, yy, wd, 14, GRID, 7)
            if mark:
                c.rect(x + 40 + wd - mark, yy - 6, mark, 26, CORAL, 8)
        c.save('封面_方版模板' if square else '封面_横版模板')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--font', default='C:/Windows/Fonts/msyh.ttc')
    FONT = ap.parse_args().font
    if not Path(FONT).exists():
        raise SystemExit('请通过 --font 指定本机中文字体文件')
    lib = json.loads((ROOT / '提示词库.json').read_text(encoding='utf-8'))
    fig1(lib); fig2(); fig3(); fig4(); covers()
    print('已生成 4 张示意图、2 份封面模板；每份均含 PNG 与可编辑 SVG。')
