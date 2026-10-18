"""25个中证主题指数的波段规则回测：与宽基指数相同的四类规则 × 参数网格。

口径：当日收盘产生信号，下一交易日收盘成交（主题指数官网历史数据只有收盘价）；单边成本0.05%；价格指数不含分红。
"""
from pathlib import Path
import importlib.util
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('bt', ROOT / '回测.py')
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)
LATE = {'5G通信': '2017-01-03', '卫星产业': '2017-01-03'}   # 基日2015-12-31，留足一年均线预热
DEFAULT_START, SPLIT, FEE = '2016-01-04', '2021-01-01', 0.0005


def load():
    raw = json.loads((ROOT / '数据' / '主题指数日线.json').read_text(encoding='utf-8'))
    out = {}
    for name, v in raw['series'].items():
        s = pd.Series({d: c for d, c in v['rows']}, dtype=float)
        s.index = pd.to_datetime(s.index)
        s = s.sort_index()
        if (s.index[1] - s.index[0]).days > 7:   # 接口在起始日补的一行
            s = s.iloc[1:]
        out[name] = pd.DataFrame({'close': s})
    return out, raw['cutoff']


run = bt.run   # 与宽基共用同一个回测函数（次日收盘成交）


def main():
    data, cutoff = load()
    rows, annual, vol = [], {}, {}
    for name, df in data.items():
        start = LATE.get(name, DEFAULT_START)
        hold_t = pd.Series(1, index=df.index)
        hnav, _ = run(df, hold_t, start)
        hs = bt.stats(hnav)
        vol[name] = df.close[df.index >= start].pct_change().std() * np.sqrt(244) * 100
        annual[(name, '买入持有')] = bt.yearly(hnav)
        rows.append({'主题': name, '规则类别': '买入持有', '规则': '买入持有', **hs, '年化波动': vol[name]})
        ha, _ = run(df, hold_t, start, SPLIT)
        hb, _ = run(df, hold_t, SPLIT)
        for fam, params in bt.FAMILIES.items():
            for p in params:
                sig = bt.signal(df, p)
                nav, n = run(df, sig, start)
                exp = sig.shift(1).reindex(nav.index).fillna(0).mean()
                s = bt.stats(nav, n, exp)
                a, _ = run(df, sig, start, SPLIT)
                b, _ = run(df, sig, SPLIT)
                rows.append({'主题': name, '规则类别': fam, '规则': bt.label(p), **s, '超额年化': s['年化'] - hs['年化'],
                             '前段超额': bt.stats(a)['年化'] - bt.stats(ha)['年化'],
                             '后段超额': bt.stats(b)['年化'] - bt.stats(hb)['年化'], '年化波动': vol[name]})
                annual[(name, bt.label(p))] = bt.yearly(nav)
    res = pd.DataFrame(rows)
    res.to_csv(ROOT / '主题回测结果.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(annual).to_csv(ROOT / '主题逐年收益.csv', encoding='utf-8-sig')
    r = res[res.规则类别 != '买入持有']
    pd.set_option('display.width', 240, 'display.max_rows', 200)
    print('截止', cutoff)
    t = res[res.规则 == '买入持有'].set_index('主题')[['年化', '最大回撤', '年化波动']]
    t['跑赢比例'] = r.groupby('主题').超额年化.apply(lambda x: (x > 0).mean() * 100)
    t['趋势超额中位'] = r[r.规则类别.isin(['单均线', '双均线', '突破'])].groupby('主题').超额年化.median()
    t['低吸超额中位'] = r[r.规则类别 == 'RSI低吸'].groupby('主题').超额年化.median()
    t['最佳规则'] = r.loc[r.groupby('主题').超额年化.idxmax()].set_index('主题').规则
    t['最佳超额'] = r.groupby('主题').超额年化.max()
    print(t.sort_values('跑赢比例', ascending=False).round(1).to_string())
    print('波动率与跑赢比例相关', round(t.年化波动.corr(t.跑赢比例, method='spearman'), 2),
          '| 与持有年化相关', round(t.年化.corr(t.跑赢比例, method='spearman'), 2))
    print('各类规则：主题中位数超额>0 的个数', r.groupby(['规则类别', '主题']).超额年化.median().gt(0).groupby('规则类别').sum().to_dict())
    rho = r.groupby('主题').apply(lambda g: g.前段超额.corr(g.后段超额, method='spearman'))
    print('前后段排名相关 中位数', round(rho.median(), 2), '范围', round(rho.min(), 2), round(rho.max(), 2))
    sel = r.loc[r.groupby('主题').前段超额.idxmax()]
    print('前段冠军→后段仍>0 的比例', round((sel.后段超额 > 0).mean() * 100, 1), '% ；后段超额中位', round(sel.后段超额.median(), 1))


if __name__ == '__main__':
    main()
