"""v1.0.0 | 2026-09-06 | 10 百分比堆叠柱状图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('季度渠道占比', '季度', '占本季度订单（%）')
bottom = np.zeros(3)
for j, label in enumerate(channels):
    ax.bar(periods, percent[:, j], bottom=bottom, color=COLORS[j], label=label, width=.6)
    for i in range(3):
        ax.text(i, bottom[i]+percent[i,j]/2, f'{percent[i,j]:.1f}%', ha='center', va='center', color='white', fontsize=8)
    bottom += percent[:, j]
ax.set_ylim(0, 100)
ax.set_title('季度渠道占比', loc='left', pad=36)
ax.legend(ncol=4, loc='lower left', bbox_to_anchor=(0, 1.0), fontsize=8)

# Plotly：实际执行的完整绘图段
pfig = new_p('季度渠道占比', '季度', '占本季度订单（%）')
for j, label in enumerate(channels):
    pfig.add_trace(go.Bar(x=periods, y=percent[:, j], name=label, marker_color=COLORS[j],
                         text=[f'{v:.1f}%' for v in percent[:,j]], textposition='inside', textfont_color='white'))
pfig.update_layout(barmode='stack', showlegend=True)
pfig.update_yaxes(range=[0, 100])

finish(10, '百分比堆叠柱状图', mfig, pfig)
