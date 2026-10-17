"""主题指数波段回测图表：持有收益与波段胜率散点、主题×规则类别热力图、代表主题净值对比。"""
from pathlib import Path
import importlib.util
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '图表'


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


g = module('g', '绘图.py')      # 复用配色、字体与收尾样式
bt, tb = g.bt, module('tb', '主题回测.py')
BG, INK, MUTED, GRID, INDIGO, UP, DOWN, CMAP = g.BG, g.INK, g.MUTED, g.GRID, g.INDIGO, g.UP, g.DOWN, g.CMAP
NOTE = '数据：中证指数有限公司、腾讯行情；价格指数不含分红；单边成本0.05%；2016年初至2026年10月16日（部分主题自2017年起）'


# 相邻点标签手动错开
OFFSET = {'生物科技': (-52, 4), '创业板指': (6, -12), '上证指数': (-58, 4), '沪深300': (-58, 4), '上证50': (6, -13),
          '科创50': (-46, 4), '新能源': (6, 3), '卫星产业': (6, 6), '智能汽车': (6, -12)}


def summary():
    th = pd.read_csv(ROOT / '主题回测结果.csv')
    ix = pd.read_csv(ROOT / '回测结果.csv').rename(columns={'指数': '主题'})
    out = []
    for kind, res in (('主题', th), ('宽基', ix)):
        r = res[res.规则类别 != '买入持有']
        h = res[res.规则 == '买入持有'].set_index('主题').年化
        for n in h.index:
            x = r[r.主题 == n]
            out.append({'名称': n, '类型': kind, '持有年化': h[n], '跑赢比例': (x.超额年化 > 0).mean() * 100,
                        **{f: x[x.规则类别 == f].超额年化.median() for f in bt.FAMILIES}})
    return pd.DataFrame(out)


def fig_scatter(s):
    fig, ax = plt.subplots(figsize=(12, 8.4), dpi=130, facecolor=BG)
    g.clean(ax)
    for kind, mk, col in (('主题', 'o', INDIGO), ('宽基', 'D', '#C8813B')):
        d = s[s.类型 == kind]
        ax.scatter(d.持有年化, d.跑赢比例, s=90 if kind == '主题' else 80, marker=mk, color=col, alpha=.85,
                   edgecolor='white', lw=1, zorder=3, label=f'{kind}指数（{len(d)}个）')
        for _, r in d.iterrows():
            ax.annotate(r.名称, (r.持有年化, r.跑赢比例), xytext=OFFSET.get(r.名称, (6, 3)), textcoords='offset points', fontsize=9.5,
                        color=INK if kind == '主题' else '#9A6224')
    k, b = np.polyfit(s.持有年化, s.跑赢比例, 1)
    xs = np.linspace(s.持有年化.min() - .5, s.持有年化.max() + .5, 50)
    ax.plot(xs, k * xs + b, color=MUTED, lw=1.4, ls='--', zorder=1)
    rho = s.持有年化.corr(s.跑赢比例, method='spearman')
    ax.axhline(50, color=MUTED, lw=.8)
    ax.axvline(0, color=MUTED, lw=.8)
    ax.text(.99, .97, f'秩相关 {rho:+.2f}', transform=ax.transAxes, ha='right', va='top', fontsize=11, color=INK, weight='bold')
    ax.text(s.持有年化.min(), 97, '← 持有10年没赚钱：做波段多数跑赢', fontsize=10.5, color=UP, va='top')
    ax.text(s.持有年化.max(), 28, '持有10年涨得多：做波段多数跑输 ↓', fontsize=10.5, color=DOWN, ha='right')
    ax.set_xlabel('买入持有年化收益（%）', fontsize=10.5, color=MUTED)
    ax.set_ylabel('24条波段规则中跑赢持有的比例（%）', fontsize=10.5, color=MUTED)
    ax.set_ylim(-2, 102)
    ax.grid(color=GRID, lw=.6)
    ax.legend(frameon=False, loc='center right', fontsize=10, labelcolor=INK)
    fig.subplots_adjust(top=.86, bottom=.09, left=.08, right=.97)
    g.finish(fig, '越是长牛的板块，做波段越吃亏', '每个点是一个指数：横轴为一直拿着的年化收益，纵轴为24条波段规则里跑赢持有的比例', NOTE)
    fig.savefig(OUT / '图4_持有收益与波段胜率.png', facecolor=BG)
    plt.close(fig)
    return rho


def fig_family(s):
    d = s[s.类型 == '主题'].sort_values('持有年化')
    fams = list(bt.FAMILIES)
    fig = plt.figure(figsize=(12, 13), dpi=130, facecolor=BG)
    ax = fig.add_axes([0.15, 0.05, 0.83, 0.82])
    g.clean(ax)
    norm = TwoSlopeNorm(vmin=-8, vcenter=0, vmax=8)
    cols = fams + ['持有年化', '跑赢比例']
    for i, (_, r) in enumerate(d.iterrows()):
        for j, f in enumerate(fams):
            v = r[f]
            ax.add_patch(plt.Rectangle((j + .04, i + .06), .92, .88, color=CMAP(norm(np.clip(v, -8, 8))), lw=0))
            ax.text(j + .5, i + .52, f'{v:+.1f}', ha='center', va='center', fontsize=10, color='white' if abs(v) > 5 else INK)
        ax.text(4.5, i + .52, f'{r.持有年化:+.1f}%', ha='center', va='center', fontsize=10.5, color=UP if r.持有年化 > 0 else DOWN)
        ax.text(5.5, i + .52, f'{r.跑赢比例:.0f}%', ha='center', va='center', fontsize=10.5, weight='bold',
                color=UP if r.跑赢比例 >= 50 else DOWN)
        ax.text(-.1, i + .52, r.名称, ha='right', va='center', fontsize=11, color=INK)
    for j, c in enumerate(cols):
        ax.text(j + .5, -.45, c if c != '跑赢比例' else '规则跑赢比例', ha='center', fontsize=11, color=INK, weight='bold')
    ax.axvline(4.02, color=GRID, lw=1.2)
    ax.set_xlim(0, len(cols))
    ax.set_ylim(len(d), -1)
    ax.set_xticks([])
    ax.set_yticks([])
    g.finish(fig, '25个板块，四类波段规则各自表现如何？',
             '每格：该类规则相对买入持有的超额年化中位数（百分点），红色跑赢、绿色跑输；按持有年化从低到高排序', NOTE, top=.955)
    fig.savefig(OUT / '图5_主题规则类别热力图.png', facecolor=BG)
    plt.close(fig)


def fig_navs():
    data, _ = tb.load()
    P = g.P
    cases = [('光伏', ['站上30日线', 'RSI<30买 >70卖']), ('医疗器械', ['RSI<20买 >50卖', '站上60日线']),
             ('半导体', ['站上60日线', 'RSI<30买 >70卖']), ('黄金采掘', ['站上60日线', 'RSI<30买 >70卖'])]
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), dpi=130, facecolor=BG)
    for ax, (n, rules) in zip(axes.flat, cases):
        g.clean(ax)
        df = data[n]
        st = tb.LATE.get(n, tb.DEFAULT_START)
        hold, _ = tb.run(df, pd.Series(1, index=df.index), st)
        ax.plot(hold.index, (hold - 1) * 100, color='#B7BCCD', lw=2, label='买入持有')
        ax.text(hold.index[-1], (hold.iloc[-1] - 1) * 100, f' {(hold.iloc[-1] - 1) * 100:+.0f}%', color=MUTED, fontsize=9.5, va='center')
        for rule, col in zip(rules, (INDIGO, '#C8813B')):
            nav, _ = tb.run(df, bt.signal(df, P[rule]), st)
            ax.plot(nav.index, (nav - 1) * 100, color=col, lw=2, label=rule)
            ax.text(nav.index[-1], (nav.iloc[-1] - 1) * 100, f' {(nav.iloc[-1] - 1) * 100:+.0f}%', color=col, fontsize=9.5,
                    va='center', weight='bold')
        ax.axhline(0, color=MUTED, lw=.6, ls='--')
        ax.set_title(n, loc='left', fontsize=14, color=INK, weight='bold')
        ax.legend(frameon=False, fontsize=9, loc='upper left', labelcolor=INK)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:+.0f}%' if v else '0'))
        ax.grid(axis='y', color=GRID, lw=.6)
        ax.tick_params(labelsize=8.5)
    fig.subplots_adjust(top=.86, bottom=.06, left=.07, right=.94, hspace=.32, wspace=.18)
    g.finish(fig, '来回折腾的板块，波段能多赚；一路走牛的板块，波段反而少赚',
             '累计收益：灰线为买入持有，彩色为两条代表规则；收盘出信号、次日收盘成交', NOTE)
    fig.savefig(OUT / '图6_主题净值对比.png', facecolor=BG)
    plt.close(fig)


def main():
    s = summary()
    rho = fig_scatter(s)
    fig_family(s)
    fig_navs()
    out = {'持有年化与跑赢比例秩相关': round(rho, 3),
           '指数汇总': s.round(2).to_dict('records'),
           '说明': '跑赢比例为24条规则中年化超过买入持有的比例；四类规则列为该类规则超额年化中位数（百分点）'}
    (ROOT / '主题分析结果.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('秩相关', round(rho, 2))


if __name__ == '__main__':
    main()
