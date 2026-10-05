"""从图1同一份16只ETF记录重绘横版封面，独立输出，保留正文图。"""
from pathlib import Path
from hashlib import sha256
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image

ROOT = Path(__file__).resolve().parent
INK, BLUE, MUTED, GRID = '#172F43', '#3B7196', '#71818E', '#E5EBF0'


def main():
    protected = [ROOT/'文章.md', ROOT/'文章.html', ROOT/'图表/最大回撤与修复总览.png', ROOT/'图表/最大回撤与修复总览.svg']
    before = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()}
    table = pd.read_csv(ROOT/'数据/最大回撤与修复.csv', dtype={'code': str}).sort_values('max_drawdown_pct').reset_index(drop=True)
    assert len(table) == 16 and (table.status == '尚未修复').all()
    assert table.recovery_days.isna().all()
    font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
    plt.rcParams.update({'font.family': 'Microsoft YaHei', 'axes.unicode_minus': False, 'svg.fonttype': 'none'})
    # 1800×766高清画布，所有文字与柱形按横版比例重新布局。
    fig, axes = plt.subplots(1, 2, figsize=(12, 766/150), dpi=150,
                             gridspec_kw={'width_ratios': [1, 1.5]}, facecolor='white')
    fig.subplots_adjust(left=.125, right=.96, top=.735, bottom=.14, wspace=.20)
    y = np.arange(len(table))
    for ax in axes:
        ax.spines[['top', 'right']].set_visible(False)
        ax.spines[['left', 'bottom']].set_color('#BCC8D1')
        ax.tick_params(colors=MUTED, length=0, pad=4, labelsize=8)
        ax.grid(axis='x', color=GRID, lw=.6)
        ax.set_axisbelow(True)
        ax.set_ylim(len(table)-.4, -.8)
    axes[0].barh(y, -table.max_drawdown_pct, color=BLUE, height=.62)
    axes[0].set_yticks(y, table['name'], fontsize=8.2)
    axes[0].set_xlim(0, 49)
    axes[0].set_xticks([0, 20, 40])
    axes[0].set_title('最大回撤幅度 / %', loc='left', fontsize=10, color=INK, pad=11)
    axes[1].set_yticks(y, [])
    axes[1].barh(y, table.decline_days, color=BLUE, height=.62)
    axes[1].barh(y, table.observed_after_trough_days, left=table.decline_days,
                 color='#DCE4E9', edgecolor='#7E929F', hatch='///', height=.62, lw=.5)
    axes[1].set_xlim(0, 315)
    axes[1].set_xticks([0, 100, 200, 300])
    axes[1].set_title('下跌 + 低点后已观察 / 交易日', loc='left', fontsize=10, color=INK, pad=11)
    labels = []
    for i, row in table.iterrows():
        labels.append(axes[0].text(-row.max_drawdown_pct+.6, i, f'{row.max_drawdown_pct:.1f}%',
                                   va='center', color=INK, fontsize=8.1))
        duration = row.decline_days+row.observed_after_trough_days
        labels.append(axes[1].text(duration+3, i, f'{int(row.decline_days)} + {int(row.observed_after_trough_days)}',
                                   va='center', color=INK, fontsize=8.1))
    fig.text(.035, .925, 'ETF跌下去以后，多久才能涨回来？', fontsize=23, weight='bold', color=INK)
    fig.text(.037, .845, '16只代表ETF  ·  2025-09-30—2026-09-30  ·  最大回撤与修复时间', fontsize=10, color=MUTED)
    fig.text(.037, .04, '16次窗口最大回撤均尚未修复；斜纹表示已观察时间。', fontsize=8.5, color=MUTED)
    fig.text(.963, .04, '可以叫我才哥', ha='right', fontsize=9.5, color=INK)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    assert all(fig.bbox.contains(t.get_window_extent(renderer).x1, t.get_window_extent(renderer).y1) for t in labels)
    png, svg = ROOT/'图表/封面图.png', ROOT/'图表/封面图.svg'
    fig.savefig(png, dpi=150, facecolor='white')
    fig.savefig(svg, facecolor='white')
    plt.close(fig)
    with Image.open(png) as im:
        assert im.size == (1800, 766)
    after = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()}
    assert before == after
    report = {'status': 'passed', 'cover': '图表/封面图.png', 'size': [1800, 766],
              'source': '数据/最大回撤与修复.csv', 'entities': 16, 'unrepaired_events': 16,
              'original_figure_and_article_preserved': True, 'protected_sha256': after}
    (ROOT/'验收_封面.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    metadata = ROOT/'文章元数据.json'
    if metadata.is_file():
        meta = json.loads(metadata.read_text(encoding='utf-8'))
        meta['cover'] = {'path': '图表/封面图.png', 'svg': '图表/封面图.svg', 'size': [1800, 766],
                         'source_figure': '图表/最大回撤与修复总览.png', 'layout': '独立重绘横版封面'}
        metadata.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'protected_sha256'}, ensure_ascii=True))


if __name__ == '__main__':
    main()
