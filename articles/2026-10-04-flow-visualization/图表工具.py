"""共用字体、配色和文件导出；四份示例的绘图逻辑各自独立。"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '配图'
OUT.mkdir(exist_ok=True)
COLORS = ['#3275BB', '#EE9D3A', '#28A59C', '#906BC3']
INK = '#24364B'
available = {x.name for x in font_manager.fontManager.ttflist}
FONT = next((x for x in ['Microsoft YaHei', 'Noto Sans CJK SC', 'SimHei'] if x in available), None)
if FONT is None:
    raise RuntimeError('请先安装 Microsoft YaHei 或 Noto Sans CJK SC 中文字体。')
plt.rcParams.update({'font.family': FONT, 'axes.unicode_minus': False, 'svg.fonttype': 'none'})

def 保存交互图(fig, stem, title, subtitle):
    fig.update_layout(
        title=dict(text=f'<b>{title}</b><br><sup>{subtitle}</sup>', x=.06, y=.95, yanchor='top', font=dict(size=27)),
        font=dict(family=FONT, size=20, color=INK),
        width=960, height=730, margin=dict(l=95, r=105, t=150, b=100),
        paper_bgcolor='#F7FAFD', plot_bgcolor='#F7FAFD',
        annotations=[dict(text='模拟数据 · 教学演示', x=0, y=-.14, xref='paper', yref='paper', showarrow=False, font=dict(size=15)),
                     dict(text='可以叫我才哥', x=1, y=-.14, xref='paper', yref='paper', showarrow=False, font=dict(size=15))],
    )
    html = fig.to_html(include_plotlyjs=True, div_id=stem)
    html = html.replace('<head>', '<head><link rel="icon" href="data:,">', 1)
    (ROOT / ('交互桑基图.html' if stem == '01_桑基图' else '交互冲积图.html')).write_text(html, encoding='utf-8')
    fig.write_image(OUT / f'{stem}.png', scale=1.8)
    fig.write_image(OUT / f'{stem}.svg')

def 保存静态图(fig, stem, title, subtitle):
    fig.set_layout_engine(None)
    fig.set_facecolor('#F7FAFD')
    fig.subplots_adjust(left=.14, right=.87, top=.77, bottom=.17)
    fig.text(.05, .93, title, fontsize=23, weight='bold', color=INK)
    fig.text(.05, .86, subtitle, fontsize=13, color='#52657A')
    fig.text(.05, .06, '模拟数据 · 教学演示', fontsize=13, color='#52657A')
    fig.text(.95, .06, '可以叫我才哥', fontsize=13, color='#52657A', ha='right')
    fig.savefig(OUT / f'{stem}.png', dpi=180, facecolor=fig.get_facecolor())
    fig.savefig(OUT / f'{stem}.svg', facecolor=fig.get_facecolor())
    plt.close(fig)
