"""从行情快照复算融资指标，输出公众号配图、明细和验收结果。"""
from pathlib import Path
import json
import math
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '数据'
OUT = ROOT / '图表'
OUT.mkdir(exist_ok=True)
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
plt.rcParams.update({'font.family': 'Microsoft YaHei', 'axes.unicode_minus': False,
                     'font.size': 11, 'axes.titleweight': 'bold', 'svg.fonttype': 'none'})
INK, BLUE, GOLD, GRID, MUTED = '#172F43', '#3B7196', '#C8813B', '#E5EBF0', '#71818E'
CUTOFF = pd.Timestamp('2026-09-30')


def read(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


def frame(name, market):
    df = pd.DataFrame(read(name)['result']['data'])
    df['date'] = pd.to_datetime(df.DIM_DATE).dt.normalize()
    df = df.sort_values('date').reset_index(drop=True)
    assert df.date.is_unique
    cols = ['RZYE', 'RZMRE', 'RZCHE', 'RZJME']
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='raise')
        assert df[col].notna().all() and np.isfinite(df[col]).all()
    assert (df[['RZYE', 'RZMRE', 'RZCHE']] >= 0).all().all()
    error = (df.RZMRE - df.RZCHE - df.RZJME).abs().max()
    # 展示净买入严格由买入额减偿还额计算；第三方预计算字段保留供核对。
    result = df[['date'] + cols].rename(columns={c: c + '_' + market for c in cols})
    return result, float(error)


def style(ax):
    ax.set_facecolor('white')
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color('#BCC8D1')
    ax.tick_params(colors=MUTED, length=0, pad=8)
    ax.grid(axis='y', color=GRID, linewidth=.7)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)


def dates(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))


def draw_balance(ax, df):
    style(ax)
    dates(ax)
    x, y = df.date, df.balance_trillion
    ax.plot(x, y, color=BLUE, linewidth=2.5)
    lo, hi = float(y.min()), float(y.max())
    pad = max((hi - lo) * .28, .035)
    ax.set_ylim(lo - pad * .65, hi + pad)
    ax.set_xlim(x.iloc[0] - pd.Timedelta(days=10), x.iloc[-1] + pd.Timedelta(days=24))
    ax.set_ylabel('融资余额 / 万亿元')
    ax.set_title('01  融资余额：看存量如何变化', loc='left', color=INK, fontsize=15, pad=20)
    for row, label, offset in [(df.iloc[0], '起点', (12, -24)), (df.loc[df.balance_trillion.idxmax()], '窗口高点', (-70, 25)), (df.iloc[-1], '最新', (-95, -30))]:
        ax.scatter([row.date], [row.balance_trillion], s=45, color=GOLD, edgecolor='white', zorder=5)
        ax.annotate(f'{label} {row.balance_trillion:.3f}\n{row.date:%Y-%m-%d}', (row.date, row.balance_trillion), xytext=offset, textcoords='offset points', color=INK, fontsize=10,
                    arrowprops={'arrowstyle': '-', 'color': '#AEBAC3', 'lw': .8})
    ax.text(.99, .02, '纵轴聚焦观察区间', transform=ax.transAxes, ha='right', color=MUTED, fontsize=9)


def draw_net(ax, df):
    style(ax)
    dates(ax)
    values = df.net_buy_yi
    colors = np.where(values >= 0, GOLD, BLUE)
    ax.bar(df.date, values, width=1.8, color=colors, alpha=.75)
    ax.plot(df.date, df.net_buy_yi.rolling(20, min_periods=20).mean(), color=INK, linewidth=1.5, label='20日均值')
    ax.axhline(0, color='#8DA0AE', lw=.8)
    ax.set_xlim(df.date.iloc[0] - pd.Timedelta(days=10), df.date.iloc[-1] + pd.Timedelta(days=24))
    ax.set_ylabel('净买入 / 亿元')
    ax.set_title('02  每日融资净买入：买入额减去偿还额', loc='left', color=INK, fontsize=15, pad=16)
    ax.legend(frameon=False, loc='upper right', fontsize=10)


def scatter(ax, df, response, title, symmetric_x, symmetric_y, label_dates=False):
    style(ax)
    x, y = df.net_buy_yi, df[response]
    ax.grid(axis='both', color=GRID, linewidth=.6)
    # 两张图采用同一组交易日和相同坐标尺度；每个点代表一个交易日。
    for mask, color, marker, label in [(x >= 0, GOLD, 'o', '净买入 ≥ 0'), (x < 0, BLUE, 's', '净买入 < 0')]:
        ax.scatter(x[mask], y[mask], s=30, c=color, marker=marker, alpha=.62, linewidths=.35, edgecolors='white', label=label)
    ax.axhline(0, color='#9AAAB6', lw=1)
    ax.axvline(0, color='#9AAAB6', lw=1)
    ax.set_xlim(-symmetric_x, symmetric_x)
    ax.set_ylim(-symmetric_y, symmetric_y)
    ax.set_xlabel('当日沪深融资净买入 / 亿元', labelpad=12)
    ax.set_ylabel('沪深300涨跌幅 / %', labelpad=8)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:+.0f}'))
    ax.set_title(title, loc='left', color=INK, fontsize=14, pad=22)
    r = float(x.corr(y))
    ax.text(.03, .97, f'Pearson r = {r:+.3f}  |  n = {len(df)}', transform=ax.transAxes, va='top', color=INK, fontsize=11,
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .95, 'pad': 5})
    for xm, ym, xx, yy, ha, va in [(x < 0, y > 0, .02, .89, 'left', 'top'), (x >= 0, y > 0, .98, .89, 'right', 'top'),
                                    (x < 0, y <= 0, .02, .025, 'left', 'bottom'), (x >= 0, y <= 0, .98, .025, 'right', 'bottom')]:
        ax.text(xx, yy, f'{int((xm & ym).sum())}日', transform=ax.transAxes, ha=ha, va=va, color=MUTED, fontsize=10)
    if label_dates:
        row = df.loc[df[response].abs().idxmax()]
        ax.annotate(f'{row.date:%m-%d}', (row.net_buy_yi, row[response]), xytext=(8, -16), textcoords='offset points', fontsize=9, color=INK)


def export(fig, name):
    fig.savefig(OUT / (name + '.png'), dpi=180, facecolor='white')
    fig.savefig(OUT / (name + '.svg'), facecolor='white')
    plt.close(fig)


def main():
    sh, sh_error = frame('沪市融资汇总.json', 'sh')
    sz, sz_error = frame('深市融资汇总.json', 'sz')
    official_sh = pd.DataFrame(read('上交所融资汇总.json')['result'])
    official_sh['date'] = pd.to_datetime(official_sh.opDate, format='%Y%m%d')
    assert official_sh.date.is_unique
    sh['RZCHE_em_sh'] = sh.RZCHE_sh
    sh = sh.merge(official_sh[['date', 'rzche']].rename(columns={'rzche': 'official_repay_sh'}), on='date', how='left', validate='one_to_one')
    sh['RZCHE_sh'] = sh.official_repay_sh.fillna(sh.RZCHE_sh)
    index_raw = read('沪深300日线.json')['data']['sh000300']
    assert 'day' in index_raw
    index = pd.DataFrame(index_raw['day'])
    index = pd.DataFrame({'date': pd.to_datetime(index[0]), 'close': pd.to_numeric(index[2], errors='raise')}).sort_values('date')
    assert index.date.is_unique and (index.close > 0).all()
    index['return_pct'] = index.close.pct_change(fill_method=None) * 100
    index['next_return_pct'] = index.return_pct.shift(-1)
    index['next_date'] = index.date.shift(-1)
    index = index[index.date <= CUTOFF].copy()
    index['next_return_pct'] = index.return_pct.shift(-1)
    index['next_date'] = index.date.shift(-1)
    last_common = min(sh.loc[sh.date <= CUTOFF, 'date'].max(), sz.loc[sz.date <= CUTOFF, 'date'].max(), index.date.max())
    start = CUTOFF - pd.DateOffset(years=1)
    joined = sh.merge(sz, on='date', validate='one_to_one')
    joined['balance_yuan'] = joined.RZYE_sh + joined.RZYE_sz
    joined['buy_yuan'] = joined.RZMRE_sh + joined.RZMRE_sz
    joined['repay_yuan'] = joined.RZCHE_sh + joined.RZCHE_sz
    joined['net_buy_yuan'] = joined.buy_yuan - joined.repay_yuan
    joined['reported_net_buy_yuan'] = joined.RZJME_sh + joined.RZJME_sz
    joined['reported_net_difference_yuan'] = joined.net_buy_yuan - joined.reported_net_buy_yuan
    joined['balance_trillion'] = joined.balance_yuan / 1e12
    joined['net_buy_yi'] = joined.net_buy_yuan / 1e8
    expected_dates = set(index.loc[index.date.between(start, last_common), 'date'])
    missing = sorted(expected_dates - set(joined.date))
    assert not missing, 'missing_market_dates_in_analysis_window'
    df = joined.merge(index, on='date', validate='one_to_one')
    df = df[df.date.between(start, last_common)].reset_index(drop=True)
    assert df.official_repay_sh.notna().all(), 'official_sh_repayment_missing_in_window'
    pairs = df.dropna(subset=['return_pct', 'next_return_pct']).copy()
    assert len(pairs) == len(df) and len(df) >= 200
    assert (pairs.next_date > pairs.date).all()
    df.to_csv(DATA / '融资与指数日度明细.csv', index=False, encoding='utf-8-sig', date_format='%Y-%m-%d')
    csv_records = json.loads(df.to_json(orient='records', date_format='iso'))
    (DATA / '融资与指数日度明细.json').write_text(json.dumps(csv_records, ensure_ascii=False, indent=2), encoding='utf-8')

    # 官方抽样：上交所按元逐项比对；深交所页面以亿元保留两位小数并可能截断。
    official_checks = []
    if (DATA / '上交所融资汇总.json').exists():
        for row in read('上交所融资汇总.json').get('result', []):
            day = pd.to_datetime(row['opDate'], format='%Y%m%d')
            expected = sh[sh.date == day]
            if expected.empty:
                continue
            item = expected.iloc[0]
            errors = {key: abs(float(row[official]) - float(item[field])) for key, official, field in [('balance', 'rzye', 'RZYE_sh'), ('buy', 'rzmre', 'RZMRE_sh'), ('repay', 'rzche', 'RZCHE_sh')]}
            assert max(errors.values()) <= 100
            official_checks.append({'market': '沪市', 'date': str(day.date()), 'absolute_errors_yuan': errors})
    if (DATA / '深交所汇总抽样.json').exists():
        block = read('深交所汇总抽样.json')[0]
        day = pd.to_datetime(block['metadata']['subname'])
        if block['data']:
            row = block['data'][0]
            item = sz.loc[sz.date == day].iloc[0]
            errors = {key: abs(float(row[official].replace(',', '')) * 1e8 - float(item[field])) for key, official, field in [('balance', 'jrrzye', 'RZYE_sz'), ('buy', 'jrrzmr', 'RZMRE_sz')]}
            assert max(errors.values()) <= 1e6
            official_checks.append({'market': '深市', 'date': str(day.date()), 'absolute_errors_yuan': errors, 'official_display_precision_yi': .01})

    quadrants = {}
    for key, response in [('same_day', 'return_pct'), ('next_day', 'next_return_pct')]:
        x, y = pairs.net_buy_yi, pairs[response]
        quadrants[key] = {'net_buy_and_up': int(((x > 0) & (y > 0)).sum()), 'net_buy_and_down': int(((x > 0) & (y < 0)).sum()),
                          'net_repay_and_up': int(((x < 0) & (y > 0)).sum()), 'net_repay_and_down': int(((x < 0) & (y < 0)).sum()),
                          'zero_axis_days': int(((x == 0) | (y == 0)).sum())}
        assert sum(quadrants[key].values()) == len(pairs)
    r_same = float(pairs.net_buy_yi.corr(pairs.return_pct))
    r_next = float(pairs.net_buy_yi.corr(pairs.next_return_pct))
    peak = df.loc[df.balance_yuan.idxmax()]
    min_net, max_net = df.loc[df.net_buy_yuan.idxmin()], df.loc[df.net_buy_yuan.idxmax()]
    summary = {'period': [str(df.date.iloc[0].date()), str(last_common.date())], 'trading_days': len(df),
               'information_cutoff': str(CUTOFF.date()), 'requested_window': [str(start.date()), str(CUTOFF.date())],
               'latest_sh_date': str(sh.loc[sh.date <= CUTOFF, 'date'].max().date()),
               'latest_sz_date': str(sz.loc[sz.date <= CUTOFF, 'date'].max().date()),
               'next_return_last_date': str(pairs.next_date.iloc[-1].date()), 'balance_start_trillion': float(df.balance_trillion.iloc[0]),
               'balance_end_trillion': float(df.balance_trillion.iloc[-1]), 'balance_change_yi': float((df.balance_yuan.iloc[-1] - df.balance_yuan.iloc[0]) / 1e8),
               'balance_change_pct': float((df.balance_yuan.iloc[-1] / df.balance_yuan.iloc[0] - 1) * 100),
               'peak_balance_trillion': float(peak.balance_trillion), 'peak_date': str(peak.date.date()),
               'latest_net_buy_yi': float(df.net_buy_yi.iloc[-1]), 'positive_net_days': int((df.net_buy_yuan > 0).sum()),
               'pearson_same_day': r_same, 'pearson_next_day': r_next,
               'spearman_same_day': float(pairs.net_buy_yi.rank().corr(pairs.return_pct.rank())),
               'spearman_next_day': float(pairs.net_buy_yi.rank().corr(pairs.next_return_pct.rank())),
               'max_net_buy': {'date': str(max_net.date.date()), 'yi': float(max_net.net_buy_yi)},
               'max_net_repay': {'date': str(min_net.date.date()), 'yi': float(min_net.net_buy_yi)},
               'quadrants': quadrants,
               'last_60_same_day_r': float(pairs.tail(60).net_buy_yi.corr(pairs.tail(60).return_pct)),
               'last_60_next_day_r': float(pairs.tail(60).net_buy_yi.corr(pairs.tail(60).next_return_pct)),
               'interpretation': '同期相关描述同一交易日共变；次日结果仅为本窗口样本内观察，未进行样本外预测或显著性检验。'}
    latest_sh = sh.loc[sh.date == CUTOFF].iloc[0]
    latest_index = index.loc[index.date == CUTOFF].iloc[0]
    summary['cutoff_day_sh'] = {'balance_yi': float(latest_sh.RZYE_sh / 1e8), 'buy_yi': float(latest_sh.RZMRE_sh / 1e8),
                              'repay_yi': float(latest_sh.RZCHE_sh / 1e8), 'net_buy_yi': float((latest_sh.RZMRE_sh - latest_sh.RZCHE_sh) / 1e8),
                              'csi300_return_pct': float(latest_index.return_pct), 'csi300_close': float(latest_index.close),
                              'sz_values': None, 'combined_values': None}
    sh_only = official_sh[official_sh.date.between(start, CUTOFF)].sort_values('date').reset_index(drop=True).copy()
    sh_only['balance_trillion'] = sh_only.rzye / 1e12
    sh_only['net_buy_yi'] = (sh_only.rzmre - sh_only.rzche) / 1e8
    summary['sh_only_period'] = [str(sh_only.date.iloc[0].date()), str(sh_only.date.iloc[-1].date())]
    summary['sh_only_trading_days'] = len(sh_only)
    assert sh_only.date.max() == CUTOFF
    sh_only[['date', 'rzye', 'rzmre', 'rzche', 'balance_trillion', 'net_buy_yi']].to_csv(DATA / '沪市截至9月30日日度明细.csv', index=False, encoding='utf-8-sig', date_format='%Y-%m-%d')
    summary['peak_to_latest_change_yi'] = float((df.balance_yuan.iloc[-1] - peak.balance_yuan) / 1e8)
    summary['peak_to_latest_change_pct'] = float((df.balance_yuan.iloc[-1] / peak.balance_yuan - 1) * 100)
    summary['conditional_returns'] = []
    for name, mask in [('净买入日', pairs.net_buy_yi > 0), ('净偿还日', pairs.net_buy_yi < 0), ('全部样本', pairs.net_buy_yi.notna())]:
        subset = pairs[mask]
        summary['conditional_returns'].append({'group': name, 'n': len(subset), 'same_up_n': int((subset.return_pct > 0).sum()),
                  'next_up_n': int((subset.next_return_pct > 0).sum()), 'same_up_pct': float((subset.return_pct > 0).mean() * 100),
                  'next_up_pct': float((subset.next_return_pct > 0).mean() * 100), 'same_mean_pct': float(subset.return_pct.mean()),
                  'next_mean_pct': float(subset.next_return_pct.mean()), 'next_median_pct': float(subset.next_return_pct.median())})
    summary['quarter_correlations'] = []
    for quarter, subset in pairs.groupby(pairs.date.dt.to_period('Q')):
        if len(subset) >= 15:
            summary['quarter_correlations'].append({'quarter': str(quarter), 'n': len(subset), 'same_day_r': float(subset.net_buy_yi.corr(subset.return_pct)),
                                                    'next_day_r': float(subset.net_buy_yi.corr(subset.next_return_pct))})
    pair_bins = pd.qcut(pairs.net_buy_yi, 4, labels=False)
    summary['net_buy_quartiles'] = []
    for number in range(4):
        subset = pairs[pair_bins == number]
        summary['net_buy_quartiles'].append({'quartile': number + 1, 'n': len(subset), 'min_yi': float(subset.net_buy_yi.min()),
                  'max_yi': float(subset.net_buy_yi.max()), 'same_up_pct': float((subset.return_pct > 0).mean() * 100),
                  'next_up_pct': float((subset.next_return_pct > 0).mean() * 100)})
    (ROOT / '分析结果.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    # 独立数值检查：手算均值、协方差复核 Pearson，避免仅用同一函数检查自身。
    def independent_corr(x, y):
        a, b = list(map(float, x)), list(map(float, y))
        aa, bb = sum(a) / len(a), sum(b) / len(b)
        numerator = sum((v - aa) * (w - bb) for v, w in zip(a, b))
        denominator = math.sqrt(sum((v - aa) ** 2 for v in a) * sum((w - bb) ** 2 for w in b))
        return numerator / denominator
    assert abs(independent_corr(pairs.net_buy_yi, pairs.return_pct) - r_same) < 1e-12
    assert abs(independent_corr(pairs.net_buy_yi, pairs.next_return_pct) - r_next) < 1e-12
    report = {'status': 'passed', 'checks': {'unique_dates': True, 'finite_nonnegative_balance_buy_repay': True, 'no_missing_dates_against_index': True,
              'reported_net_field_vs_buy_minus_repay_max_difference_yuan_full_snapshot': {'sh': sh_error, 'sz': sz_error},
              'net_buy_definition': '买入额减偿还额；不采用第三方预计算RZJME字段',
              'reported_net_difference_days_in_window': int((df.reported_net_difference_yuan.abs() > 100).sum()),
              'computed_net_buy_identity': bool((df.net_buy_yuan == df.buy_yuan - df.repay_yuan).all()), 'same_samples_for_paired_scatter': True,
              'next_day_aligned_on_full_index_calendar': True, 'independent_correlations': True, 'official_cross_checks': official_checks},
              'scope': '沪深市场融资标的汇总，含基金，不含京市；沪深300仅作为宽基价格表现参照。'}
    (ROOT / '验收结果.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    symmetric_x = float(pairs.net_buy_yi.abs().max()) * 1.14
    symmetric_y = float(pairs[['return_pct', 'next_return_pct']].abs().max().max()) * 1.17
    period = f'{df.date.iloc[0]:%Y-%m-%d} — {last_common:%Y-%m-%d}  |  {len(df)}个共同交易日'
    fig = plt.figure(figsize=(14, 16), facecolor='white')
    fig.text(.065, .965, '融资交易与市场涨跌', fontsize=28, weight='bold', color=INK)
    fig.text(.065, .937, '信息截止2026-09-30  |  沪深完整样本：' + period, fontsize=11, color=MUTED)
    for xx, label, value, detail in [(.065, '最新完整融资余额', f'{summary["balance_end_trillion"]:.3f} 万亿', '沪市 + 深市，截至09-29'),
                                     (.30, '窗口首尾变化', f'{summary["balance_change_pct"]:+.1f}%', f'{summary["balance_change_yi"]:+,.0f}亿元'),
                                     (.54, '与当日涨跌的相关', f'{r_same:+.3f}', 'Pearson r'),
                                     (.77, '与次日涨跌的相关', f'{r_next:+.3f}', 'Pearson r')]:
        fig.text(xx, .892, label, color=MUTED, fontsize=11)
        fig.text(xx, .860, value, color=INK, fontsize=23, weight='bold')
        fig.text(xx, .840, detail, color=MUTED, fontsize=10)
    gs = fig.add_gridspec(3, 2, left=.09, right=.95, top=.765, bottom=.11, height_ratios=[1.06, .72, 1.25], hspace=.57, wspace=.30)
    fig.text(.065, .813, f'09-30沪市：余额{summary["cutoff_day_sh"]["balance_yi"]:,.2f}亿元，净买入{summary["cutoff_day_sh"]["net_buy_yi"]:+.2f}亿元；深市当日数据待更新。', fontsize=10, color=MUTED)
    draw_balance(fig.add_subplot(gs[0, :]), df)
    draw_net(fig.add_subplot(gs[1, :]), df)
    scatter(fig.add_subplot(gs[2, 0]), pairs, 'return_pct', '03  净买入 × 当日涨跌', symmetric_x, symmetric_y, True)
    scatter(fig.add_subplot(gs[2, 1]), pairs, 'next_return_pct', '04  净买入 × 次日涨跌', symmetric_x, symmetric_y)
    fig.text(.065, .057, '散点：每点一个交易日；橙色圆点为净买入，蓝色方点为净偿还。两图使用同一批日期、相同坐标范围。', color=MUTED, fontsize=10)
    fig.text(.065, .037, '数据：上交所、东方财富、腾讯证券。融资标的含基金；不含京市。同期相关不能说明因果，次日相关不等于预测能力。', color=MUTED, fontsize=9)
    fig.text(.95, .018, '可以叫我才哥', ha='right', color=INK, fontsize=11)
    export(fig, '融资交易总览')

    fig, axes = plt.subplots(2, 1, figsize=(13, 8), gridspec_kw={'height_ratios': [1.65, 1]}, facecolor='white')
    fig.subplots_adjust(left=.10, right=.95, top=.84, bottom=.13, hspace=.50)
    fig.suptitle('沪深市场融资余额与每日净买入', x=.08, ha='left', y=.97, fontsize=23, color=INK, weight='bold')
    fig.text(.08, .91, period, color=MUTED, fontsize=11)
    draw_balance(axes[0], df)
    draw_net(axes[1], df)
    fig.text(.08, .025, '数据：上交所、东方财富。含股票与基金融资标的，不含京市。净买入 = 融资买入额 − 融资偿还额。', fontsize=10, color=MUTED)
    fig.text(.95, .025, '可以叫我才哥', ha='right', fontsize=10, color=INK)
    export(fig, '融资余额与净买入')
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), gridspec_kw={'height_ratios': [1.65, 1]}, facecolor='white')
    fig.subplots_adjust(left=.10, right=.95, top=.84, bottom=.13, hspace=.50)
    fig.suptitle('沪市融资余额与每日净买入', x=.08, ha='left', y=.97, fontsize=23, color=INK, weight='bold')
    fig.text(.08, .91, f'{sh_only.date.iloc[0]:%Y-%m-%d} — {CUTOFF:%Y-%m-%d}  |  {len(sh_only)}个交易日  |  仅沪市', color=MUTED, fontsize=11)
    draw_balance(axes[0], sh_only)
    draw_net(axes[1], sh_only)
    fig.text(.08, .025, '数据：上交所融资融券汇总。包含股票与基金融资标的；此图为沪市单独序列，信息截止2026-09-30。', fontsize=9, color=MUTED)
    fig.text(.95, .025, '可以叫我才哥', ha='right', fontsize=10, color=INK)
    export(fig, '沪市融资余额与净买入')

    fig, axes = plt.subplots(1, 2, figsize=(14, 7), facecolor='white')
    fig.subplots_adjust(left=.075, right=.96, top=.76, bottom=.19, wspace=.25)
    fig.suptitle('融资净买入：与当日、次日涨跌分别有多大关系？', x=.065, ha='left', y=.965, fontsize=22, color=INK, weight='bold')
    fig.text(.065, .89, period + '；每个点代表一个交易日，涨跌参照沪深300。', color=MUTED, fontsize=11)
    scatter(axes[0], pairs, 'return_pct', '当日净买入 × 当日涨跌', symmetric_x, symmetric_y, True)
    scatter(axes[1], pairs, 'next_return_pct', '当日净买入 × 下一交易日涨跌', symmetric_x, symmetric_y)
    fig.text(.065, .065, '橙色圆点：净买入 ≥ 0   /   蓝色方点：净买入 < 0；两图相同样本、相同坐标范围。', color=MUTED, fontsize=10)
    fig.text(.065, .028, '数据：上交所、东方财富、腾讯证券。同期关系不说明因果；次日结果为样本内观察，未进行样本外预测验证。', color=MUTED, fontsize=9)
    fig.text(.96, .028, '可以叫我才哥', ha='right', fontsize=10, color=INK)
    export(fig, '融资净买入与涨跌散点图')
    for response, name, title in [('return_pct', '融资净买入与当日涨跌', '当日融资净买入与沪深300当日涨跌'),
                                 ('next_return_pct', '融资净买入与次日涨跌', '当日融资净买入与沪深300下一交易日涨跌')]:
        fig, ax = plt.subplots(figsize=(9, 7), facecolor='white')
        fig.subplots_adjust(left=.12, right=.94, top=.75, bottom=.19)
        fig.suptitle(title, x=.07, ha='left', y=.96, fontsize=20, color=INK, weight='bold')
        fig.text(.07, .89, period + '；信息截止09-30', color=MUTED, fontsize=10)
        scatter(ax, pairs, response, '每个点代表一个交易日', symmetric_x, symmetric_y)
        fig.text(.07, .062, '橙色圆点为净买入，蓝色方点为净偿还；沪深合计完整样本截至09-29。', color=MUTED, fontsize=9)
        fig.text(.07, .025, '来源：上交所、东方财富、腾讯证券。相关系数描述本窗口历史共变。', color=MUTED, fontsize=8)
        fig.text(.94, .025, '可以叫我才哥', ha='right', color=INK, fontsize=9)
        export(fig, name)
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    fig.subplots_adjust(left=.1, right=.95, top=.77, bottom=.23)
    groups = summary['net_buy_quartiles']
    locations = np.arange(4)
    style(ax)
    same_bars = ax.bar(locations - .17, [g['same_up_pct'] for g in groups], width=.32, color=GOLD, label='当日上涨占比')
    next_bars = ax.bar(locations + .17, [g['next_up_pct'] for g in groups], width=.32, color=BLUE, label='次日上涨占比')
    ax.bar_label(same_bars, labels=[f'{g["same_up_pct"]:.1f}%' for g in groups], padding=4, fontsize=10, color=INK)
    ax.bar_label(next_bars, labels=[f'{g["next_up_pct"]:.1f}%' for g in groups], padding=4, fontsize=10, color=INK)
    ax.set_ylim(0, 100)
    ax.set_ylabel('上涨交易日占比 / %')
    ax.set_xticks(locations, [f'Q{g["quartile"]}  ·  {g["n"]}日\n{g["min_yi"]:+.0f}～{g["max_yi"]:+.0f}亿元' for g in groups])
    ax.axhline(50, color='#AAB7C0', lw=.8, ls='--')
    ax.legend(frameon=False, ncol=2, loc='upper left', bbox_to_anchor=(0, 1.18), fontsize=10)
    fig.suptitle('把净买入按强弱分组，再看上涨占比', x=.07, ha='left', y=.95, color=INK, fontsize=20, weight='bold')
    fig.text(.07, .86, f'{len(pairs)}个样本按净买入金额从低到高分为四组，组别在本窗口内划分。', color=MUTED, fontsize=10)
    fig.text(.07, .08, '分组用于描述历史分布；各柱分母为对应组交易日数。虚线表示50%，不是随机模型或显著性阈值。', fontsize=9, color=MUTED)
    fig.text(.07, .03, '数据：上交所、东方财富、腾讯证券；沪深完整样本截至2026-09-29，信息截止09-30。', fontsize=8, color=MUTED)
    fig.text(.95, .03, '可以叫我才哥', ha='right', color=INK, fontsize=9)
    export(fig, '净买入分组与上涨占比')
    print(json.dumps({'status': 'passed', **summary}, ensure_ascii=True))


if __name__ == '__main__':
    main()
