"""v1.0.0 | 2026-09-06 | 05 区间带图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('订单中心值与模拟区间', '月份', '订单数（笔）')
ax.fill_between(months, orders-20, orders+20, color=BLUE, alpha=.18, label='模拟范围 ±20')
ax.plot(months, orders, color=BLUE, linewidth=2, label='中心值')
ax.legend(loc='upper left', fontsize=8)
ax.set(xticks=months, xlim=(1, 12), ylim=(0, 340))

# Plotly：实际执行的完整绘图段
pfig = new_p('订单中心值与模拟区间', '月份', '订单数（笔）')
pfig.add_trace(go.Scatter(x=months, y=orders-20, line_width=0, showlegend=False))
pfig.add_trace(go.Scatter(x=months, y=orders+20, line_width=0, fill='tonexty',
                         fillcolor='rgba(50,105,180,.18)', name='模拟范围 ±20'))
pfig.add_trace(go.Scatter(x=months, y=orders, line_color=BLUE, name='中心值'))
pfig.update_layout(showlegend=True)
pfig.update_xaxes(dtick=1, range=[1, 12])
pfig.update_yaxes(range=[0, 340])

finish(5, '区间带图', mfig, pfig)
