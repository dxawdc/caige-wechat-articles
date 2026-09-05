"""v1.0.0 | 2026-09-06 | 09 堆叠柱状图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('季度订单及来源构成', '季度', '订单数（笔）')
bottom = np.zeros(3)
for j, label in enumerate(channels):
    ax.bar(periods, matrix[:, j], bottom=bottom, color=COLORS[j], label=label, width=.6)
    bottom += matrix[:, j]
ax.legend(ncol=4, loc='upper left', fontsize=8)
ax.set_ylim(0, 580)

# Plotly：实际执行的完整绘图段
pfig = new_p('季度订单及来源构成', '季度', '订单数（笔）')
for j, label in enumerate(channels):
    pfig.add_trace(go.Bar(x=periods, y=matrix[:, j], name=label, marker_color=COLORS[j], width=.6))
pfig.update_layout(barmode='stack', showlegend=True)
pfig.update_yaxes(range=[0, 580])

finish(9, '堆叠柱状图', mfig, pfig)
