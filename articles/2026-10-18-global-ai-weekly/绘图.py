"""本周AI要闻配图：一周时间线、芯片股本周涨跌幅。时间线来自公开报道，手工录入；行情数据由 采集数据.py 生成。

画布宽8英寸、130dpi（约1040px），正文字号15pt以上，保证手机端缩放后仍可读。
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '配图'
OUT.mkdir(exist_ok=True)
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyhbd.ttc')
plt.rcParams.update({'font.family': 'Microsoft YaHei', 'axes.unicode_minus': False})

# 视觉轮换方案（2026-10-11起）：白底、靛蓝/珊瑚/紫色；A股习惯下跌用绿色
BG, INK, MUTED, GRID = '#FAFAFE', '#202B54', '#6B7290', '#E4E6F1'
INDIGO, CORAL, VIOLET, DOWN = '#4457C4', '#DB655A', '#9471BE', '#13895E'
BRAND = '可以叫我才哥'
W, DPI = 8, 130


def finish(fig, title, sub, note, h):
    """标题区固定高度（英寸），换算为画布比例。"""
    fig.text(0.05, 1 - 0.5 / h, title, color=INK, fontsize=22, weight='bold', va='center')
    fig.text(0.05, 1 - 0.95 / h, sub, color=MUTED, fontsize=13, va='center')
    fig.text(0.05, 0.28 / h, note, color=MUTED, fontsize=10.5, va='center')
    fig.text(0.95, 0.28 / h, BRAND, color=MUTED, fontsize=11, ha='right', weight='bold', va='center')


def clean(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, colors=MUTED)


def fig_timeline():
    """竖版时间线：行为日期，列为三条主线。"""
    days = ['10/12 周一', '10/13 周二', '10/14 周三', '10/15 周四', '10/16 周五', '10/17 周六']
    lanes = [('模型', INDIGO), ('监管', CORAL), ('资本·基建', VIOLET)]
    events = [
        (0, 0, 'Meta\nMuse Wonder'), (1, 0, 'Gemini 4\nArgon 开放'),
        (3, 0, 'Meta 开放权重\nSpark Open'), (3, 0, '微软\nMAI-Base-2'),
        (5, 0, 'DeepSeek\nV4.1-Flash'),
        (1, 1, '约400位\n科学家联名'), (2, 1, '美国8州\n起诉OpenAI'),
        (2, 1, '欧盟AI办公室\n信息请求'), (3, 1, 'FTC调查令\n被曝光'),
        (3, 2, 'SK海力士\n单日跌超10%'), (4, 2, '加拿大100亿\n加元数据中心'),
        (4, 2, '旧金山数据中心\n45天暂停令'),
    ]
    h = 11.5
    fig, ax = plt.subplots(figsize=(W, h), dpi=DPI, facecolor=BG)
    clean(ax)
    # 每天的行高按当天单条主线最多事件数分配
    per_day = [max(sum(1 for e in events if e[0] == d and e[1] == l) for l in range(3)) or 1 for d in range(len(days))]
    tops, y = [], 0
    for n in per_day:
        tops.append(y)
        y += n * 0.9 + 0.25
    total = y
    ax.set_xlim(-0.05, 3.0)
    ax.set_ylim(total, -0.75)
    for i, (name, c) in enumerate(lanes):
        ax.add_patch(FancyBboxPatch((i + 0.04, -0.7), 0.92, total + 0.6, boxstyle='round,pad=0,rounding_size=0.05',
                                    fc=c, alpha=.06, ec='none', zorder=0))
        ax.text(i + 0.5, -0.38, name, ha='center', va='center', fontsize=17, color=c, weight='bold')
    for d, label in enumerate(days):
        mid = tops[d] + per_day[d] * 0.45
        ax.axhline(tops[d] - 0.12, color=GRID, lw=1, zorder=0)
        ax.text(-0.04, mid, label.replace(' ', '\n'), ha='right', va='center', fontsize=14, color=INK, linespacing=1.4)
    count = {}
    for d, lane, txt in events:
        j = count.get((d, lane), 0)
        count[(d, lane)] = j + 1
        c = lanes[lane][1]
        y0 = tops[d] + j * 0.9
        ax.add_patch(FancyBboxPatch((lane + 0.1, y0 + 0.04), 0.8, 0.78, boxstyle='round,pad=0,rounding_size=0.06',
                                    fc='white', ec=c, lw=2, zorder=3))
        ax.text(lane + 0.5, y0 + 0.43, txt, ha='center', va='center', fontsize=14, color=INK, zorder=5, linespacing=1.35)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.subplots_adjust(top=1 - 1.35 / h, bottom=0.6 / h, left=.17, right=.97)
    finish(fig, '一周AI大事时间线', '2026年10月12日—18日，按事件公开日期排列',
           '来源：官方页面、Hugging Face、Axios、CP24 等公开报道', h)
    fig.savefig(OUT / '图1_一周时间线.png', facecolor=BG)
    plt.close(fig)


def fig_chips():
    """本周累计涨跌幅：数据来自 采集数据.py 输出的 数据/芯片股本周涨跌幅.csv。"""
    import pandas as pd
    df = pd.read_csv(ROOT / '数据' / '芯片股本周涨跌幅.csv').sort_values('周涨跌幅%')
    h = 10
    fig, ax = plt.subplots(figsize=(W, h), dpi=DPI, facecolor=BG)
    clean(ax)
    for i, r in enumerate(df.itertuples()):
        v = r._7
        etf = r.代码 == 'SOXX'
        ax.barh(i, v, color=VIOLET if etf else DOWN, height=.62, alpha=1 if (etf or v <= -14) else .55)
        ax.text(v - 0.4, i, f'{v:.1f}%', ha='right', va='center', fontsize=15,
                color=VIOLET if etf else DOWN, weight='bold')
        ax.text(0.4, i, r.市场, ha='left', va='center', fontsize=12.5, color=MUTED)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels([n.replace('半导体ETF（SOXX）', '半导体ETF') for n in df.名称], fontsize=14.5, color=INK)
    for t in ax.get_yticklabels():
        if t.get_text() == '半导体ETF':
            t.set_color(VIOLET)
            t.set_weight('bold')
    ax.invert_yaxis()
    ax.set_xlim(-30, 4.5)
    ax.axvline(0, color=INK, lw=1.2)
    ax.set_xticks([])
    fig.subplots_adjust(top=1 - 1.35 / h, bottom=0.6 / h, left=.24, right=.97)
    finish(fig, '本周芯片股全线下跌', '10月12日—16日累计涨跌幅，紫色为半导体ETF',
           '数据：Yahoo Finance 日线收盘；韩国基准为10月8日收盘（9日休市）', h)
    fig.savefig(OUT / '图3_芯片股本周涨跌幅.png', facecolor=BG)
    plt.close(fig)

if __name__ == '__main__':
    fig_timeline()
    fig_chips()
    print('ok')
