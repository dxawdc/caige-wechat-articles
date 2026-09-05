"""v1.0.0 | 2026-09-06 | 教学模拟数据、统一样式、输出工具。"""
from pathlib import Path
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.sankey import Sankey
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde, linregress
import squarify
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '图表'
OUT.mkdir(exist_ok=True)
CHROME = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
if CHROME.exists():
    os.environ.setdefault('BROWSER_PATH', str(CHROME))
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'Noto Sans CJK SC', 'DejaVu Sans'],
    'axes.unicode_minus': False, 'font.size': 10, 'axes.titlesize': 14,
    'axes.labelsize': 10, 'xtick.labelsize': 9, 'ytick.labelsize': 9,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.edgecolor': '#CBD2DC', 'text.color': '#263445',
    'axes.labelcolor': '#263445', 'xtick.color': '#526071', 'ytick.color': '#526071',
    'savefig.facecolor': 'white', 'figure.facecolor': 'white',
})
BLUE, ORANGE, GOLD, OLIVE, PINK = '#3269B4', '#D88936', '#C5A544', '#778A42', '#C76589'
COLORS = [BLUE, ORANGE, OLIVE, PINK, GOLD]
SEQUENTIAL = [[0, '#F0F4FA'], [1, BLUE]]
DIVERGING = [[0, ORANGE], [.5, '#FAFAFA'], [1, BLUE]]
CMAP = LinearSegmentedColormap.from_list('blue_article', ['#F0F4FA', BLUE])
DCMAP = LinearSegmentedColormap.from_list('signed_article', [ORANGE, '#FAFAFA', BLUE])
rng = np.random.default_rng(20260906)

# 同一脚本重跑、单篇图重跑均产生同样的数据。
months = np.arange(1, 13)
orders = np.array([120, 138, 132, 162, 175, 188, 205, 198, 221, 245, 258, 276])
trend_parts = np.array([[55, 60, 58, 72, 77, 86, 92, 89, 98, 110, 115, 124],
                        [40, 46, 43, 52, 56, 59, 66, 63, 73, 81, 87, 93],
                        [25, 32, 31, 38, 42, 43, 47, 46, 50, 54, 56, 59]])
trend_names = ['自然访问', '内容推荐', '广告访问']
channels = np.array(['自然搜索', '内容推荐', '社群', '广告'])
values = np.array([420, 350, 280, 190])
before = np.array([290, 260, 230, 150])
after = np.array([350, 330, 250, 210])
periods = ['第一季度', '第二季度', '第三季度']
matrix = np.array([[120, 100, 80, 60], [140, 110, 90, 65], [160, 140, 110, 65]])
percent = matrix / matrix.sum(axis=1, keepdims=True) * 100
group_names = ['方案 A', '方案 B', '方案 C']
samples = [np.clip(rng.normal(mu, sd, 160), 1, None) for mu, sd in [(34, 8), (41, 10), (47, 9)]]
dist = samples[0]
bins = np.arange(0, 81, 5)
hist_counts, _ = np.histogram(dist, bins=bins)
density_grid = np.linspace(0, 80, 240)
density = gaussian_kde(dist, bw_method=.3)(density_grid)
box_stats = []
for name, a in zip(group_names, samples):
    q1, med, q3 = np.quantile(a, [.25, .5, .75], method='linear')
    iqr = q3 - q1
    lo = a[a >= q1 - 1.5 * iqr].min()
    hi = a[a <= q3 + 1.5 * iqr].max()
    box_stats.append(dict(label=name, q1=q1, med=med, q3=q3, whislo=lo, whishi=hi,
                          fliers=a[(a < lo) | (a > hi)]))
violin_densities = [gaussian_kde(a, bw_method=.3)(density_grid) for a in samples]
jitter = [rng.uniform(-.18, .18, len(a)) for a in samples]
budget = rng.uniform(10, 100, 140)
sales = np.rint(np.clip(3.7 * budget + rng.normal(0, 45, 140) + 45, 0, None))
customers = rng.integers(30, 200, 140)
segment = np.arange(140) % 3
scatter_df = pd.DataFrame({'预算': budget, '订单': sales, '客户数': customers, '分组': segment})
slope, intercept, rvalue, pvalue, stderr = linregress(budget, sales)
fit_x = np.linspace(0, 110, 100)
fit_y = intercept + slope * fit_x
xedges, yedges = np.linspace(0, 110, 12), np.linspace(0, 550, 12)
hist2d, _, _ = np.histogram2d(budget, sales, bins=(xedges, yedges))
metric_names = ['预算', '曝光', '访问', '订单', '客单价']
metric_data = np.column_stack([budget, budget * 80 + rng.normal(0, 800, 140),
                              budget * 12 + rng.normal(0, 180, 140), sales,
                              rng.normal(80, 12, 140)])
corr = np.corrcoef(metric_data, rowvar=False)
gx, gy = np.linspace(0, 10, 100), np.linspace(0, 8, 80)
XX, YY = np.meshgrid(gx, gy)
ZZ = 100 * np.exp(-((XX - 6) ** 2 / 12 + (YY - 4) ** 2 / 5))
contour_levels = np.arange(0, 101, 10)
funnel_names = ['访问页面', '查看商品', '加入购物车', '提交订单', '支付完成']
funnel_values = np.array([10000, 6200, 3200, 1900, 1500])
tree_labels = ['搜索广告', '信息流', '短视频', '公众号', '社群']
tree_values = [35, 25, 20, 12, 8]
radar_labels = ['性能', '易用', '文档', '扩展', '维护']
radar_a, radar_b = np.array([4, 3, 5, 4, 3]), np.array([3, 5, 4, 3, 4])
angles = np.linspace(0, 2 * np.pi, 5, endpoint=False)
hours = np.arange(0, 24, 3)
hour_values = np.array([8, 5, 12, 35, 42, 38, 50, 27])
tasks = pd.DataFrame({'任务': ['需求确认', '数据准备', '开发实现', '测试验收', '上线观察'],
                      '开始': pd.to_datetime(['2026-01-02', '2026-01-04', '2026-01-07', '2026-01-13', '2026-01-17']),
                      '结束': pd.to_datetime(['2026-01-05', '2026-01-08', '2026-01-14', '2026-01-17', '2026-01-21'])})
ohlc_dates = pd.date_range('2026-01-01', periods=12, freq='D')
open_prices = 100 + np.cumsum(rng.normal(0, 1.8, 12))
close_prices = open_prices + rng.normal(0, 2.4, 12)
high_prices = np.maximum(open_prices, close_prices) + rng.uniform(.6, 2, 12)
low_prices = np.minimum(open_prices, close_prices) - rng.uniform(.6, 2, 12)
issues = ['加载慢', '支付失败', '闪退', '界面错位', '消息延迟', '其他']
issue_counts = np.array([48, 30, 18, 12, 8, 4])
cumulative = issue_counts.cumsum() / issue_counts.sum() * 100

def new_m(title, xlabel='', ylabel='', polar=False):
    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=200, layout='constrained',
                           subplot_kw={'projection': 'polar'} if polar else {})
    ax.set_title(title, loc='center' if polar else 'left', pad=18)
    if not polar:
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_axisbelow(True)
        ax.grid(axis='y', color='#E8ECF2', linewidth=.65)
    return fig, ax

def new_p(title, xlabel='', ylabel=''):
    fig = go.Figure()
    fig.update_layout(template='plotly_white', width=720, height=480,
                      font=dict(family='Microsoft YaHei, Noto Sans CJK SC, Arial', size=14, color='#263445'),
                      title=dict(text=title, x=.07, y=.97, font_size=20),
                      margin=dict(l=70, r=35, t=85, b=65),
                      xaxis=dict(title=xlabel, showgrid=False, zeroline=False),
                      yaxis=dict(title=ylabel, gridcolor='#E8ECF2', zeroline=False),
                      colorway=COLORS, showlegend=False, paper_bgcolor='white', plot_bgcolor='white',
                      legend=dict(orientation='h', x=0, y=1.12, font_size=12, traceorder='normal'))
    return fig

def finish(number, name, mfig, pfig):
    stem = f'{number:02d}_{name}_v1.0.0'
    for trace in pfig.data:
        if isinstance(trace, go.Scatter) and trace.mode is None:
            trace.mode = 'lines'
    mfig.savefig(OUT / f'{stem}_matplotlib.png', dpi=200)
    plt.close(mfig)
    # 共用一份本地 plotly.min.js，断网也可以查看交互图。
    pfig.write_html(OUT / f'{stem}_plotly.html', include_plotlyjs='directory',
                   config={'displaylogo': False, 'responsive': True})
    pfig.write_json(OUT / f'{stem}_plotly.json')
    if os.environ.get('CHART_BATCH') != '1':
        pfig.write_image(OUT / f'{stem}_plotly.png', width=720, height=480, scale=2)
    print(f'完成 {number:02d} {name}', flush=True)
