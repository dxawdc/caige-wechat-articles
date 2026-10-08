"""根据 数据/ 下的整理表绘制公众号配图，输出到 配图/。只分析指南正文内容。"""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib import font_manager as fm

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '数据'
IMG = ROOT / '配图'
IMG.mkdir(exist_ok=True)
FONTS = Path(r'C:\Windows\Fonts')
SANS = fm.FontProperties(fname=str(FONTS / 'msyh.ttc'))
SANS_B = fm.FontProperties(fname=str(FONTS / 'msyhbd.ttc'))
TITLE = fm.FontProperties(fname=str(FONTS / 'Noto Sans SC Bold (TrueType).otf'))
fm.fontManager.addfont(str(FONTS / 'msyh.ttc'))
plt.rcParams.update({'font.family': SANS.get_name(), 'axes.unicode_minus': False, 'savefig.dpi': 180})

BG, CARD, INK, MUTED, LINE = '#F6F2EA', '#FFFDF8', '#1F2A2E', '#7B8186', '#E3DCCF'
LENS = {'换寿命': '#C2553F', '换钱': '#C9962F', '换时间精力': '#3B8A7A', '换人身自由': '#3A5878'}
LENS_ORDER = ['换寿命', '换钱', '换时间精力', '换人身自由']
GRADE = {'A': '#24414F', 'B': '#7C9EAE', 'C': '#CCD8DD'}
TIER = {'极高': 1.0, '高': .55, '一般': .2}
FOOT = '数据：github.com/eternity4719/HowToLiveBetter（CC BY 4.0）｜正文快照 2026-10-08'

df = pd.read_csv(DATA / '条目.csv', dtype={'钱': str})
sec = pd.read_csv(DATA / '章节统计.csv')


def frame(title, sub, size=(10, 7)):
    fig = plt.figure(figsize=size, facecolor=BG)
    h = size[1]
    fig.add_artist(Rectangle((.06, 1 - .42 / h), .05, .07 / h, transform=fig.transFigure, color=LENS['换寿命'], lw=0))
    fig.text(.06, 1 - .55 / h, title, fontproperties=TITLE, fontsize=25, color=INK, va='top')
    fig.text(.06, 1 - 1.18 / h, sub, fontsize=12.5, color=MUTED, va='top')
    fig.text(.06, .32 / h, FOOT, fontsize=9.5, color=MUTED)
    fig.text(.94, .32 / h, '可以叫我才哥', fontproperties=SANS_B, fontsize=10.5, color=LENS['换人身自由'], ha='right')
    return fig


def clean(ax):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, colors=MUTED)
    ax.set_facecolor(BG)


def card(f, x, y, w, h, accent=None, top=False):
    f.add_artist(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=.012', transform=f.transFigure, fc=CARD, ec=LINE, lw=1))
    if accent and top:
        f.add_artist(Rectangle((x, y + h - .007), w, .007, transform=f.transFigure, color=accent, lw=0))
    elif accent:
        f.add_artist(Rectangle((x, y), .006, h, transform=f.transFigure, color=accent, lw=0))


def save(fig, name):
    fig.savefig(IMG / name, facecolor=fig.get_facecolor())
    plt.close(fig)
    print('saved', name)


def overview():
    n = len(df)
    a = (df.证据 == 'A').sum()
    top = (df.性价比 == '极高').sum()
    f = frame('一本 672 条的人生账本', '《高性价比人生指南》正文概况｜每条写明成本、收益、证据等级和原始出处', size=(10, 6.2))
    cards = [(f'{n}', '条建议', f'分在 {df.节.nunique()} 节里', LENS['换寿命']),
             (f'{a}', '条 A 级证据', f'占 {a / n:.0%}，有确切数字可查', LENS['换人身自由']),
             (f'{top}', '条性价比极高', '不花钱、不占时间、不用毅力', LENS['换钱']),
             (f'{int(df.链接数.sum()):,}', '条原始出处链接', '期刊论文与官方文件', LENS['换时间精力'])]
    for i, (num, label, note, c) in enumerate(cards):
        x = .06 + (i % 2) * .45
        y = .49 - (i // 2) * .29
        card(f, x, y, .41, .24, c)
        f.text(x + .035, y + .15, num, fontproperties=TITLE, fontsize=38, color=c, va='center')
        f.text(x + .035, y + .055, label, fontproperties=SANS_B, fontsize=14.5, color=INK, va='center')
        f.text(x + .385, y + .055, note, fontsize=10.8, color=MUTED, va='center', ha='right')
    save(f, '02_总览.png')


def anatomy():
    f = frame('一条建议长什么样', '每条都要回答：花掉什么、换回什么、证据多硬、出处在哪', size=(10, 8.4))
    rows = [
        ('标题', '9. 把家里的食盐换成低钠盐（钾盐）', '动词开头，直接写做什么', INK),
        ('成本', '一袋比普通盐贵几元，\n买的时候顺手换，口味几乎不变', '钱 / 时间 / 毅力 三项成本', LENS['换钱']),
        ('说人话', '得过中风或 60 岁以上有高血压的人，\n五年内死亡的概率低约 12%', '只看这一行就够拿主意', LENS['换寿命']),
        ('收益', '随机分组试验，20995 人，\n跟踪 4.74 年：RR 0.88', '原样保留研究数字，可自行核对', LENS['换寿命']),
        ('证据等级', 'A', 'A 有确切数字 / B 有研究无确数 / C 经验', GRADE['A']),
        ('来源', 'Neal B 等 (2021). NEJM.\ndoi.org/10.1056/NEJMoa2105675', '只引期刊论文与官方文件', LENS['换时间精力']),
        ('备注', '争议：试验对象是高危老人；\n肾功能不全、吃保钾药先问医生', '适用人群与反方证据写在这里', LENS['换人身自由']),
    ]
    top, step = .79, .1
    f.add_artist(FancyBboxPatch((.06, top - step * len(rows) + .02), .54, step * len(rows) + .02, boxstyle='round,pad=0,rounding_size=.015',
                                transform=f.transFigure, fc=CARD, ec=LINE, lw=1.2))
    for i, (k, v, why, c) in enumerate(rows):
        y = top - i * step
        f.text(.085, y - .005, k, fontproperties=SANS_B, fontsize=12, color=c, va='top')
        if k == '证据等级':
            f.add_artist(FancyBboxPatch((.2, y - .042), .05, .036, boxstyle='round,pad=0,rounding_size=.006', transform=f.transFigure, fc=c, ec='none'))
            f.text(.225, y - .024, 'A', fontproperties=SANS_B, fontsize=14, color='white', ha='center', va='center')
        else:
            f.text(.2, y - .005, v, fontsize=11, color=INK, va='top', linespacing=1.45)
        f.add_artist(plt.Line2D([.61, .655], [y - .02, y - .02], transform=f.transFigure, color=c, lw=1.3))
        f.add_artist(plt.Circle((.655, y - .02), .0045, transform=f.transFigure, color=c))
        f.text(.67, y - .02, why, fontsize=11.3, color=INK, va='center')
    f.text(.06, .075, '隐藏标签：钱=少 时间=少 毅力=否 收益=中 口径=死亡率。证据是 A 级，性价比却只算「一般」。', fontsize=10.5, color=MUTED)
    save(f, '03_条目结构.png')


def waffle():
    f = frame('672 条建议，换回四样东西', '每格一条｜颜色 = 换回什么，深浅 = 性价比档（深：极高　中：高　浅：一般）', size=(10, 8.6))
    order = {k: i for i, k in enumerate(LENS_ORDER)}
    tiers = {'极高': 0, '高': 1, '一般': 2}
    d = df.assign(o=df.口径名.map(order), t=df.性价比.map(tiers)).sort_values(['o', 't'])
    cols, rows = 28, 24
    ax = f.add_axes((.06, .2, .88, .6))
    clean(ax)
    white = matplotlib.colors.to_rgb(CARD)
    for i, r in enumerate(d.itertuples()):
        cx, cy = i % cols, rows - 1 - i // cols
        base = matplotlib.colors.to_rgb(LENS[r.口径名])
        a = TIER[r.性价比]
        col = tuple(a * b + (1 - a) * w for b, w in zip(base, white))
        ax.add_patch(FancyBboxPatch((cx + .08, cy + .08), .84, .84, boxstyle='round,pad=0,rounding_size=.18', fc=col, ec='none'))
    ax.set_xlim(0, cols); ax.set_ylim(0, rows); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for i, k in enumerate(LENS_ORDER):
        g = df[df.口径名 == k]
        x = .06 + i * .225
        f.text(x, .145, k, fontproperties=SANS_B, fontsize=13.5, color=LENS[k])
        f.text(x, .105, f'{len(g)} 条｜极高 {int((g.性价比 == "极高").sum())}', fontsize=11, color=INK)
    save(f, '04_四种资源华夫图.png')


def funnel():
    d = df
    m0 = d.钱 == '0'
    m1 = m0 & (d.时间 == '少')
    m2 = m1 & (d.毅力 == '否')
    m3 = m2 & (d.收益量级 == '大')
    steps = [('全部建议', len(d)), ('不花钱', m0.sum()), ('且只占顺手时间', m1.sum()), ('且不需要毅力（零成本）', m2.sum()),
             ('且收益落在最大一档 = 性价比极高', m3.sum())]
    f = frame('从 672 条到 114 条「极高」', '三项成本全为零、收益又落在“大”档，才算性价比极高', size=(10, 7.4))
    ax = f.add_axes((.06, .14, .88, .66))
    clean(ax)
    n0 = steps[0][1]
    for i, (label, n) in enumerate(steps):
        y = len(steps) - 1 - i
        w = n / n0
        last = i == len(steps) - 1
        ax.add_patch(FancyBboxPatch((.5 - w / 2, y + .16), w, .68, boxstyle='round,pad=0,rounding_size=.04',
                                    fc=LENS['换寿命'] if last else '#2F4855', alpha=1 if last else .25 + .15 * i, ec='none'))
        ax.text(.5, y + .5, f'{n}', fontproperties=TITLE, fontsize=24, color='white' if i >= 2 else INK, ha='center', va='center')
        if w < .8:
            ax.text(.5 - w / 2 - .015, y + .5, label, fontsize=12, color=INK, ha='right', va='center')
        else:
            ax.text(.5 - w / 2 + .02, y + .5, label, fontsize=12, color=INK, ha='left', va='center')
        if i:
            ax.text(.5 + w / 2 + .015, y + .5, f'{n / n0:.0%}', fontsize=11.5, color=MUTED, va='center')
    ax.set_xlim(-.35, 1.05); ax.set_ylim(0, len(steps)); ax.set_xticks([]); ax.set_yticks([])
    save(f, '05_零成本漏斗.png')


def chapters():
    d = sec.copy()
    d['短名'] = d.节名.str.split('：').str[0]
    f = frame('34 节，每节有多少条、证据多硬', '条形 = 条目数，按 A / B / C 证据等级分段｜右列红点 = 性价比极高条数', size=(10, 14))
    ax = f.add_axes((.30, .05, .52, .8))
    clean(ax)
    y = np.arange(len(d))[::-1]
    left = np.zeros(len(d))
    for g in 'ABC':
        ax.barh(y, d[g], left=left, height=.66, color=GRADE[g], label=f'{g} 级')
        left += d[g]
    for yi, r in zip(y, d.itertuples()):
        ax.text(r.条目 + .8, yi, str(r.条目), va='center', fontsize=10.5, color=INK)
    ax.set_yticks(y, [f'{n:>2}  {s}' for n, s in zip(d.节, d.短名)], fontsize=10.8, color=INK)
    ax.set_xlim(0, 52); ax.set_xticks([0, 10, 20, 30, 40]); ax.tick_params(axis='x', labelsize=10)
    ax.xaxis.grid(color=LINE, lw=.8); ax.set_axisbelow(True); ax.set_ylim(-.7, len(d) - .3)
    ax.legend(loc='lower left', frameon=False, fontsize=10.5, ncol=3, bbox_to_anchor=(-.02, 1.0))
    ax2 = f.add_axes((.85, .05, .1, .8))
    clean(ax2)
    ax2.scatter(np.full(len(d), .3), y, s=d.极高 * 22 + 4, color=LENS['换寿命'], alpha=.9, lw=0)
    for yi, n in zip(y, d.极高):
        ax2.text(.62, yi, str(n), va='center', fontsize=10, color=LENS['换寿命'] if n else MUTED)
    ax2.set_xlim(0, 1); ax2.set_ylim(-.7, len(d) - .3); ax2.set_xticks([]); ax2.set_yticks([])
    f.text(.85, .862, '极高', fontproperties=SANS_B, fontsize=11, color=LENS['换寿命'])
    save(f, '06_章节证据.png')


def lens_matrix():
    f = frame('换寿命争议最多，换自由证据最硬', '按“换回什么”拆开看证据等级与争议条目', size=(10, 7.2))
    ax = f.add_axes((.2, .2, .72, .58))
    clean(ax)
    y = np.arange(4)[::-1]
    for yi, k in zip(y, LENS_ORDER):
        g = df[df.口径名 == k]
        n = len(g)
        left = 0
        for gr in 'ABC':
            v = (g.证据 == gr).sum() / n
            ax.barh(yi, v, left=left, height=.5, color=GRADE[gr])
            if v > .07:
                ax.text(left + v / 2, yi, f'{gr} {v:.0%}', ha='center', va='center', fontsize=10.5, color='white' if gr != 'C' else INK)
            left += v
        disp = int(g.争议.sum())
        ax.text(1.03, yi, f'{disp}', fontproperties=TITLE, fontsize=17, color=LENS['换寿命'] if disp else MUTED, va='center')
        ax.text(-.02, yi + .06, k, fontproperties=SANS_B, fontsize=13, color=LENS[k], ha='right', va='center')
        ax.text(-.02, yi - .2, f'{n} 条', fontsize=10, color=MUTED, ha='right', va='center')
    ax.text(1.03, 3.55, '争议', fontproperties=SANS_B, fontsize=11, color=LENS['换寿命'])
    ax.set_xlim(0, 1.12); ax.set_ylim(-.6, 3.8); ax.set_xticks([]); ax.set_yticks([])
    f.text(.06, .1, '全书 70 条标注「争议」，50 条在健康类；法律类的 A 级指引到了法条或官方文件原文。', fontsize=11, color=INK)
    save(f, '07_口径证据.png')


def sources():
    cats = {'学术论文（DOI / PubMed）': 0, '中国官方（法规·司法·部委·地方政府）': 0, '境外官方与国际组织': 0, '新闻报道与网页存档': 0, '其他机构网站': 0}
    raw = pd.read_csv(DATA / '来源域名.csv')
    for d, n in zip(raw.域名, raw.次数):
        if d == 'doi.org' or 'pubmed' in d or 'ncbi.nlm' in d:
            k = '学术论文（DOI / PubMed）'
        elif d.endswith('.gov.cn') or d.endswith('.mil.cn'):
            k = '中国官方（法规·司法·部委·地方政府）'
        elif re.search(r'(\.gov|\.int|\.gov\.uk|nice\.org\.uk|uspreventiveservicestaskforce\.org|ifrc\.org|\.state\.\w\w\.us|\.europa\.eu|\.gc\.ca|\.gov\.au)$', d):
            k = '境外官方与国际组织'
        elif re.search(r'archive\.org|news\.cn|thepaper\.cn|people\.com\.cn|xinhuanet|cctv|chinanews|caixin|infzm|bjnews', d):
            k = '新闻报道与网页存档'
        else:
            k = '其他机构网站'
        cats[k] += n
    pd.Series(cats).rename('链接数').to_csv(DATA / '来源分类.csv', encoding='utf-8-sig')
    total = sum(cats.values())
    f = frame(f'{total:,} 条出处，都指向哪里', '按链接域名归类｜同一条建议可引用多个出处', size=(10, 6.8))
    ax = f.add_axes((.06, .5, .88, .14))
    clean(ax)
    colors = [LENS['换时间精力'], LENS['换寿命'], LENS['换人身自由'], LENS['换钱'], '#B9B2A5']
    left = 0
    for (k, v), c in zip(cats.items(), colors):
        ax.barh(0, v, left=left, color=c, height=1, edgecolor=BG, lw=2)
        if v / total > .06:
            ax.text(left + v / 2, 0, f'{v / total:.0%}', ha='center', va='center', fontproperties=TITLE, fontsize=18, color='white')
        left += v
    ax.set_xlim(0, total); ax.set_ylim(-.5, .5); ax.set_xticks([]); ax.set_yticks([])
    for i, ((k, v), c) in enumerate(zip(cats.items(), colors)):
        x = .06 + (i % 2) * .45
        yy = .4 - (i // 2) * .085
        f.add_artist(Rectangle((x, yy - .012), .016, .03, transform=f.transFigure, color=c, lw=0))
        f.text(x + .028, yy, k, fontsize=12, color=INK, va='center')
        f.text(x + .41, yy, f'{v}', fontproperties=SANS_B, fontsize=12.5, color=INK, va='center', ha='right')
    top = raw.head(5)
    f.text(.06, .73, '引用最多的域名：' + '　'.join(f'{d} {n}' for d, n in zip(top.域名, top.次数)), fontsize=10.8, color=MUTED)
    save(f, '08_来源构成.png')


def picks():
    items = {
        '换寿命': [('1-1', '系安全带，前排后排都系'), ('13-3', '嘴歪、一侧没劲、说话不清，立刻打 120'), ('13-14', '烫伤后流动凉水冲 20 分钟'),
                 ('20-2', '新生儿 24 小时内打乙肝第一针'), ('34-1', '两种感冒药同吃前看成分表')],
        '换钱': [('8-2', '发现被骗，立刻打 110 / 96110 止付'), ('5-6', '看到「高收益」「保本」「稳赚」就走'), ('8-19', '维权有期限：诉讼 3 年，仲裁 1 年'),
                ('19-4', '被裁先算清经济补偿 N'), ('14-1', '常用账号都开二次验证')],
        '换时间精力': [('3-6', '连续思考时，挡住哪怕几秒的打断'), ('4-1', '把「打算做」写成几点、在哪、做什么'), ('4-4', '按过去的实际耗时估工期')],
        '换人身自由': [('9-5', '不用自己的卡替人收钱、取现、转账'), ('8-1', '出了交通事故先停车、救人、报警'), ('9-16', '身份证不借人，也不用别人的'),
                  ('9-9', '阳台窗户不往外扔任何东西'), ('11-3', '不写、不卖抢票刷单脚本')],
    }
    f = frame('先从这 18 条「极高」开始', '性价比极高 = 不花钱、不占时间、不用毅力，收益又最大｜编号为“节-条”', size=(10, 10.6))
    W, H = .425, .37
    for i, k in enumerate(LENS_ORDER):
        x = .06 + (i % 2) * (W + .03)
        y0 = .47 - (i // 2) * (H + .02)
        c = LENS[k]
        card(f, x, y0, W, H, c, top=True)
        g = df[(df.口径名 == k) & (df.性价比 == '极高')]
        f.text(x + .025, y0 + H - .045, k, fontproperties=TITLE, fontsize=19, color=c, va='center')
        f.text(x + W - .025, y0 + H - .045, f'极高共 {len(g)} 条', fontsize=10.5, color=MUTED, va='center', ha='right')
        for j, (ref, t) in enumerate(items[k]):
            yy = y0 + H - .1 - j * .056
            f.add_artist(FancyBboxPatch((x + .025, yy - .014), .052, .028, boxstyle='round,pad=0,rounding_size=.006', transform=f.transFigure, fc=c, alpha=.12, ec='none'))
            f.text(x + .051, yy, ref, fontproperties=SANS_B, fontsize=9.5, color=c, ha='center', va='center')
            f.text(x + .09, yy, t, fontsize=11, color=INK, va='center')
    save(f, '01_极高精选.png')


if __name__ == '__main__':
    for p in IMG.glob('0*.png'):
        p.unlink()
    picks(); overview(); anatomy(); waffle(); funnel(); chapters(); lens_matrix(); sources()
