"""A股主题"元素周期表"：年度/月度涨跌排名表（红涨绿跌版与大类配色版）、重点主题排名九宫格、冠军次年排名、10年累计，及逐年揭晓动图。"""
from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, to_rgb
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '图表'
OUT.mkdir(exist_ok=True)
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyhbd.ttc')
plt.rcParams.update({'font.family': 'Microsoft YaHei', 'axes.unicode_minus': False})

# 视觉轮换方案（2026-10-11起）：白底、靛蓝/珊瑚/紫色；红绿只表示涨跌
BG, INK, MUTED, GRID, INDIGO = '#FAFAFE', '#202B54', '#6B7290', '#E4E6F1', '#4457C4'
UP, DOWN = '#D63A2F', '#13895E'
CMAP = LinearSegmentedColormap.from_list('cn', [DOWN, '#8FD0B1', '#ECEEF4', '#F1A096', UP])
BRAND = '可以叫我才哥'
GROUPS = {
    '科技': ('#4457C4', ['人工智能', '5G通信', '半导体', '云计算', '消费电子']),
    '高端制造': ('#9471BE', ['机器人', '智能汽车', '军工', '卫星产业']),
    '新能源与电力': ('#2B8DB0', ['新能源', '光伏', '电池', '核电', '电网设备']),
    '资源': ('#C8813B', ['油气', '有色金属', '黄金采掘', '稀土']),
    '金融': ('#202B54', ['银行', '证券']),
    '消费医药': ('#C2649A', ['主要消费', '白酒', '生物科技', '创新药', '医疗器械']),
}
GROUP_COLOR = {n: c for c, names in GROUPS.values() for n in names}
GROUP_OF = {n: g for g, (_, names) in GROUPS.items() for n in names}
FOCUS = ['白酒', '银行', '半导体', '新能源', '稀土', '黄金采掘', '5G通信', '创新药', '消费电子']
YEARS = list(range(2017, 2027))
VERSION = {'rg': '红绿', 'group': '大类'}


def load():
    raw = json.loads((ROOT / '数据' / '主题指数日线.json').read_text(encoding='utf-8'))
    df = pd.DataFrame({n: pd.Series({d: c for d, c in v['rows']}) for n, v in raw['series'].items()})
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    assert len(df.columns) == 25 and set(FOCUS) <= set(df.columns)
    return df, pd.Timestamp(raw['cutoff']), raw


def yearly(df):
    ye = df.groupby(df.index.year).last()   # 每年最后一个交易日收盘
    return ((ye / ye.shift(1) - 1) * 100).loc[YEARS]


def finish(fig, title, sub, note, top=0.955):
    fig.text(0.04, top, title, color=INK, fontsize=21, weight='bold')
    fig.text(0.04, top - 0.03, sub, color=MUTED, fontsize=11.5)
    fig.text(0.04, 0.012, note, color=MUTED, fontsize=8.5)
    fig.text(0.96, 0.012, BRAND, color=MUTED, fontsize=9, ha='right', weight='bold')


def tint(c, k):
    """大类配色版：k∈[0,1]，涨跌幅越大颜色越饱和。"""
    r, g, b = to_rgb(c)
    w = 0.55 * (1 - k)
    return (r + (1 - r) * w, g + (1 - g) * w, b + (1 - b) * w)


def key(fig, y, lim, unit='%', mode='rg'):
    """红绿版：色阶 + 大类色条；大类版：大类色块 + 深浅说明。"""
    if mode == 'group':
        x = 0.04
        for g, (c, _) in GROUPS.items():
            fig.patches.append(plt.Rectangle((x, y - 0.003), 0.014, 0.012, color=c, transform=fig.transFigure, figure=fig))
            fig.text(x + 0.019, y + 0.003, g, color=INK, fontsize=10, va='center')
            x += 0.03 + 0.0115 * len(g)
        fig.text(0.96, y + 0.003, '颜色越深，涨跌幅越大', color=MUTED, fontsize=9.5, va='center', ha='right')
        return
    cax = fig.add_axes([0.04, y, 0.26, 0.008])
    norm = TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim)
    cax.imshow(np.linspace(-lim, lim, 256)[None, :], aspect='auto', cmap=CMAP, norm=norm, extent=[-lim, lim, 0, 1])
    cax.set_yticks([])
    cax.set_xticks([-lim, 0, lim])
    cax.set_xticklabels([f'跌≥{lim}{unit}', '0', f'涨≥{lim}{unit}'], fontsize=9, color=MUTED)
    cax.tick_params(length=0, pad=3)
    for s in cax.spines.values():
        s.set_visible(False)
    x = 0.36
    for g, (c, _) in GROUPS.items():
        fig.patches.append(plt.Rectangle((x, y - 0.003), 0.005, 0.014, color=c, transform=fig.transFigure, figure=fig))
        fig.text(x + 0.009, y + 0.004, g, color=INK, fontsize=9.5, va='center')
        x += 0.018 + 0.0105 * len(g)


def table_axes(fig, ret, cols, labels, lim, upto=None, rect=(0.04, 0.035, 0.92, 0.815), mode='rg'):
    ax = fig.add_axes(rect)
    ax.set_facecolor(BG)
    norm = TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim)
    n = len(ret.columns)
    for j, col in enumerate(cols):
        if upto is not None and j > upto:
            continue
        s = ret.loc[col].sort_values(ascending=False)
        span = max(s.abs().max(), 1)
        for i, (name, v) in enumerate(s.items()):
            focus = name in FOCUS
            if mode == 'group':
                fc = tint(GROUP_COLOR[name], min(1, abs(v) / span) ** .6)
                ax.add_patch(plt.Rectangle((j + .04, i + .05), .92, .9, color=fc, lw=0))
                dark = sum(to_rgb(fc)) / 3 <= .72
            else:
                fc = CMAP(norm(np.clip(v, -lim, lim)))
                ax.add_patch(plt.Rectangle((j + .05, i + .06), .9, .88, color=fc, lw=0))
                ax.add_patch(plt.Rectangle((j + .05, i + .06), .06, .88, color=GROUP_COLOR[name], lw=0))
                dark = abs(v) > lim * .55
            tc = 'white' if dark else INK
            ax.text(j + .53, i + .36, name, ha='center', va='center', fontsize=10 if focus else 9.2, color=tc,
                    weight='bold' if focus else 'normal', alpha=1 if focus or dark else .78)
            ax.text(j + .53, i + .7, f'{v:+.1f}%', ha='center', va='center', fontsize=8.8, color=tc,
                    alpha=1 if focus or dark else .78)
    ax.set_xlim(0, len(cols))
    ax.set_ylim(n, 0)
    ax.set_xticks(np.arange(len(cols)) + .5)
    ax.set_xticklabels(labels, fontsize=11, color=INK, weight='bold')
    ax.xaxis.tick_top()
    ax.set_yticks([.5, n - .5])
    ax.set_yticklabels(['第1', f'第{n}'], fontsize=9, color=MUTED)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    return ax


SUB = {'rg': '每列从高到低排序，红涨绿跌，颜色越深幅度越大', 'group': '每列从高到低排序，颜色表示所属大类'}


def fig_table(ret, cutoff, upto=None, path=None, mode='rg'):
    fig = plt.figure(figsize=(12, 15.5), dpi=130, facecolor=BG)
    labels = [str(y) if y < 2026 else '2026*' for y in YEARS]
    table_axes(fig, ret, YEARS, labels, lim=50, upto=upto, mode=mode)
    finish(fig, 'A股主题"元素周期表"：每年谁是冠军？',
           '25个中证主题指数年度涨跌幅，' + SUB[mode],
           f'*2026年截至{cutoff.month}月{cutoff.day}日  ·  数据：中证指数有限公司  ·  价格指数，不含分红')
    key(fig, 0.893, 50, mode=mode)
    if path:
        fig.savefig(path, facecolor=BG)
        plt.close(fig)
    return fig


def fig_months(df, cutoff, mode='rg'):
    me = df.resample('ME').last()
    mret = (me / me.shift(1) - 1) * 100
    cols = list(mret.index[-12:])
    ret = mret.loc[cols]
    labels = [f'{c.year % 100}/{c.month}' + ('*' if c == cols[-1] else '') for c in cols]
    fig = plt.figure(figsize=(13, 15.5), dpi=130, facecolor=BG)
    table_axes(fig, ret, cols, labels, lim=20, mode=mode)
    finish(fig, '最近12个月：月度冠军换得有多快？',
           '25个中证主题指数月度涨跌幅，' + SUB[mode],
           f'*{cutoff.month}月截至{cutoff.day}日  ·  数据：中证指数有限公司  ·  价格指数，不含分红')
    key(fig, 0.893, 20, mode=mode)
    fig.savefig(OUT / f'图6_近12个月月度周期表_{VERSION[mode]}.png', facecolor=BG)
    plt.close(fig)
    return {f'{c:%Y-%m}': {'冠军': ret.loc[c].idxmax(), '垫底': ret.loc[c].idxmin(),
                            '红格数': int((ret.loc[c] > 0).sum())} for c in cols}


def fig_focus(ret, cutoff):
    """9个重点主题的排名九宫格：灰线为其余主题，圆点按当年涨跌标红绿。"""
    rank = ret.rank(axis=1, ascending=False)
    fig, axes = plt.subplots(3, 3, figsize=(12, 11.5), dpi=130, facecolor=BG, sharex=True, sharey=True)
    for ax, n in zip(axes.flat, FOCUS):
        ax.set_facecolor(BG)
        for m in rank.columns:
            ax.plot(YEARS, rank[m], color='#E3E5EE', lw=.9, zorder=1)
        ax.plot(YEARS, rank[n], color=INK, lw=2.4, zorder=2)
        ax.scatter(YEARS, rank[n], s=46, zorder=3, c=[UP if v > 0 else DOWN for v in ret[n]], edgecolor='white', lw=.8)
        top = int((rank[n] <= 3).sum())
        bot = int((rank[n] >= 23).sum())
        ax.set_title(n, loc='left', fontsize=14, color=INK, weight='bold', pad=6)
        ax.text(1, 1.04, f'前3：{top}次  后3：{bot}次', transform=ax.transAxes, ha='right', fontsize=9.5, color=MUTED)
        ax.set_ylim(26, 0)
        ax.set_yticks([1, 13, 25])
        ax.set_yticklabels(['第1', '第13', '第25'], fontsize=8.5, color=MUTED)
        ax.set_xticks([2017, 2020, 2023, 2026])
        ax.set_xticklabels(['2017', '2020', '2023', '2026*'], fontsize=8.5, color=MUTED)
        ax.tick_params(length=0)
        ax.grid(axis='y', color=GRID, lw=.7)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.subplots_adjust(top=.86, bottom=.06, left=.06, right=.97, hspace=.38, wspace=.12)
    fig.text(0.78, 0.928, '●', color=UP, fontsize=12, va='center')
    fig.text(0.795, 0.928, '当年上涨', color=INK, fontsize=10, va='center')
    fig.text(0.865, 0.928, '●', color=DOWN, fontsize=12, va='center')
    fig.text(0.88, 0.928, '当年下跌', color=INK, fontsize=10, va='center')
    finish(fig, '9个重点主题的排名过山车',
           '每年在25个主题中的涨幅排名（第1在最上），灰线为其余主题',
           f'*2026年截至{cutoff.month}月{cutoff.day}日  ·  数据：中证指数有限公司', top=.955)
    fig.savefig(OUT / '图4_重点主题排名.png', facecolor=BG)
    plt.close(fig)


def fig_persistence(ret, cutoff):
    rank = ret.rank(axis=1, ascending=False)
    rows = []
    for a, b in zip(YEARS[:-1], YEARS[1:]):
        champ = ret.loc[a].idxmax()
        top5 = set(rank.columns[rank.loc[a] <= 5])
        rows.append({'year': a, 'next': b, 'champ': champ, 'champ_ret': ret.loc[a, champ],
                     'champ_next_rank': int(rank.loc[b, champ]), 'champ_next_ret': ret.loc[b, champ],
                     'top5_stay': len(top5 & set(rank.columns[rank.loc[b] <= 5])),
                     'spearman': ret.loc[a].corr(ret.loc[b], method='spearman')})
    t = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(12, 7.4), dpi=130, facecolor=BG)
    ax.set_facecolor(BG)
    for i, r in t.iterrows():
        y = r.champ_next_rank
        ax.annotate('', xy=(i, y - .7), xytext=(i, 1.7), arrowprops=dict(arrowstyle='-|>', color=MUTED, lw=1.4, mutation_scale=14))
        c = GROUP_COLOR[r.champ]
        ax.scatter(i, 1, s=420, color=c, zorder=3)
        ax.scatter(i, y, s=420, facecolor=BG, edgecolor=c, lw=2.6, zorder=3)
        ax.text(i, y + 1.3, f'第{y}', ha='center', va='top', fontsize=11.5, color=INK, weight='bold')
        ax.text(i, y + 2.7, f'{r.champ_next_ret:+.1f}%', ha='center', va='top', fontsize=10,
                color=UP if r.champ_next_ret > 0 else DOWN, weight='bold')
        ax.text(i, -.4, r.champ, ha='center', va='bottom', fontsize=11, color=c, weight='bold')
        ax.text(i + .2, 1, f'{r.champ_ret:+.1f}%', ha='left', va='center', fontsize=10,
                color=UP if r.champ_ret > 0 else DOWN, weight='bold')
    ax.set_ylim(29, -2.3)
    ax.set_xlim(-.6, len(t) - .4)
    ax.set_xticks(range(len(t)))
    ax.set_xticklabels([f'{a}→{b}' + ('*' if b == 2026 else '') for a, b in zip(t.year, t.next)], fontsize=10.5, color=INK)
    ax.set_yticks([1, 5, 10, 15, 20, 25])
    ax.set_yticklabels(['第1', '第5', '第10', '第15', '第20', '第25'], fontsize=10, color=MUTED)
    ax.tick_params(length=0)
    ax.grid(axis='y', color=GRID, lw=.8)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.subplots_adjust(top=.84, bottom=.08, left=.07, right=.97)
    key(fig, 0.875, 50, mode='group')
    fig.texts[-1].remove()  # 只要大类图例
    finish(fig, '今年的冠军，明年排第几？',
           f'实心圆：当年涨幅第1的主题及其涨跌；空心圆：它在下一年的排名和涨跌。9次里平均排在第{t.champ_next_rank.mean():.0f}名',
           f'*2026年截至{cutoff.month}月{cutoff.day}日  ·  数据：中证指数有限公司', top=.945)
    fig.savefig(OUT / '图3_冠军次年排名.png', facecolor=BG)
    plt.close(fig)
    return t


def fig_total(df, ret, cutoff):
    base = df[df.index <= '2016-12-31'].iloc[-1]
    total = ((df.iloc[-1] / base - 1) * 100).sort_values()
    best, worst = ret.max(), ret.min()
    fig, ax = plt.subplots(figsize=(12, 11), dpi=130, facecolor=BG)
    ax.set_facecolor(BG)
    for i, (n, v) in enumerate(total.items()):
        focus = n in FOCUS
        ax.barh(i, v, height=.66, color=UP if v >= 0 else DOWN, alpha=1 if focus else .45)
        ax.text(v + (6 if v >= 0 else -6), i, f'{v:+.1f}%', va='center', ha='left' if v >= 0 else 'right',
                fontsize=10.5, color=INK, weight='bold' if focus else 'normal')
        ax.add_patch(plt.Rectangle((-160, i - .3), 3.5, .6, color=GROUP_COLOR[n], lw=0))
        ax.text(-152, i, n, va='center', ha='left', fontsize=11.5 if focus else 10.5, color=INK,
                weight='bold' if focus else 'normal', alpha=1 if focus else .75)
        ax.text(400, i, f'最好 {best[n]:+.1f}%（{int(ret[n].idxmax())}）  最差 {worst[n]:+.1f}%（{int(ret[n].idxmin())}）',
                va='center', fontsize=9.2, color=MUTED)
    ax.axvline(0, color=MUTED, lw=.8)
    ax.set_xlim(-160, 640)
    ax.set_ylim(-.7, len(total) - .3)
    ax.axis('off')
    fig.subplots_adjust(top=.85, bottom=.04, left=.03, right=.98)
    key(fig, 0.885, 50)
    fig.axes[-1].remove()  # 累计图只保留大类图例，不需要色阶
    finish(fig, '把10年加起来：谁是长跑冠军？',
           '2016年末至今累计涨跌幅；右侧为单年最好与最差表现',
           f'截至{cutoff:%Y年%m月%d日}  ·  数据：中证指数有限公司  ·  价格指数，不含分红', top=.95)
    fig.savefig(OUT / '图5_10年累计.png', facecolor=BG)
    plt.close(fig)
    return total


def make_gif(ret, cutoff):
    frames = []
    for j in range(len(YEARS)):
        fig = fig_table(ret, cutoff, upto=j)
        fig.canvas.draw()
        img = Image.frombuffer('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert('RGB')
        plt.close(fig)
        frames.append(img.resize((img.width * 3 // 4, img.height * 3 // 4), Image.LANCZOS))
    pal = frames[-1].quantize(colors=160, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(OUT / '图1_逐年揭晓.gif', save_all=True, append_images=q[1:],
              duration=[900] * (len(q) - 1) + [3500], loop=0, optimize=True)


def main():
    df, cutoff, raw = load()
    ret = yearly(df)
    for mode in VERSION:
        fig_table(ret, cutoff, path=OUT / f'图2_年度周期表_{VERSION[mode]}.png', mode=mode)
    fig_focus(ret, cutoff)
    t = fig_persistence(ret, cutoff)
    total = fig_total(df, ret, cutoff)
    months = fig_months(df, cutoff)
    fig_months(df, cutoff, mode='group')
    make_gif(ret, cutoff)
    rank = ret.rank(axis=1, ascending=False)
    stats = {
        '截止日': f'{cutoff:%Y-%m-%d}',
        '重点主题': FOCUS,
        '指数清单': {n: {'代码': v['code'], '全称': v['full_name'], '对应东财主题': v['eastmoney_theme'], '大类': GROUP_OF[n]}
                 for n, v in raw['series'].items()},
        '年度涨跌': {int(y): {n: round(v, 2) for n, v in ret.loc[y].sort_values(ascending=False).items()} for y in YEARS},
        '年度冠军': {int(y): ret.loc[y].idxmax() for y in YEARS},
        '年度垫底': {int(y): ret.loc[y].idxmin() for y in YEARS},
        '年度上涨主题数': {int(y): int((ret.loc[y] > 0).sum()) for y in YEARS},
        '冠军次年': {f'{r.year}→{r.next}': {'冠军': r.champ, '当年涨跌': round(r.champ_ret, 2), '次年排名': r.champ_next_rank,
                                            '次年涨跌': round(r.champ_next_ret, 2)} for r in t.itertuples()},
        '冠军次年平均排名': round(float(t.champ_next_rank.mean()), 2),
        '前5次年仍在前5的个数': {f'{r.year}→{r.next}': r.top5_stay for r in t.itertuples()},
        '相邻年份排名相关系数': {f'{r.year}→{r.next}': round(r.spearman, 3) for r in t.itertuples()},
        '10年累计涨跌': {n: round(v, 2) for n, v in total.sort_values(ascending=False).items()},
        '重点主题排名': {n: {int(y): int(rank.loc[y, n]) for y in YEARS} for n in FOCUS},
        '近12个月': months,
    }
    (ROOT / '分析结果.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
    for k in ['年度上涨主题数', '冠军次年', '冠军次年平均排名', '重点主题排名', '近12个月']:
        print(k, json.dumps(stats[k], ensure_ascii=False))


if __name__ == '__main__':
    main()
