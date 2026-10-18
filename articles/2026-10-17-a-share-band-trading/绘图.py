"""A股指数波段回测图表：持有基准、规则×指数超额热力图、净值对比、前后段检验、逐年超额、成本敏感性。"""
from pathlib import Path
import importlib.util
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '图表'
OUT.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location('bt', ROOT / '回测.py')
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyhbd.ttc')
plt.rcParams.update({'font.family': 'Microsoft YaHei', 'axes.unicode_minus': False})

# 视觉轮换方案（2026-10-11起）：白底、靛蓝/珊瑚/紫色；红绿只表示涨跌或跑赢跑输
BG, INK, MUTED, GRID, INDIGO = '#FAFAFE', '#202B54', '#6B7290', '#E4E6F1', '#4457C4'
UP, DOWN = '#D63A2F', '#13895E'
CMAP = LinearSegmentedColormap.from_list('cn', [DOWN, '#8FD0B1', '#ECEEF4', '#F1A096', UP])
BRAND = '可以叫我才哥'
ORDER = ['上证50', '沪深300', '上证指数', '中证500', '中证1000', '创业板指', '科创50']
LINE = {'上证50': INK, '沪深300': '#4457C4', '上证指数': '#8C93AE', '中证500': '#2B8DB0',
        '中证1000': '#C8813B', '创业板指': '#9471BE', '科创50': '#C2649A'}
P = {bt.label(p): p for ps in bt.FAMILIES.values() for p in ps}


def finish(fig, title, sub, note, top=0.95):
    fig.text(0.04, top, title, color=INK, fontsize=20, weight='bold')
    fig.text(0.04, top - 0.035, sub, color=MUTED, fontsize=11)
    fig.text(0.04, 0.015, note, color=MUTED, fontsize=8.5)
    fig.text(0.96, 0.015, BRAND, color=MUTED, fontsize=9, ha='right', weight='bold')


def clean(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, colors=MUTED)


NOTE = '数据：腾讯行情；价格指数不含分红；收盘出信号、次日收盘成交，单边成本0.05%；科创50自2021年起'


def fig_hold(data, cutoff):
    fig, ax = plt.subplots(figsize=(12, 6.8), dpi=130, facecolor=BG)
    clean(ax)
    last = {}
    for n in ORDER:
        df = data[n]
        st = bt.START.get(n, bt.DEFAULT_START)
        nav, _ = bt.run(df, pd.Series(1, index=df.index), st)
        v = (nav - 1) * 100
        ax.plot(v.index, v.values, color=LINE[n], lw=2.6 if n in ('沪深300', '中证1000', '科创50') else 1.8)
        last[n] = v.iloc[-1]
    pos = []
    for n, v in sorted(last.items(), key=lambda kv: kv[1]):
        y = max(v, pos[-1][1] + 6.5) if pos else v
        pos.append((n, y))
    for n, y in pos:
        ax.text(pd.Timestamp(cutoff) + pd.Timedelta(days=40), y, f'{n} {last[n]:+.1f}%', color=LINE[n], fontsize=11,
                weight='bold', va='center')
    ax.axhline(0, color=MUTED, lw=.8, ls='--')
    ax.set_xlim(pd.Timestamp('2016-01-01'), pd.Timestamp('2028-10-01'))
    ax.set_xticks([pd.Timestamp(y, 1, 1) for y in range(2016, 2027, 2)])
    ax.set_xticklabels([str(y) for y in range(2016, 2027, 2)])
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:+.0f}%' if v else '0'))
    ax.grid(axis='y', color=GRID, lw=.7)
    fig.subplots_adjust(top=.84, bottom=.08, left=.07, right=.98)
    finish(fig, '一直拿着：10年下来，多数指数原地踏步', '买入持有的累计涨跌（2016年初起，科创50自2021年初起）', NOTE)
    fig.savefig(OUT / '图1_持有10年.png', facecolor=BG)
    plt.close(fig)
    return last


def fig_heat(res):
    r = res[res.规则类别 != '买入持有']
    rules = [bt.label(p) for ps in bt.FAMILIES.values() for p in ps]
    mat = r.pivot(index='规则', columns='指数', values='超额年化').loc[rules, ORDER]
    hold = res[res.规则 == '买入持有'].set_index('指数').年化.loc[ORDER]
    fig = plt.figure(figsize=(12, 15), dpi=130, facecolor=BG)
    ax = fig.add_axes([0.2, 0.04, 0.78, 0.855])
    clean(ax)
    norm = TwoSlopeNorm(vmin=-10, vcenter=0, vmax=10)
    y = 0
    ypos = {}
    for fam, ps in bt.FAMILIES.items():
        ax.text(-.12, y + .55, fam, transform=ax.get_yaxis_transform(), ha='right', fontsize=12.5, color=INDIGO, weight='bold')
        y += .9
        for p in ps:
            ypos[bt.label(p)] = y
            y += 1
        y += .3
    for rule, yy in ypos.items():
        for j, n in enumerate(ORDER):
            v = mat.loc[rule, n]
            ax.add_patch(plt.Rectangle((j + .04, yy + .05), .92, .9, color=CMAP(norm(np.clip(v, -10, 10))), lw=0))
            ax.text(j + .5, yy + .52, f'{v:+.1f}', ha='center', va='center', fontsize=10, color='white' if abs(v) > 6 else INK)
        ax.text(-.02, yy + .52, rule, transform=ax.get_yaxis_transform(), ha='right', va='center', fontsize=10.5, color=INK)
    win = (mat > 0).mean()
    for j, n in enumerate(ORDER):
        ax.text(j + .5, -1.25, n, ha='center', fontsize=11.5, color=INK, weight='bold')
        ax.text(j + .5, -.45, f'持有 {hold[n]:+.1f}%', ha='center', fontsize=9, color=MUTED)
        ax.text(j + .5, y + .5, f'{win[n] * 100:.0f}%', ha='center', fontsize=12, weight='bold',
                color=UP if win[n] >= .5 else DOWN)
    ax.text(-.02, y + .5, '跑赢持有的规则占比', transform=ax.get_yaxis_transform(), ha='right', fontsize=10.5, color=INK, weight='bold')
    ax.set_xlim(0, len(ORDER))
    ax.set_ylim(y + 1.2, -1.8)
    ax.set_xticks([])
    ax.set_yticks([])
    finish(fig, '同一条波段规则，换个指数结果完全不同',
           '每格：规则年化收益 − 买入持有年化（百分点），红色跑赢、绿色跑输；2016年初至2026年10月16日', NOTE, top=.955)
    fig.savefig(OUT / '图2_规则指数热力图.png', facecolor=BG)
    plt.close(fig)
    return mat, win


def fig_navs(data):
    cases = [('科创50', ['站上20日线', '站上60日线']), ('中证1000', ['RSI<25买 >55卖', '站上60日线']),
             ('创业板指', ['站上250日线', 'RSI<30买 >70卖']), ('沪深300', ['站上20日线', 'RSI<30买 >70卖'])]
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), dpi=130, facecolor=BG)
    for ax, (n, rules) in zip(axes.flat, cases):
        clean(ax)
        df = data[n]
        st = bt.START.get(n, bt.DEFAULT_START)
        hold, _ = bt.run(df, pd.Series(1, index=df.index), st)
        ax.plot(hold.index, (hold - 1) * 100, color='#B7BCCD', lw=2, label='买入持有')
        for rule, col in zip(rules, (INDIGO, '#C8813B')):
            nav, _ = bt.run(df, bt.signal(df, P[rule]), st)
            ax.plot(nav.index, (nav - 1) * 100, color=col, lw=2, label=rule)
            ax.text(nav.index[-1], (nav.iloc[-1] - 1) * 100, f' {(nav.iloc[-1] - 1) * 100:+.0f}%', color=col, fontsize=9.5,
                    va='center', weight='bold')
        ax.text(hold.index[-1], (hold.iloc[-1] - 1) * 100, f' {(hold.iloc[-1] - 1) * 100:+.0f}%', color=MUTED, fontsize=9.5,
                va='center')
        ax.axhline(0, color=MUTED, lw=.6, ls='--')
        ax.set_title(n, loc='left', fontsize=14, color=INK, weight='bold')
        ax.legend(frameon=False, fontsize=9, loc='upper left', labelcolor=INK)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:+.0f}%' if v else '0'))
        ax.grid(axis='y', color=GRID, lw=.6)
        ax.tick_params(labelsize=8.5)
    fig.subplots_adjust(top=.86, bottom=.06, left=.07, right=.94, hspace=.32, wspace=.18)
    finish(fig, '有的指数越做越好，有的越做越亏', '累计收益：灰线为买入持有，彩色为两条代表规则', NOTE)
    fig.savefig(OUT / '图3_净值对比.png', facecolor=BG)
    plt.close(fig)


def fig_oos(res):
    r = res[(res.规则类别 != '买入持有') & (res.指数 != '科创50')]
    names = [n for n in ORDER if n != '科创50']
    fig, axes = plt.subplots(2, 3, figsize=(12, 8.6), dpi=130, facecolor=BG, sharex=True, sharey=True)
    for ax, n in zip(axes.flat, names):
        clean(ax)
        g = r[r.指数 == n]
        best = g.loc[g.前段超额.idxmax()]
        ax.scatter(g.前段超额, g.后段超额, s=36, color='#B7BCCD', zorder=2)
        ax.scatter(best.前段超额, best.后段超额, s=110, color=UP if best.后段超额 > 0 else DOWN, zorder=3, edgecolor='white')
        right = best.前段超额 > 4   # 靠右的点把标注放到左侧，避免被裁掉
        ax.annotate(f'前段冠军\n{best.规则}\n后段 {best.后段超额:+.1f}', (best.前段超额, best.后段超额),
                    xytext=(-8 if right else 8, -6), textcoords='offset points', fontsize=8.5, color=INK, va='top',
                    ha='right' if right else 'left')
        ax.axhline(0, color=MUTED, lw=.7)
        ax.axvline(0, color=MUTED, lw=.7)
        rho = g.前段超额.corr(g.后段超额, method='spearman')
        ax.set_title(f'{n}', loc='left', fontsize=13, color=INK, weight='bold')
        ax.text(1, 1.02, f'排名相关 {rho:+.2f}', transform=ax.transAxes, ha='right', fontsize=9.5, color=MUTED)
        ax.grid(color=GRID, lw=.5)
        ax.tick_params(labelsize=8.5)
    for ax in axes[1]:
        ax.set_xlabel('2016—2020年 超额年化（百分点）', fontsize=9.5, color=MUTED)
    for ax in axes[:, 0]:
        ax.set_ylabel('2021年至今 超额年化', fontsize=9.5, color=MUTED)
    fig.subplots_adjust(top=.85, bottom=.09, left=.07, right=.98, hspace=.34, wspace=.1)
    finish(fig, '前5年的最优参数，后5年还灵吗？',
           '每个点是一条规则：横轴为2016—2020年超额，纵轴为2021年至今超额；彩色点为前段表现最好的规则', NOTE)
    fig.savefig(OUT / '图8_前后段检验.png', facecolor=BG)
    plt.close(fig)
    return {n: round(r[r.指数 == n].前段超额.corr(r[r.指数 == n].后段超额, method='spearman'), 2) for n in names}


def fig_yearly(data, rule, path, title):
    years = list(range(2016, 2027))
    mat = pd.DataFrame(index=ORDER, columns=years, dtype=float)
    for n in ORDER:
        df = data[n]
        st = bt.START.get(n, bt.DEFAULT_START)
        h = bt.yearly(bt.run(df, pd.Series(1, index=df.index), st)[0])
        s = bt.yearly(bt.run(df, bt.signal(df, P[rule]), st)[0])
        mat.loc[n, (s - h).index] = (s - h).values
    fig = plt.figure(figsize=(12, 6.2), dpi=130, facecolor=BG)
    ax = fig.add_axes([0.11, 0.1, 0.87, 0.66])
    clean(ax)
    norm = TwoSlopeNorm(vmin=-25, vcenter=0, vmax=25)
    for i, n in enumerate(ORDER):
        for j, yv in enumerate(years):
            v = mat.loc[n, yv]
            if np.isnan(v):
                continue
            ax.add_patch(plt.Rectangle((j + .04, i + .06), .92, .88, color=CMAP(norm(np.clip(v, -25, 25))), lw=0))
            ax.text(j + .5, i + .52, f'{v:+.1f}', ha='center', va='center', fontsize=9.5, color='white' if abs(v) > 15 else INK)
    ax.set_xlim(0, len(years))
    ax.set_ylim(len(ORDER), 0)
    ax.set_yticks(np.arange(len(ORDER)) + .5)
    ax.set_yticklabels(ORDER, fontsize=11, color=INK)
    ax.set_xticks(np.arange(len(years)) + .5)
    ax.set_xticklabels([str(y) if y < 2026 else '2026*' for y in years], fontsize=10, color=INK)
    ax.xaxis.tick_top()
    finish(fig, title, f'规则"{rule}"每年收益 − 买入持有当年收益（百分点），红色跑赢、绿色跑输',
           NOTE + '；*2026年截至10月16日', top=.94)
    fig.savefig(path, facecolor=BG)
    plt.close(fig)
    return mat


def fig_cost(data, res):
    picks = [('科创50', '站上20日线'), ('创业板指', '10/30日金叉'), ('中证500', '10/30日金叉'), ('创业板指', '站上250日线'),
             ('中证1000', 'RSI<25买 >55卖'), ('上证指数', 'RSI<25买 >55卖')]
    fees = [0, .0005, .001, .002]
    fig, ax = plt.subplots(figsize=(12, 6.6), dpi=130, facecolor=BG)
    clean(ax)
    out = {}
    for i, (n, rule) in enumerate(picks):
        df = data[n]
        st = bt.START.get(n, bt.DEFAULT_START)
        hold = bt.stats(bt.run(df, pd.Series(1, index=df.index), st)[0])['年化']
        sig = bt.signal(df, P[rule])
        vals, trades = [], 0
        for f in fees:
            nav, trades = bt.run(df, sig, st, fee=f)
            vals.append(bt.stats(nav)['年化'] - hold)
        out[f'{n} {rule}'] = [round(v, 2) for v in vals]
        for k, (f, v) in enumerate(zip(fees, vals)):
            ax.barh(i + (k - 1.5) * .2, v, height=.18, color=[ '#C9CDDC', '#9AA3C7', INDIGO, INK][k])
        ax.text(vals[0] + .3, i - .35, f'{vals[0]:+.1f}', fontsize=9, color=MUTED, va='center')
        ax.text(vals[-1] + .3, i + .35, f'{vals[-1]:+.1f}', fontsize=9.5, color=INK, va='center', weight='bold')
        ax.text(-.4, i, f'{n} · {rule}\n10年交易 {trades} 次', ha='right', va='center', fontsize=10, color=INK)
    handles = [matplotlib.patches.Patch(color=c, label=f'单边成本 {f * 100:.2f}%')
               for c, f in zip(['#C9CDDC', '#9AA3C7', INDIGO, INK], fees)]
    ax.legend(handles=handles, frameon=False, fontsize=9.5, loc='lower right', labelcolor=INK)
    ax.set_ylim(len(picks) - .4, -.6)
    ax.set_xlim(0, 17)
    ax.set_yticks([])
    ax.axvline(0, color=MUTED, lw=.8)
    ax.grid(axis='x', color=GRID, lw=.6)
    fig.subplots_adjust(top=.84, bottom=.07, left=.25, right=.98)
    finish(fig, '交易越频繁，成本吃掉的越多', '不同单边成本下的超额年化（百分点）', NOTE)
    fig.savefig(OUT / '图9_成本敏感性.png', facecolor=BG)
    plt.close(fig)
    return out


def main():
    data, cutoff = bt.load()
    res = pd.read_csv(ROOT / '回测结果.csv')
    hold = fig_hold(data, cutoff)
    mat, win = fig_heat(res)
    fig_navs(data)
    rho = fig_oos(res)
    y1 = fig_yearly(data, '站上60日线', OUT / '图7_逐年超额_均线.png', '均线波段：熊市年份护盘，牛市年份掉队')
    y2 = fig_yearly(data, 'RSI<30买 >70卖', OUT / '图7_逐年超额_低吸.png', '超跌低吸：同样是熊市年份赢，牛市年份输')
    cost = fig_cost(data, res)
    r = res[res.规则类别 != '买入持有']
    stats = {
        '截止日': cutoff, '单边成本': bt.FEE, '持有累计涨跌': {k: round(v, 2) for k, v in hold.items()},
        '持有年化': res[res.规则 == '买入持有'].set_index('指数').年化.round(2).to_dict(),
        '跑赢持有的规则占比': {k: round(v * 100, 1) for k, v in win.items()},
        '各类规则超额中位数': r.groupby(['规则类别', '指数']).超额年化.median().unstack().round(2).to_dict(),
        '前后段排名相关': rho,
        '前段冠军后段表现': r[r.指数 != '科创50'].sort_values('前段超额', ascending=False).groupby('指数').head(1)
            [['指数', '规则', '前段超额', '后段超额']].round(2).to_dict('records'),
        '逐年超额_站上60日线': {n: {int(k): (None if np.isnan(v) else round(v, 2)) for k, v in row.items()} for n, row in y1.iterrows()},
        '逐年超额_RSI30_70': {n: {int(k): (None if np.isnan(v) else round(v, 2)) for k, v in row.items()} for n, row in y2.iterrows()},
        '成本敏感性_超额年化_0_005_01_02': cost,
    }
    (ROOT / '分析结果.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2, default=float), encoding='utf-8')
    print(json.dumps({k: stats[k] for k in ['持有年化', '跑赢持有的规则占比', '前后段排名相关', '逐年超额_站上60日线']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
