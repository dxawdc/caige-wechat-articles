"""A股主要指数的波段规则回测：单均线、双均线、突破、RSI低吸四类规则 × 参数网格，与买入持有对比。

口径：当日收盘产生信号，下一交易日收盘成交（与主题指数一致，只用收盘价）；每次买入或卖出按单边费率扣除成本；空仓不计利息；价格指数不含分红。
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
START = {'科创50': '2021-01-04'}   # 其余指数统一从2016年开始评估
DEFAULT_START = '2016-01-04'
SPLIT = '2021-01-01'               # 前段挑参数、后段检验
FEE = 0.0005                       # 单边成本（佣金+滑点）

FAMILIES = {
    '单均线': [('MA', n) for n in (10, 20, 30, 60, 90, 120, 250)],
    '双均线': [('MA2', s, l) for s, l in ((5, 20), (10, 30), (10, 60), (20, 60), (20, 120), (30, 120), (60, 250))],
    '突破': [('BRK', n, m) for n, m in ((20, 10), (55, 20), (60, 30), (120, 60), (250, 120))],
    'RSI低吸': [('RSI', a, b) for a, b in ((20, 50), (25, 55), (30, 60), (30, 70), (35, 65))],
}


def label(p):
    return {'MA': lambda: f'站上{p[1]}日线', 'MA2': lambda: f'{p[1]}/{p[2]}日金叉',
            'BRK': lambda: f'{p[1]}日新高/{p[2]}日新低', 'RSI': lambda: f'RSI<{p[1]}买 >{p[2]}卖'}[p[0]]()


def load():
    raw = json.loads((ROOT / '数据' / '指数日线.json').read_text(encoding='utf-8'))
    out = {}
    for name, v in raw['series'].items():
        df = pd.DataFrame(v['rows'], columns=['date', 'open', 'close'])
        df['date'] = pd.to_datetime(df.date)
        out[name] = df.set_index('date')
    return out, raw['cutoff']


def rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def signal(df, p):
    """返回每日收盘后的目标仓位（0/1），按状态机生成。"""
    c = df.close
    if p[0] == 'MA':
        return (c > c.rolling(p[1]).mean()).astype(int)
    if p[0] == 'MA2':
        return (c.rolling(p[1]).mean() > c.rolling(p[2]).mean()).astype(int)
    if p[0] == 'BRK':
        hi = c.rolling(p[1]).max().shift(1)
        lo = c.rolling(p[2]).min().shift(1)
        enter, leave = (c >= hi).values, (c <= lo).values
    else:
        r = rsi(c)
        enter, leave = (r < p[1]).values, (r > p[2]).values
    pos, out = 0, np.zeros(len(c), dtype=int)
    for i in range(len(c)):
        if pos == 0 and enter[i]:
            pos = 1
        elif pos == 1 and leave[i]:
            pos = 0
        out[i] = pos
    return pd.Series(out, index=c.index)


def run(df, target, start, end=None, fee=FEE):
    """target[t]为t日收盘后的目标仓位，t+1日收盘成交，t+2日起承担涨跌。返回日净值序列与交易次数。"""
    held = target.reindex(df.index).shift(1).fillna(0)          # t+1日收盘后实际持仓
    ret = df.close.pct_change().fillna(0)
    sel = (df.index >= start) & ((df.index < end) if end else True)
    h, prev, r = held[sel].values, held.shift(1).fillna(0)[sel].values, ret[sel].values
    nav, v, trades = np.empty(len(h)), 1.0, 0
    for i in range(len(h)):
        p_prev = 0 if i == 0 else prev[i]   # 区间起点视为空仓
        if p_prev == 1:
            v *= 1 + r[i]                   # 昨日收盘的持仓承担今日涨跌
        if h[i] != p_prev:
            v *= 1 - fee
            trades += 1
        nav[i] = v
    return pd.Series(nav, index=held[sel].index), trades


def stats(nav, trades=None, exposure=None):
    yrs = (nav.index[-1] - nav.index[0]).days / 365.25
    cagr = nav.iloc[-1] ** (1 / yrs) - 1
    dd = (nav / nav.cummax() - 1).min()
    out = {'年化': cagr * 100, '最大回撤': dd * 100, '卡玛': cagr / -dd if dd < 0 else np.nan, '累计': (nav.iloc[-1] - 1) * 100}
    if trades is not None:
        out['交易次数'] = trades
        out['持仓占比'] = exposure * 100
    return out


def yearly(nav):
    ye = nav.groupby(nav.index.year).last()
    first = nav.iloc[0]
    prev = ye.shift(1)
    prev.iloc[0] = first
    return (ye / prev - 1) * 100


def main():
    data, cutoff = load()
    rows, annual = [], {}
    for name, df in data.items():
        start = START.get(name, DEFAULT_START)
        hold = pd.Series(1, index=df.index)
        hnav, _ = run(df, hold, start)
        hs = stats(hnav)
        annual[(name, '买入持有')] = yearly(hnav)
        rows.append({'指数': name, '规则类别': '买入持有', '规则': '买入持有', **hs})
        for fam, params in FAMILIES.items():
            for p in params:
                sig = signal(df, p)
                nav, n = run(df, sig, start)
                exp = sig.shift(1).reindex(nav.index).fillna(0).mean()
                s = stats(nav, n, exp)
                # 前后两段：前段挑参数，后段检验
                a, _ = run(df, sig, start, SPLIT)
                b, _ = run(df, sig, SPLIT)
                ha, _ = run(df, hold, start, SPLIT)
                hb, _ = run(df, hold, SPLIT)
                rows.append({'指数': name, '规则类别': fam, '规则': label(p), **s, '超额年化': s['年化'] - hs['年化'],
                             '前段超额': stats(a)['年化'] - stats(ha)['年化'] if name != '科创50' else np.nan,
                             '后段超额': stats(b)['年化'] - stats(hb)['年化']})
                annual[(name, label(p))] = yearly(nav)
    res = pd.DataFrame(rows)
    res.to_csv(ROOT / '回测结果.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(annual).to_csv(ROOT / '逐年收益.csv', encoding='utf-8-sig')
    pd.set_option('display.width', 220, 'display.max_rows', 400)
    print('截止', cutoff)
    print(res[res.规则 == '买入持有'][['指数', '年化', '最大回撤', '卡玛']].round(1).to_string(index=False))
    best = res[res.规则类别 != '买入持有'].sort_values('超额年化', ascending=False).groupby('指数').head(3)
    print(best[['指数', '规则', '年化', '最大回撤', '卡玛', '交易次数', '持仓占比', '超额年化', '前段超额', '后段超额']].round(1).to_string(index=False))
    fam = res[res.规则类别 != '买入持有'].groupby(['规则类别', '指数']).超额年化.median().unstack().round(1)
    print('各类规则超额年化中位数\n', fam.to_string())
    win = res[res.规则类别 != '买入持有'].assign(赢=lambda x: x.超额年化 > 0).groupby('指数').赢.mean().round(2)
    print('跑赢持有的规则比例\n', win.to_string())


if __name__ == '__main__':
    main()
