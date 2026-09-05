"""v1.0.0 | 2026-09-06 | 08 分组柱状图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('季度与渠道订单对比', '季度', '订单数（笔）')
x = np.arange(3)
for j, label in enumerate(channels):
    ax.bar(x+(j-1.5)*.18, matrix[:, j], width=.18, color=COLORS[j], label=label)
ax.set(xticks=x, xticklabels=periods, ylim=(0, 205))
ax.legend(ncol=4, loc='upper left', fontsize=8)

# Plotly：实际执行的完整绘图段
pfig = new_p('季度与渠道订单对比', '季度', '订单数（笔）')
for j, label in enumerate(channels):
    pfig.add_trace(go.Bar(x=periods, y=matrix[:, j], name=label, marker_color=COLORS[j]))
pfig.update_layout(barmode='group', showlegend=True)
pfig.update_yaxes(range=[0, 205])

finish(8, '分组柱状图', mfig, pfig)
