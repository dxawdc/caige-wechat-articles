"""v1.0.0 | 2026-09-06 | 12 哑铃图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('渠道订单前后对比', '订单数（笔）', '渠道')
y = np.arange(4)
ax.hlines(y, before, after, color='#B9C4D2', linewidth=3)
ax.scatter(before, y, color=ORANGE, marker='o', s=65, label='前期', zorder=3)
ax.scatter(after, y, color=BLUE, marker='D', s=55, label='后期', zorder=3)
ax.set(yticks=y, yticklabels=channels, xlim=(0, 420), ylim=(3.5, -.5))
ax.legend(loc='lower right', fontsize=8)
ax.grid(False)

# Plotly：实际执行的完整绘图段
pfig = new_p('渠道订单前后对比', '订单数（笔）', '渠道')
xs, ys = [], []
for i in range(4):
    xs += [int(before[i]), int(after[i]), None]; ys += [i, i, None]
pfig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', line_color='#B9C4D2', showlegend=False))
for a, label, color, symbol in [(before,'前期',ORANGE,'circle'),(after,'后期',BLUE,'diamond')]:
    pfig.add_trace(go.Scatter(x=a, y=np.arange(4), mode='markers', name=label,
                             marker=dict(color=color, symbol=symbol, size=11)))
pfig.update_layout(showlegend=True)
pfig.update_xaxes(range=[0, 420])
pfig.update_yaxes(tickvals=list(range(4)), ticktext=channels, range=[3.5, -.5], showgrid=False)

finish(12, '哑铃图', mfig, pfig)
