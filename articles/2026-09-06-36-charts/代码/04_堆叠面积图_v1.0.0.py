"""v1.0.0 | 2026-09-06 | 04 堆叠面积图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('订单来源随月份变化', '月份', '订单数（笔）')
ax.stackplot(months, trend_parts, labels=trend_names, colors=COLORS[:3], alpha=.85)
ax.legend(ncol=3, loc='upper left', fontsize=8)
ax.set(xticks=months, xlim=(1, 12), ylim=(0, 350))

# Plotly：实际执行的完整绘图段
pfig = new_p('订单来源随月份变化', '月份', '订单数（笔）')
for label, row, color in zip(trend_names, trend_parts, COLORS):
    pfig.add_trace(go.Scatter(x=months, y=row, name=label,
                             stackgroup='orders', line_color=color))
pfig.update_layout(showlegend=True)
pfig.update_xaxes(dtick=1, range=[1, 12])
pfig.update_yaxes(range=[0, 350])

finish(4, '堆叠面积图', mfig, pfig)
