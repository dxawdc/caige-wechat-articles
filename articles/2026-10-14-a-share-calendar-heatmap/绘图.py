"""大A近期下跌与近10年对比：日历热力图、跌幅排行、海内外走势、年度涨跌矩阵及动图。"""
from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '图表'
OUT.mkdir(exist_ok=True)
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyhbd.ttc')
plt.rcParams.update({'font.family': 'Microsoft YaHei', 'axes.unicode_minus': False})

# 视觉轮换方案（2026-10-11起）：明亮白底、靛蓝/珊瑚/紫色、稀疏网格
BG, INK, MUTED, GRID = '#FAFAFE', '#202B54', '#6B7290', '#E4E6F1'
UP, DOWN = '#D63A2F', '#13895E'  # 涨跌只用红绿，类别不用红绿
CAT = {'上证指数': INK, '创业板指': '#9471BE', '科创50': '#4457C4', 'KOSPI': '#C8813B',
       '纳斯达克': '#2B8DB0', '标普500': '#7FA6D6', '沪深300': '#8C93AE'}
CMAP = LinearSegmentedColormap.from_list('cn', [DOWN, '#8FD0B1', '#ECEEF4', '#F1A096', UP])
NORM = TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3)
BRAND = '可以叫我才哥'
BASE = pd.Timestamp('2026-06-30')  # 近期对比以6月末收盘为起点
Y0 = 2017  # 长周期部分：2017年1月至今
START = pd.Timestamp('2016-12-31')  # 长周期累计以2016年末收盘为基准


def load():
    raw = json.loads((ROOT / '数据' / '指数日线.json').read_text(encoding='utf-8'))
    series, cutoff = {}, {}
    for name, v in raw.items():
        s = pd.Series({d: c for d, c in v['rows']}, dtype=float)
        s.index = pd.to_datetime(s.index)
        assert s.index.is_unique and (s > 0).all()
        series[name], cutoff[name] = s.sort_index(), pd.Timestamp(v['cutoff'])
    return series, cutoff


def at(s, day):
    return s[s.index <= day].iloc[-1]


def finish(fig, title, sub, note, top=0.94):
    fig.text(0.05, top, title, color=INK, fontsize=20, weight='bold')
    fig.text(0.05, top - 0.045, sub, color=MUTED, fontsize=11)
    fig.text(0.05, 0.025, note, color=MUTED, fontsize=8.5)
    fig.text(0.95, 0.025, BRAND, color=MUTED, fontsize=9, ha='right', weight='bold')


def clean(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, colors=MUTED)


def save(fig, name):
    fig.savefig(OUT / name, facecolor=BG)
    plt.close(fig)


def colorbar(fig, rect):
    cax = fig.add_axes(rect)
    cax.imshow(np.linspace(-3, 3, 256)[None, :], aspect='auto', cmap=CMAP, norm=NORM, extent=[-3, 3, 0, 1])
    cax.set_yticks([])
    cax.set_xticks([-3, 0, 3])
    cax.set_xticklabels(['跌≥3%', '0', '涨≥3%'], fontsize=8.5)
    clean(cax)


def write_gif(frames, path, ms, hold=3000, colors=96):
    pal = frames[-1].quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=[ms] * (len(q) - 1) + [hold], loop=0, optimize=True)


def to_image(fig, scale=1.0):
    fig.canvas.draw()
    img = Image.frombuffer('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert('RGB')
    plt.close(fig)
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    return img


# ---------- 图1 三张日历 ----------
def fig_calendars(S, end):
    rows = ['上证指数', '创业板指', '科创50']
    start = pd.Timestamp('2026-06-29')  # 周一，对齐周格
    fig = plt.figure(figsize=(12, 9.4), dpi=150, facecolor=BG)
    for k, name in enumerate(rows):
        s = S[name]
        pct = (s.pct_change() * 100)[(s.index > BASE) & (s.index <= end)]
        top = 0.63 - k * 0.255
        ax = fig.add_axes([0.05, top, 0.62, 0.19])
        clean(ax)
        for dt, v in pct.items():
            w = (dt - start).days // 7
            ax.add_patch(plt.Rectangle((w + .07, dt.dayofweek + .07), .86, .86,
                                       color=CMAP(NORM(np.clip(v, -3, 3))), lw=0))
        ax.set_xlim(0, (end - start).days // 7 + 1)
        ax.set_ylim(5, 0)
        ax.set_aspect('equal')
        ax.axis('off')
        for m in [7, 8, 9, 10]:
            ax.text((pd.Timestamp(2026, m, 1) - start).days // 7 + .1, -.35, f'{m}月', color=MUTED, fontsize=9)
        r = s[end] / s[BASE] - 1
        fig.text(0.71, top + 0.145, name, color=INK, fontsize=15, weight='bold')
        fig.text(0.71, top + 0.065, f'{r * 100:+.1f}%', color=DOWN if r < 0 else UP, fontsize=30, weight='bold')
        fig.text(0.71, top + 0.02, f'下跌 {(pct < 0).sum()} 天 · 跌超3% 有 {(pct <= -3).sum()} 天',
                 color=MUTED, fontsize=10.5)
    colorbar(fig, [0.05, 0.085, 0.25, 0.014])
    finish(fig, '同一个夏天，三张日历', f'2026年7月1日至{end.month}月{end.day}日，每格一个交易日，一列一周',
           '数据：腾讯行情；涨跌幅以2026年6月30日收盘为基准')
    save(fig, '图1_三张日历.png')


# ---------- 图2 A股各指数跌幅 ----------
def fig_cn_rank(S, end):
    names = ['上证50', '上证指数', '沪深300', '国证2000', '中证1000', '中证500', '深证成指', '创业板指', '科创50']
    ret = pd.Series({n: (S[n][end] / S[n][BASE] - 1) * 100 for n in names}).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, 7.4), dpi=150, facecolor=BG)
    clean(ax)
    for i, (n, v) in enumerate(ret.items()):
        hl = n == '上证指数'
        ax.barh(i, v, height=.62, color='#B7BCCD' if hl else DOWN, alpha=1 if hl else .45 + .55 * min(1, -v / 38))
        ax.text(v - .8, i, f'{v:.1f}%', va='center', ha='right', color=INK, fontsize=12, weight='bold')
        ax.text(.8, i, n, va='center', color=INK, fontsize=12, weight='bold' if hl else 'normal')
    ax.set_ylim(len(ret) - .4, -.6)
    ax.set_xlim(-44, 12)
    ax.axvline(0, color=MUTED, lw=.8)
    ax.axis('off')
    fig.subplots_adjust(top=.84, bottom=.08, left=.03, right=.97)
    finish(fig, f'上证只跌了{-ret["上证指数"]:.0f}%，科创50跌了{-ret["科创50"]:.0f}%',
           f'A股主要指数 2026年7月以来涨跌幅（截至{end.month}月{end.day}日收盘）', '数据：腾讯行情')
    save(fig, '图2_A股指数跌幅.png')
    return ret


# ---------- 图3 海内外走势（静态 + 动图） ----------
LINES = ['纳斯达克', '上证指数', '创业板指', 'KOSPI', '科创50']


def lines_frame(S, days, upto):
    fig, ax = plt.subplots(figsize=(10, 6.4), dpi=120, facecolor=BG)
    clean(ax)
    now = days[upto]
    last = {}
    for n in LINES:
        s = S[n]
        nv = s[(s.index >= BASE) & (s.index <= now)] / s[BASE] * 100
        ax.plot(nv.index, nv.values, color=CAT[n], lw=3.2 if n in ('上证指数', 'KOSPI', '纳斯达克') else 2.2,
                solid_capstyle='round')
        ax.scatter(nv.index[-1], nv.iloc[-1], color=CAT[n], s=30, zorder=3)
        last[n] = nv.iloc[-1]
    pos = []
    for n, v in sorted(last.items(), key=lambda kv: kv[1]):
        y = max(v, pos[-1][1] + 3.4) if pos else v
        pos.append((n, y))
    for n, y in pos:
        ax.text(now + pd.Timedelta(days=2.5), y, f'{n} {last[n] - 100:+.1f}%', color=CAT[n],
                fontsize=11, va='center', weight='bold')
    ax.axhline(100, color=MUTED, lw=.8, ls='--')
    ax.set_xlim(BASE - pd.Timedelta(days=1), days[-1] + pd.Timedelta(days=30))
    ax.set_ylim(56, 114)
    ax.set_xticks([pd.Timestamp(2026, m, 1) for m in [7, 8, 9, 10]])
    ax.set_xticklabels(['7月', '8月', '9月', '10月'])
    ax.set_yticks([60, 70, 80, 90, 100, 110])
    ax.set_yticklabels(['-40%', '-30%', '-20%', '-10%', '0', '+10%'])
    ax.grid(axis='y', color=GRID, lw=.8)
    fig.subplots_adjust(top=.83, bottom=.09, left=.08, right=.97)
    finish(fig, '同一段时间：纳指在涨，韩国和A股成长板块一起跌',
           f'以2026年6月30日收盘为起点  ·  {now:%m月%d日}', '数据：腾讯行情、Yahoo Finance；本币价格指数，美股截至10月13日收盘')
    return fig


def fig_lines(S):
    days = pd.DatetimeIndex(sorted(set().union(*[set(S[n].index[S[n].index > BASE]) for n in LINES])))
    save(lines_frame(S, days, len(days) - 1), '图3_海内外走势.png')
    frames = [to_image(lines_frame(S, days, i)) for i in range(len(days))]
    write_gif(frames, OUT / '动图_海内外走势.gif', 90)


# ---------- 图4 今年以来：6月30日 → 最新 ----------
def fig_ytd(S):
    names = ['KOSPI', '纳斯达克', '标普500', '科创50', '上证指数', '沪深300', '创业板指']
    y0 = pd.Timestamp('2025-12-31')
    h1 = {n: (at(S[n], BASE) / at(S[n], y0) - 1) * 100 for n in names}
    now = {n: (S[n].iloc[-1] / at(S[n], y0) - 1) * 100 for n in names}
    order = sorted(names, key=lambda n: now[n])
    fig, ax = plt.subplots(figsize=(10, 7), dpi=150, facecolor=BG)
    clean(ax)
    for i, n in enumerate(order):
        a, b = h1[n], now[n]
        c = UP if b >= a else DOWN
        ax.annotate('', xy=(b, i), xytext=(a, i), arrowprops=dict(arrowstyle='-|>', color=c, lw=2.4, mutation_scale=16))
        ax.scatter(a, i, s=70, facecolor=BG, edgecolor=MUTED, lw=1.6, zorder=3)
        ax.text(b + (2.5 if b >= a else -2.5), i, f'{b:+.1f}%', va='center', ha='left' if b >= a else 'right',
                color=INK, fontsize=12, weight='bold')
        ax.text(-60, i, n, va='center', ha='left', color=INK, fontsize=12, weight='bold' if n == '上证指数' else 'normal')
    ax.axvline(0, color=MUTED, lw=.8)
    ax.set_xlim(-60, 115)
    ax.set_ylim(-.7, len(order) - .3)
    ax.set_yticks([])
    ax.set_xticks([-20, 0, 20, 40, 60, 80, 100])
    ax.set_xticklabels(['-20%', '0', '+20%', '+40%', '+60%', '+80%', '+100%'])
    ax.grid(axis='x', color=GRID, lw=.8)
    ax.scatter([], [], s=70, facecolor=BG, edgecolor=MUTED, lw=1.6, label='6月30日')
    ax.plot([], [], color=MUTED, lw=2.4, label='箭头：到最新收盘')
    ax.legend(loc='lower right', frameon=False, fontsize=10, labelcolor=MUTED)
    fig.subplots_adjust(top=.84, bottom=.1, left=.03, right=.97)
    finish(fig, f'KOSPI跌了三成，今年仍涨{now["KOSPI"]:.0f}%',
           '2026年以来累计涨跌：空心圆为6月30日，箭头指向最新收盘',
           '数据：腾讯行情、Yahoo Finance；本币价格指数，不含分红；美股截至10月13日收盘')
    save(fig, '图4_今年以来.png')
    return h1, now


# ---------- 图5 上证近10年日历墙（静态 + 逐年动图） ----------
def wall_frame(S, upto):
    s = S['上证指数']
    pct = s.pct_change() * 100
    pct = pct[pct.index.year >= Y0]
    years = list(range(Y0, 2027))
    mat = np.full((len(years), 366), np.nan)
    for d, v in pct.items():
        if d.year <= upto:
            mat[d.year - Y0, d.dayofyear - 1] = v
    fig = plt.figure(figsize=(12, 7.2), dpi=150, facecolor=BG)
    ax = fig.add_axes([0.07, 0.16, 0.80, 0.66])
    clean(ax)
    cmap = CMAP.copy()
    cmap.set_bad(BG)
    ax.imshow(np.ma.masked_invalid(mat), aspect='auto', cmap=cmap, norm=NORM, interpolation='nearest',
              extent=[0, 366, len(years), 0])
    for i in range(len(years) + 1):
        ax.axhline(i, color=BG, lw=3)
    ax.set_xlim(0, 366)
    ax.set_yticks(np.arange(len(years)) + .5)
    ax.set_yticklabels(years, fontsize=10.5)
    ax.set_xticks([pd.Timestamp(2025, m, 15).dayofyear for m in range(1, 13)])
    ax.set_xticklabels([f'{m}月' for m in range(1, 13)], fontsize=10)
    yr = s.groupby(s.index.year).last()
    ret = (yr / yr.shift(1) - 1) * 100
    rax = fig.add_axes([0.875, 0.16, 0.10, 0.66], sharey=ax)
    rax.axis('off')
    rax.set_title('全年', color=MUTED, fontsize=10, pad=4)
    for y in years:
        if y > upto:
            continue
        v = ret[y]
        rax.barh(y - Y0 + .5, v, height=.55, color=UP if v >= 0 else DOWN)
        rax.text(v + (2 if v >= 0 else -2), y - Y0 + .5, f'{v:+.0f}%' + ('*' if y == 2026 else ''),
                 va='center', ha='left' if v >= 0 else 'right', color=INK, fontsize=9)
    rax.set_xlim(-45, 50)
    rax.axvline(0, color=MUTED, lw=.6)
    if upto >= 2026:
        for y, d0, d1 in [(2024, '2024-09-24', '2024-10-08'), (2026, '2026-07-01', '2026-10-14')]:
            a, b = pd.Timestamp(d0).dayofyear - 1, pd.Timestamp(d1).dayofyear
            ax.add_patch(plt.Rectangle((a - 1.5, y - Y0 + .04), b - a + 3, .92, fill=False, ec=INK, lw=1.4))
    colorbar(fig, [0.07, 0.085, 0.25, 0.015])
    shown = pct[pct.index.year <= upto]
    finish(fig, '上证指数近10年，每一天都是一个格子',
           f'{Y0}年1月至{shown.index[-1]:%Y年%m月%d日}  ·  {len(shown):,} 个交易日  ·  上涨日占 {(shown > 0).mean() * 100:.1f}%',
           '黑框：2024年9·24行情、2026年7月以来  ·  空白为周末/节假日  ·  *2026年截至10月14日  ·  数据：腾讯行情',
           top=0.935)
    return fig


def fig_wall(S):
    save(wall_frame(S, 2026), '图5_近10年日历墙.png')
    frames = [to_image(wall_frame(S, y), 2 / 3) for y in range(Y0, 2027)]
    write_gif(frames, OUT / '动图_近10年日历墙.gif', 650, hold=3000, colors=128)


# ---------- 图6 2017年以来累计走势 ----------
def fig_since(S):
    names = ['纳斯达克', '标普500', 'KOSPI', '沪深300', '上证指数']
    fig, ax = plt.subplots(figsize=(10, 6.6), dpi=150, facecolor=BG)
    clean(ax)
    res = {}
    for n in names:
        base = at(S[n], START)
        s = pd.concat([pd.Series({START: base}), S[n][S[n].index > START]])
        nv = s / base * 100
        res[n] = nv.iloc[-1] - 100
        ax.plot(nv.index, nv.values, color=CAT[n], lw=3 if n in ('上证指数', '纳斯达克', 'KOSPI') else 2)
    # 终点标签按数值排开（对数坐标下按对数间距）
    pos = []
    for n, v in sorted(res.items(), key=lambda kv: kv[1]):
        y = max(np.log(v + 100), pos[-1][1] + 0.09) if pos else np.log(v + 100)
        pos.append((n, y))
    end = max(S[n].index[-1] for n in names)
    for n, y in pos:
        ax.text(end + pd.Timedelta(days=40), np.exp(y), f'{n} {res[n]:+.0f}%', color=CAT[n],
                fontsize=11.5, weight='bold', va='center')
    ax.set_yscale('log')
    ax.axhline(100, color=MUTED, lw=.8, ls='--')
    ax.set_yticks([75, 100, 150, 200, 300, 400, 500])
    ax.set_yticklabels(['-25%', '起点', '+50%', '×2', '×3', '×4', '×5'])
    ax.minorticks_off()
    ax.set_xlim(START, pd.Timestamp('2028-12-31'))
    ax.set_xticks([pd.Timestamp(y, 1, 1) for y in range(2017, 2027, 2)])
    ax.set_xticklabels([str(y) for y in range(2017, 2027, 2)])
    ax.grid(axis='y', color=GRID, lw=.8)
    fig.subplots_adjust(top=.83, bottom=.09, left=.08, right=.97)
    finish(fig, '同样从2017年出发，近10年走到了哪里',
           '以2016年最后一个交易日收盘为起点（对数刻度）', '数据：腾讯行情、Yahoo Finance；本币价格指数，不含分红；美股截至10月13日收盘')
    save(fig, '图6_2017年以来走势.png')
    return res


# ---------- 图7 近10年年度涨跌矩阵 ----------
def fig_annual(S):
    names = ['上证指数', '沪深300', 'KOSPI', '标普500', '纳斯达克']
    years = list(range(Y0, 2027))
    tab, total = {}, {}
    for n in names:
        yr = S[n].groupby(S[n].index.year).last()
        tab[n] = ((yr / yr.shift(1) - 1) * 100).reindex(years)
        total[n] = (S[n].iloc[-1] / at(S[n], START) - 1) * 100
    fig = plt.figure(figsize=(12, 5.6), dpi=150, facecolor=BG)
    ax = fig.add_axes([0.1, 0.13, 0.72, 0.62])
    clean(ax)
    nm = TwoSlopeNorm(vmin=-40, vcenter=0, vmax=40)
    for i, n in enumerate(names):
        for j, y in enumerate(years):
            v = tab[n][y]
            ax.add_patch(plt.Rectangle((j + .04, i + .06), .92, .88, color=CMAP(nm(np.clip(v, -40, 40))), lw=0))
            ax.text(j + .5, i + .5, f'{v:+.0f}%', ha='center', va='center', fontsize=10,
                    color='white' if abs(v) > 25 else INK)
        fig.text(0.84, 0.75 - (i + .5) / len(names) * 0.62, f'{total[n]:+.0f}%', color=UP if total[n] >= 0 else DOWN,
                 fontsize=14, weight='bold', va='center')
    ax.set_xlim(0, len(years))
    ax.set_ylim(len(names), 0)
    ax.set_yticks(np.arange(len(names)) + .5)
    ax.set_yticklabels(names, color=INK, fontsize=11)
    ax.set_xticks(np.arange(len(years)) + .5)
    ax.set_xticklabels([str(y) for y in years], fontsize=10)
    ax.xaxis.tick_top()
    fig.text(0.84, 0.79, '累计', color=MUTED, fontsize=10)
    finish(fig, '近10年年度涨跌：上证累计垫底',
           f'各指数每年涨跌幅，右侧为{Y0}年初至今累计涨跌',
           '数据：腾讯行情、Yahoo Finance；本币价格指数，不含分红；2026年为年内至今', top=0.93)
    save(fig, '图7_近10年年度涨跌.png')
    return tab, total


def main():
    S, cutoff = load()
    end = cutoff['上证指数']
    fig_calendars(S, end)
    fig_cn_rank(S, end)
    fig_lines(S)
    h1, now = fig_ytd(S)
    fig_wall(S)
    since = fig_since(S)
    tab, total = fig_annual(S)
    sh = S['上证指数']
    pct = sh.pct_change()[sh.index.year >= Y0] * 100
    rng = sh[sh.index > START]
    stats = {
        '截止日': {k: f'{v:%Y-%m-%d}' for k, v in cutoff.items()},
        '7月以来涨跌': {n: round((S[n].iloc[-1] / S[n][BASE] - 1) * 100, 2) for n in S},
        '7月以来跌超3%天数': {n: int(((S[n].pct_change() * 100)[S[n].index > BASE] <= -3).sum()) for n in S},
        '今年以来_6月30日': {k: round(v, 2) for k, v in h1.items()},
        '今年以来_最新': {k: round(v, 2) for k, v in now.items()},
        f'{Y0}年以来累计': {k: round(v, 2) for k, v in since.items()},
        '年度涨跌': {n: {int(y): round(v, 2) for y, v in tab[n].items()} for n in tab},
        '上证近10年': {'区间': f'{pct.index[0]:%Y-%m-%d} 至 {pct.index[-1]:%Y-%m-%d}', '交易日': int(len(pct)),
                   '上涨日占比': round((pct > 0).mean() * 100, 2), '涨跌超3%天数': int((pct.abs() >= 3).sum()),
                   '区间收盘最高': f'{rng.idxmax():%Y-%m-%d} {rng.max():.2f}',
                   '区间收盘最低': f'{rng.idxmin():%Y-%m-%d} {rng.min():.2f}',
                   '2016年末收盘': round(float(at(sh, START)), 2)},
    }
    (ROOT / '分析结果.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
    show = ['今年以来_最新', f'{Y0}年以来累计', '年度涨跌', '上证近10年']
    print(json.dumps({k: stats[k] for k in show}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
