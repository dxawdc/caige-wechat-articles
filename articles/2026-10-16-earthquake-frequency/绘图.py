"""读取 数据/ 下的 USGS 地震目录，生成全部图表、动图与 分析结果.json。"""
from pathlib import Path
import io
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.collections import LineCollection, PolyCollection
from scipy.spatial import cKDTree
from PIL import Image

ROOT = Path(__file__).resolve().parent
D = ROOT / '数据'
OUT = ROOT / '图表'
OUT.mkdir(exist_ok=True)

# 视觉轮换方案（2026-10-11启用）：白底、靛蓝/珊瑚/紫色
INK, INDIGO, CORAL, VIOLET = '#202B54', '#4457C4', '#DB655A', '#9471BE'
GRID, BG, MUTED, LAND = '#E4E6F1', '#FAFAFE', '#6C7390', '#E9EBF3'
BRAND = '可以叫我才哥'
plt.rcParams.update({
    'font.family': ['Microsoft YaHei', 'SimHei', 'sans-serif'], 'axes.unicode_minus': False,
    'figure.facecolor': BG, 'axes.facecolor': BG, 'savefig.facecolor': BG,
    'axes.edgecolor': GRID, 'axes.labelcolor': MUTED, 'xtick.color': MUTED, 'ytick.color': MUTED,
    'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 11,
})
UTC_END = '2026-10-16'
RESULT = {}


def head(fig, title, sub):
    """左上角标题层级 + 右下角品牌。"""
    fig.text(0.04, 0.955, title, fontsize=19, fontweight='bold', color=INK, va='top')
    fig.text(0.04, 0.885, sub, fontsize=11.5, color=MUTED, va='top')
    fig.text(0.96, 0.02, BRAND, fontsize=10, color='#A3A9C2', ha='right', va='bottom')


def foot(fig, text):
    fig.text(0.04, 0.02, text, fontsize=9, color='#9AA0B8', va='bottom')


def save(fig, name):
    fig.savefig(OUT / name, dpi=160)
    plt.close(fig)


# ---------- 底图 ----------
def rings(geom):
    cs = geom['coordinates']
    if geom['type'] == 'Polygon':
        cs = [cs]
    return [np.array(poly[0]) for poly in cs]


LAND_RINGS = []
for f in json.loads((D / '底图/陆地轮廓.geojson').read_text(encoding='utf8'))['features']:
    LAND_RINGS += rings(f['geometry'])

PLATE_SEGS = []
for f in json.loads((D / '底图/板块边界PB2002.json').read_text(encoding='utf8'))['features']:
    c = np.array(f['geometry']['coordinates'])
    for a, b in zip(c[:-1], c[1:]):
        if abs(a[0] - b[0]) < 180:
            PLATE_SEGS.append([a, b])
PLATE_SEGS = np.array(PLATE_SEGS)


def draw_base(ax, shift=0.0, plates=True, xlim=None, ylim=None):
    """陆地只画轮廓填色，不画国界；shift用于把太平洋放到地图中间。"""
    for off in ([0, 360] if shift else [0]):
        polys = [np.c_[r[:, 0] + off, r[:, 1]] for r in LAND_RINGS]
        ax.add_collection(PolyCollection(polys, facecolor=LAND, edgecolor='#D3D7E6', linewidth=0.4, zorder=1))
        if plates:
            segs = PLATE_SEGS.copy()
            segs[:, :, 0] += off
            ax.add_collection(LineCollection(segs, colors='#B9A6D6', linewidths=0.7, zorder=2))
    ax.set_xlim(*(xlim or (-180, 180)))
    ax.set_ylim(*(ylim or (-62, 80)))
    ax.set_aspect('equal')
    ax.set_xticks([]), ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def pac(lon):
    """太平洋居中：经度小于-20°的点加360。"""
    lon = np.asarray(lon, float)
    return np.where(lon < -20, lon + 360, lon)


def msize(m, k=1.0):
    return k * 2.2 ** (np.asarray(m) - 4.5) * 6


def depth_color(dep):
    return np.where(dep <= 70, CORAL, np.where(dep <= 300, VIOLET, INDIGO))


def depth_legend(ax, loc='lower left'):
    for c, t in [(CORAL, '浅源 ≤70千米'), (VIOLET, '中源 70—300千米'), (INDIGO, '深源 >300千米')]:
        ax.scatter([], [], s=30, color=c, alpha=0.8, label=t)
    ax.plot([], [], color='#B9A6D6', lw=1.2, label='板块边界')
    ax.legend(loc=loc, frameon=False, fontsize=9.5, labelcolor=INK, handletextpad=0.3)


# ---------- 读数 ----------
def read(name):
    df = pd.read_csv(D / name, parse_dates=['time'])
    return df[df.time < pd.Timestamp(UTC_END, tz='UTC')].copy()


g6 = read('全球6级以上_1950起.csv')
g5 = read('全球5级以上_2016起.csv')
g30 = read('全球4.5级以上_最近30天.csv')
cnbox = read('中国周边4.5级以上_1976起.csv')
kam = read('堪察加序列_2025.csv')

# ---------- 中国省份归属 ----------
CN = json.loads((D / '底图/中国省级区划.json').read_text(encoding='utf8'))
PROV, TREE_PTS, TREE_NAME = [], [], []
for f in CN['features']:
    name = f['properties'].get('name')
    if not name:
        continue
    rs = rings(f['geometry'])
    PROV.append((name, [MPath(r) for r in rs]))
    for r in rs:
        x, y = r[:, 0], r[:, 1]
        area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        if area > 0.5:               # 近海归属只参考较大陆地，避免小岛把远海地震拉进来
            TREE_PTS.append(r)
            TREE_NAME += [name] * len(r)
TP = np.vstack(TREE_PTS)
TREE = cKDTree(np.c_[TP[:, 0] * np.cos(np.radians(TP[:, 1])), TP[:, 1]])
OTHERS = []
for f in json.loads((D / '底图/国家区域_110m.geojson').read_text(encoding='utf8'))['features']:
    if f['properties']['ADM0_A3'] not in ('CHN', 'TWN'):
        OTHERS += [MPath(r) for r in rings(f['geometry'])]
SHORT = {'新疆维吾尔自治区': '新疆', '西藏自治区': '西藏', '广西壮族自治区': '广西', '内蒙古自治区': '内蒙古',
         '宁夏回族自治区': '宁夏', '香港特别行政区': '香港', '澳门特别行政区': '澳门'}


def short(n):
    return SHORT.get(n, n.replace('省', '').replace('市', ''))


def assign_china(df):
    """震中在省级区划内记为该省；不在他国陆地、且距较大陆地约100千米内的海上地震记为该省近海。"""
    pts = df[['longitude', 'latitude']].values
    lab = np.full(len(df), None, dtype=object)
    for name, paths in PROV:
        m = np.zeros(len(df), bool)
        for p in paths:
            m |= p.contains_points(pts)
        lab[m & (lab == None)] = name  # noqa: E711
    other = np.zeros(len(df), bool)
    for p in OTHERS:
        other |= p.contains_points(pts)
    dist, idx = TREE.query(np.c_[pts[:, 0] * np.cos(np.radians(pts[:, 1])), pts[:, 1]])
    sea = (lab == None) & ~other & (dist < 0.9)  # noqa: E711
    for k in np.where(sea)[0]:
        lab[k] = TREE_NAME[idx[k]]
    out = df.copy()
    out['省份'] = [short(x) if x else None for x in lab]
    out['近海'] = sea
    return out[out['省份'].notna()].copy()


cn = assign_china(cnbox)
cn['年'] = cn.time.dt.year

# =====================================================================
# 图1 最近30天全球4.5级以上
fig = plt.figure(figsize=(10, 5.3))
ax = fig.add_axes([0.02, 0.07, 0.96, 0.74])
draw_base(ax, shift=1, xlim=(-20, 340), ylim=(-62, 76))
order = g30.sort_values('mag')
ax.scatter(pac(order.longitude), order.latitude, s=msize(order.mag), c=depth_color(order.depth),
           alpha=0.72, linewidths=0.3, edgecolors='white', zorder=3)
labels30 = [('巴拿马 7.7级', -80.6, 7.6, -46, -20), ('大西洋中脊 6.8级', -36.0, 4.0, -30, 16),
            ('新喀里多尼亚 6.6级', 168.6, -21.0, 6, -26), ('阿拉斯加 6.5级', -170.0, 52.0, 6, 14)]
for t, lo, la, dx, dy in labels30:
    x = pac(lo)
    ax.annotate(t, (x, la), (x + dx, la + dy), fontsize=10, color=INK, fontweight='bold',
                arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.8), zorder=5)
depth_legend(ax)
n30 = len(g30)
head(fig, f'最近30天，全球发生了{n30}次4.5级以上地震',
     f'2026年9月16日—10月15日（UTC），其中6级以上{int((g30.mag >= 6).sum())}次；圆越大震级越高')
foot(fig, '数据：USGS地震目录；底图仅示陆地轮廓与板块边界')
save(fig, '图1_最近30天全球地震.png')
RESULT['最近30天'] = {'4.5级以上': n30, '6级以上': int((g30.mag >= 6).sum()), '7级以上': int((g30.mag >= 7).sum()),
                   '最大': g30.nlargest(5, 'mag')[['time', 'mag', 'place']].astype(str).to_dict('records')}

# =====================================================================
# 图2 1950年以来每年7级以上地震
g6['年'] = g6.time.dt.year
yr = g6.groupby('年').agg(m6=('mag', 'size'), m7=('mag', lambda s: int((s >= 7).sum())))
full = yr.loc[1950:2025]
mean7 = full.m7.mean()
fig = plt.figure(figsize=(10, 5.6))
ax = fig.add_axes([0.07, 0.12, 0.9, 0.66])
ax.bar(full.index, full.m7, color=INDIGO, width=0.72, alpha=0.88)
ax.bar([2026], [yr.loc[2026, 'm7']], color='white', edgecolor=CORAL, hatch='////', width=0.72, linewidth=1)
ax.axhline(mean7, color=CORAL, lw=1.4, ls='--')
ax.text(1951, 26.5, f'虚线：1950—2025年平均 {mean7:.1f} 次/年', color=CORAL, fontsize=10.5, fontweight='bold')
for y_ in [2010, 1995, 1968]:
    ax.text(y_, full.m7[y_] + 0.4, str(full.m7[y_]), ha='center', fontsize=9, color=INK)
ax.text(2026, yr.loc[2026, 'm7'] + 0.4, f"{yr.loc[2026, 'm7']}", ha='center', fontsize=9, color=CORAL, fontweight='bold')
ax.set_xlim(1948.5, 2027.5)
ax.set_ylim(0, 29)
ax.yaxis.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_ylabel('次数')
head(fig, '全球7级以上大地震，并没有越来越多', '每年7级以上地震次数，1950年至今；斜线柱为2026年（截至10月15日）')
foot(fig, '数据：USGS地震目录（震级以USGS为准）')
save(fig, '图2_全球7级以上年度次数.png')
RESULT['全球大地震年度'] = {
    '7级以上年均_1950_2025': round(mean7, 1),
    '分段年均7级以上': {f'{a}-{b}': round(yr.loc[a:b, 'm7'].mean(), 1) for a, b in [(1950, 1975), (1976, 2000), (2001, 2025), (2016, 2025)]},
    '分段年均6级以上': {f'{a}-{b}': round(yr.loc[a:b, 'm6'].mean(), 1) for a, b in [(1950, 1975), (1976, 2000), (2001, 2025), (2016, 2025)]},
    '最多年份': {int(full.m7.idxmax()): int(full.m7.max())}, '最少年份': {int(full.m7.idxmin()): int(full.m7.min())},
    '2026至10月15日': {'7级以上': int(yr.loc[2026, 'm7']), '6级以上': int(yr.loc[2026, 'm6'])},
    '2026按天数折算全年7级以上': round(yr.loc[2026, 'm7'] / 288 * 365, 1),
}

# =====================================================================
# 图3 近10年全球5级以上分布 + 板块边界距离
g10 = g5[g5.time < pd.Timestamp('2026-01-01', tz='UTC')].copy()


def xyz(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


dense = np.vstack([np.linspace(a, b, max(2, int(np.hypot(*(b - a)) / 0.1))) for a, b in PLATE_SEGS])
ptree = cKDTree(xyz(dense[:, 0], dense[:, 1]))
chord, _ = ptree.query(xyz(g10.longitude.values, g10.latitude.values))
g10['距板块边界km'] = 2 * np.arcsin(chord / 2) * 6371
near200 = (g10['距板块边界km'] < 200).mean()
fig = plt.figure(figsize=(10, 5.3))
ax = fig.add_axes([0.02, 0.07, 0.96, 0.74])
draw_base(ax, shift=1, xlim=(-20, 340), ylim=(-62, 76))
order = g10.sort_values('mag')
ax.scatter(pac(order.longitude), order.latitude, s=msize(order.mag, 0.55), c=depth_color(order.depth),
           alpha=0.45, linewidths=0, zorder=3)
for t, x, y in [('环太平洋地震带', 205, 30), ('欧亚地震带', 60, 46)]:
    ax.text(x, y, t, fontsize=13, fontweight='bold', color=INK, ha='center',
            bbox=dict(boxstyle='round,pad=0.25', fc=BG, ec='none', alpha=0.8), zorder=6)
depth_legend(ax)
head(fig, f'近10年{len(g10):,}次5级以上地震，{near200:.0%}在板块边界附近',
     '2016—2025年全球5级以上地震震中；“附近”指距板块边界200千米以内')
foot(fig, '数据：USGS地震目录；板块边界：Bird (2003) PB2002')
save(fig, '图4_近10年全球5级以上分布.png')
RESULT['近10年全球5级以上'] = {'次数': len(g10), '年均': round(len(g10) / 10, 1),
                          '距板块边界100km内': round((g10['距板块边界km'] < 100).mean(), 3),
                          '距板块边界200km内': round(near200, 3),
                          '浅源70km内占比': round((g10.depth <= 70).mean(), 3)}

# =====================================================================
# 图4 地区排行（USGS地名标签 + 本文中国归属口径）
NAME = {'Indonesia': '印度尼西亚', 'Papua New Guinea': '巴布亚新几内亚', 'South Sandwich Islands region': '南桑威奇群岛一带',
        'Russia': '俄罗斯', 'Philippines': '菲律宾', 'Japan': '日本', 'Japan region': '日本', 'Tonga': '汤加',
        'Vanuatu': '瓦努阿图', 'Alaska': '美国阿拉斯加', 'Chile': '智利', 'Kermadec Islands region': '克马德克群岛一带',
        'New Zealand': '新西兰', 'Solomon Islands': '所罗门群岛', 'Mexico': '墨西哥', 'Peru': '秘鲁'}
g10['地区'] = g10.place.str.split(', ').str[-1].str.strip().map(NAME)
rank = g10['地区'].value_counts()
cn10 = cn[(cn.mag >= 5) & (cn.time >= pd.Timestamp('2016-01-01', tz='UTC')) & (cn.time < pd.Timestamp('2026-01-01', tz='UTC'))]
rank['中国（含台湾及近海）'] = len(cn10)
rank = rank.sort_values(ascending=False).head(13)[::-1]
fig = plt.figure(figsize=(10, 6.6))
ax = fig.add_axes([0.24, 0.11, 0.7, 0.69])
colors = [CORAL if '中国' in k else INDIGO for k in rank.index]
ax.barh(rank.index, rank.values, color=colors, height=0.66, alpha=0.9)
for i, v in enumerate(rank.values):
    ax.text(v + 15, i, f'{v:,}', va='center', fontsize=10, color=INK)
ax.xaxis.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.tick_params(axis='y', labelsize=11, colors=INK, length=0)
ax.set_xlim(0, rank.max() * 1.12)
head(fig, '近10年5级以上地震，哪些地方最多', '2016—2025年，按震中所在国家或海域统计次数')
foot(fig, '数据：USGS地震目录；海外按USGS地名标签归类，中国按本文省份归属口径')
save(fig, '图5_地区排行.png')
RESULT['地区排行'] = {k: int(v) for k, v in rank[::-1].items()}

# =====================================================================
# 图5 中国震中分布（1976年以来4.5级以上）
fig = plt.figure(figsize=(10, 7.4))
ax = fig.add_axes([0.03, 0.07, 0.94, 0.78])
draw_base(ax, plates=False, xlim=(72, 136), ylim=(16, 54.5))
o = cn.sort_values('mag')
ax.scatter(o.longitude, o.latitude, s=msize(o.mag, 0.6), c=np.where(o.mag >= 6, CORAL, INDIGO),
           alpha=np.where(o.mag >= 6, 0.85, 0.32), linewidths=0, zorder=3)
for t, x, y in [('新疆', 84, 44.6), ('西藏', 86, 30.5), ('青海', 96, 37.0), ('四川', 101.5, 28.4),
                ('云南', 100.0, 23.6), ('台湾', 124.6, 23.4), ('华北', 113.6, 41.6)]:
    ax.text(x, y, t, fontsize=12.5, fontweight='bold', color=INK, ha='center', zorder=6,
            bbox=dict(boxstyle='round,pad=0.2', fc=BG, ec='none', alpha=0.75))
ax.scatter([], [], s=25, color=INDIGO, alpha=0.5, label='4.5—5.9级')
ax.scatter([], [], s=60, color=CORAL, alpha=0.85, label='6级及以上')
ax.legend(loc='lower right', frameon=False, fontsize=10, labelcolor=INK)
head(fig, f'近50年，中国{len(cn):,}次4.5级以上地震都在哪', '1976年至今，中国省级区划内及近海约100千米范围的震中')
foot(fig, '数据：USGS地震目录；示意图仅绘陆地轮廓，不表示行政边界')
save(fig, '图6_中国震中分布.png')

# =====================================================================
# 图6 各省次数（陆地 / 近海）
prov = cn.groupby('省份').agg(总=('mag', 'size'), 近海=('近海', 'sum'), 六级=('mag', lambda s: int((s >= 6).sum())))
prov['陆地'] = prov['总'] - prov['近海']
top = prov.sort_values('总', ascending=False).head(12)[::-1]
fig = plt.figure(figsize=(10, 6.4))
ax = fig.add_axes([0.12, 0.11, 0.82, 0.69])
ax.barh(top.index, top['陆地'], color=INDIGO, height=0.66, label='震中在陆地')
ax.barh(top.index, top['近海'], left=top['陆地'], color=CORAL, height=0.66, label='近海')
for i, (n, r) in enumerate(top.iterrows()):
    ax.text(r['总'] + 25, i, f"{int(r['总']):,}次 · 6级以上{int(r['六级'])}次", va='center', fontsize=9.5, color=INK)
ax.xaxis.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.tick_params(axis='y', labelsize=11.5, colors=INK, length=0)
ax.set_xlim(0, top['总'].max() * 1.32)
ax.legend(loc='lower right', frameon=False, fontsize=10)
head(fig, '台湾、新疆、西藏是4.5级以上地震最多的三个省区', '1976年至今各省级区划4.5级以上地震次数（前12名）')
foot(fig, '数据：USGS地震目录；近海指震中在海上、距陆地约100千米内')
save(fig, '图7_各省地震次数.png')
top5_share = prov['总'].nlargest(5).sum() / prov['总'].sum()
RESULT['中国各省'] = {'总次数': int(len(cn)), '近海': int(cn['近海'].sum()), '前5省区占比': round(top5_share, 3),
                    '排行': {k: {kk: int(vv) for kk, vv in r.items()} for k, r in prov.sort_values('总', ascending=False).iterrows()}}

# =====================================================================
# 图7 中国每年5级以上次数
cy = cn[cn.mag >= 5].groupby('年').size().reindex(range(1976, 2027), fill_value=0)
base = cy.loc[1976:2025]
avg = base.mean()
fig = plt.figure(figsize=(10, 5.6))
ax = fig.add_axes([0.07, 0.12, 0.9, 0.66])
ax.bar(base.index, base.values, color=INDIGO, width=0.72, alpha=0.88)
ax.bar([2026], [cy[2026]], color='white', edgecolor=CORAL, hatch='////', width=0.72, linewidth=1)
ax.axhline(avg, color=CORAL, lw=1.4, ls='--')
ax.text(1977, 150, f'虚线：1976—2025年平均 {avg:.0f} 次/年', color=CORAL, fontsize=10.5, fontweight='bold')
for y_, t in [(2008, '2008\n汶川'), (2024, '2024\n乌什、花莲'), (1986, '1986\n花莲'), (1976, '1976\n唐山')]:
    ax.text(y_, cy[y_] + 2, t, ha='center', fontsize=9, color=INK, linespacing=1.1)
ax.text(2026, cy[2026] + 2, f'{cy[2026]}', ha='center', fontsize=9.5, color=CORAL, fontweight='bold')
ax.set_xlim(1974.5, 2027.5)
ax.set_ylim(0, 165)
ax.yaxis.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_ylabel('次数')
head(fig, '中国每年5级以上地震：高峰都跟着一场大震', '中国省级区划内及近海5级以上地震年度次数；斜线柱为2026年（截至10月15日）')
foot(fig, '数据：USGS地震目录（震级以USGS为准，与中国地震台网测定值可能不同）')
save(fig, '图9_中国5级以上年度次数.png')
rank_years = base.sort_values(ascending=False)
RESULT['中国5级以上年度'] = {'年均_1976_2025': round(avg, 1), '2026至10月15日': int(cy[2026]),
                         '2026按天数折算全年': round(cy[2026] / 288 * 365, 1),
                         '最多前5年': {int(k): int(v) for k, v in rank_years.head(5).items()},
                         '近10年年均_2016_2025': round(base.loc[2016:2025].mean(), 1),
                         '2026折算后排名_1976起': int((base > cy[2026] / 288 * 365).sum() + 1)}

# =====================================================================
# 图8 2026年中国5级以上地震时间线
c26 = cn[(cn.time >= pd.Timestamp('2026-01-01', tz='UTC')) & (cn.mag >= 5)].copy()
c26['t'] = c26.time.dt.tz_convert('Asia/Shanghai').dt.tz_localize(None)
pal = {'青海': CORAL, '四川': VIOLET, '新疆': INDIGO, '台湾': '#2E9C8F'}
fig = plt.figure(figsize=(10, 5.6))
ax = fig.add_axes([0.07, 0.12, 0.9, 0.64])
for p_, grp in c26.groupby(c26['省份'].where(c26['省份'].isin(pal), '其他')):
    ax.scatter(grp.t, grp.mag, s=msize(grp.mag, 3.2), color=pal.get(p_, '#A3A9C2'), alpha=0.82,
               edgecolors='white', linewidths=0.6, label=f'{p_}（{len(grp)}次）', zorder=3)
notes = [('2026-06-16 17:06', 6.3, '青海大柴旦\n台网测定6.3级', 18, 0.05), ('2026-05-18 00:21', 5.0, '广西柳州\n台网测定5.2级', -40, 0.55),
         ('2026-09-03 19:39', 5.5, '四川北川\n台网测定4.8级', 4, 0.75), ('2026-07-28 11:34', 5.8, '青海兴海\n台网测定5.7、5.8级', 6, 0.3)]
for t, m, s, dx, dy in notes:
    x = pd.Timestamp(t)
    ax.annotate(s, (x, m), (x + pd.Timedelta(days=dx), m + dy), fontsize=9.5, color=INK, linespacing=1.15,
                arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.8), zorder=5)
ax.set_xlim(pd.Timestamp('2025-12-25'), pd.Timestamp('2026-10-20'))
ax.set_ylim(4.85, 6.75)
ax.set_yticks([5.0, 5.5, 6.0, 6.5])
ax.yaxis.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_ylabel('USGS震级')
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m月'))
ax.legend(loc='upper left', frameon=False, fontsize=9.5, ncol=5, bbox_to_anchor=(0, 1.1))
head(fig, f'2026年，中国已发生{len(c26)}次5级以上地震', '每个圆是一次地震（北京时间），纵轴为USGS震级')
foot(fig, '数据：USGS地震目录；标注中的台网测定值来自中国地震台网正式测定')
save(fig, '图8_2026年中国5级以上.png')
RESULT['2026中国5级以上'] = {'次数': len(c26), '分省': c26['省份'].value_counts().to_dict()}

# =====================================================================
# 图9 震级每高一级，次数少约10倍
bins = [(5, 6, '5级'), (6, 7, '6级'), (7, 8, '7级'), (8, 10, '8级及以上')]
per = [((g10.mag >= a) & (g10.mag < b)).sum() / 10 for a, b, _ in bins]
fig = plt.figure(figsize=(10, 5.6))
ax = fig.add_axes([0.08, 0.12, 0.52, 0.64])
ax.bar([t for *_, t in bins], per, color=[INDIGO, VIOLET, CORAL, CORAL], width=0.6)
ax.set_yscale('log')
ax.set_ylim(0.3, 5000)
ax.set_yticks([1, 10, 100, 1000], ['1', '10', '100', '1000'])
ax.minorticks_off()
for i, v in enumerate(per):
    ax.text(i, v * 1.25, f'{v:,.1f}' if v < 10 else f'{v:,.0f}', ha='center', fontsize=12, fontweight='bold', color=INK)
ax.yaxis.grid(color=GRID, lw=0.8, which='major')
ax.set_axisbelow(True)
ax.set_ylabel('平均每年次数（对数刻度）')
ax.tick_params(axis='x', labelsize=11.5, colors=INK, length=0)
fig.text(0.66, 0.72, '震级每高1级', fontsize=13, color=INK, fontweight='bold')
fig.text(0.66, 0.64, '次数：约少 10 倍', fontsize=13, color=INDIGO, fontweight='bold')
fig.text(0.66, 0.565, '能量：约大 32 倍', fontsize=13, color=CORAL, fontweight='bold')
fig.text(0.66, 0.30, '一次8级释放的能量\n≈ 32个7级\n≈ 1000个6级', fontsize=12, color=INK, linespacing=1.5)
head(fig, '震级每高一级，次数少约10倍', '2016—2025年全球各震级段地震的年均次数')
foot(fig, '数据：USGS地震目录；能量换算按 lgE = 1.5M + 4.8')
save(fig, '图10_震级与次数.png')
b_fit = np.polyfit(np.arange(5, 7.5, 0.1), np.log10([(g10.mag >= x - 1e-9).sum() for x in np.arange(5, 7.5, 0.1)]), 1)[0]
RESULT['震级规律'] = {'年均': {t: round(v, 1) for (*_, t), v in zip(bins, per)}, 'b值拟合_5到7.4级': round(-b_fit, 2)}

# =====================================================================
# 图10 堪察加8.8级地震前后
t0 = pd.Timestamp('2025-07-29 23:24:52', tz='UTC')
kam['日'] = np.floor((kam.time - t0).dt.total_seconds() / 86400).astype(int)
daily = kam[(kam['日'] >= -15) & (kam['日'] < 120)].groupby('日').size().reindex(range(-15, 120), fill_value=0)
after = kam[kam.time >= t0]
fig = plt.figure(figsize=(10, 5.6))
ax = fig.add_axes([0.08, 0.16, 0.88, 0.6])
ax.bar(daily.index, daily.values, color=np.where(daily.index < 0, VIOLET, INDIGO), width=0.8)
ax.annotate(f'主震当天\n{daily[0]}次', (0, daily[0]), (8, daily[0] - 40), fontsize=10.5, color=CORAL, fontweight='bold',
            arrowprops=dict(arrowstyle='-', color=CORAL, lw=0.8))
ax.annotate('10天前\n7.4级前震', (-10, daily[-10]), (-15, 150), fontsize=9.5, color=VIOLET,
            arrowprops=dict(arrowstyle='-', color=VIOLET, lw=0.8))
d1 = int((after['日'] < 1).sum()); w1 = int((after['日'] < 7).sum()); m1 = int((after['日'] < 30).sum())
last_day = int(after['日'].max())
l30 = int((after['日'] > last_day - 30).sum())
fig.text(0.56, 0.60, f'主震后第1个月：{m1:,}次\n之后14个月合计：{len(after):,}次\n最近30天：仍有{l30}次', fontsize=11.5,
         color=INK, linespacing=1.6, bbox=dict(boxstyle='round,pad=0.6', fc='white', ec=GRID))
ax.set_xlim(-16, 120)
ax.yaxis.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_xlabel('距主震天数')
ax.set_ylabel('4.5级以上地震次数/天')
head(fig, '一场8.8级地震之后：余震来得急，退得慢', '2025年7月30日（北京时间）堪察加8.8级地震周边500千米内，每天4.5级以上地震次数')
foot(fig, '数据：USGS地震目录')
save(fig, '图11_堪察加余震.png')
RESULT['堪察加8.8级'] = {'主震UTC': str(t0), '主震前一个月内4.5级以上': int((kam.time < t0).sum()),
                       '首日': d1, '首周': w1, '首月': m1, '截至10月15日合计': len(after), '最近30天': l30,
                       '其中6级以上': int((after.mag >= 6).sum()), '其中7级以上': int((after.mag >= 7).sum())}

# =====================================================================
# 补充统计：月份与时刻分布（不出图，正文引用）
mon = g10.groupby(g10.time.dt.month).size()
RESULT['月份分布_2016_2025'] = {'最多': {int(mon.idxmax()): int(mon.max())}, '最少': {int(mon.idxmin()): int(mon.min())},
                            '月均': round(mon.mean(), 1)}

# =====================================================================
# 动图：1950年以来全球6级以上地震逐年累积
frames = []
years = list(range(1950, 2027, 2))
xs, ys = pac(g6.longitude.values), g6.latitude.values
for i, y0 in enumerate(years + [2026] * 8):
    fig = plt.figure(figsize=(9, 5.4), dpi=100)
    ax = fig.add_axes([0.02, 0.06, 0.96, 0.76])
    draw_base(ax, shift=1, xlim=(-20, 340), ylim=(-62, 76))
    y1 = min(y0 + 1, 2026)
    old = g6['年'] < y0
    new = (g6['年'] >= y0) & (g6['年'] <= y1)
    ax.scatter(xs[old], ys[old], s=msize(g6.mag[old], 0.35), color=INDIGO, alpha=0.18, linewidths=0, zorder=3)
    ax.scatter(xs[new], ys[new], s=msize(g6.mag[new], 0.7), color=CORAL, alpha=0.9, linewidths=0, zorder=4)
    n = int((g6['年'] <= y1).sum())
    fig.text(0.04, 0.95, '1950年以来全球6级以上地震', fontsize=17, fontweight='bold', color=INK, va='top')
    fig.text(0.04, 0.875, f'{1950}—{y1}年累计 {n:,} 次（珊瑚色为当期新增）', fontsize=11.5, color=MUTED, va='top')
    fig.text(0.96, 0.955, f'{y1}', fontsize=26, fontweight='bold', color=CORAL, ha='right', va='top')
    fig.text(0.96, 0.02, BRAND, fontsize=9, color='#A3A9C2', ha='right', va='bottom')
    fig.text(0.04, 0.02, '数据：USGS地震目录', fontsize=8.5, color='#9AA0B8', va='bottom')
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    frames.append(Image.open(buf).convert('RGB').quantize(colors=64, method=Image.Quantize.MEDIANCUT))
frames[0].save(OUT / '图3_全球6级以上累积.gif', save_all=True, append_images=frames[1:],
               duration=[260] * (len(frames) - 1) + [1800], loop=0, optimize=True)

(ROOT / '分析结果.json').write_text(json.dumps(RESULT, ensure_ascii=False, indent=2, default=str), encoding='utf8')
print(json.dumps(RESULT, ensure_ascii=False, indent=1, default=str)[:6000])
