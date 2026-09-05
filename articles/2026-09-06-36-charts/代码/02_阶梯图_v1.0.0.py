"""v1.0.0 | 2026-09-06 | 02 阶梯图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('月度配置容量', '月份', '容量（个）')
ax.step(months, orders, where='post', color=BLUE, linewidth=2)
ax.plot(months, orders, 'o', color=BLUE)
ax.set(xticks=months, xlim=(.5, 12.5), ylim=(0, 320))

# Plotly：实际执行的完整绘图段
pfig = new_p('月度配置容量', '月份', '容量（个）')
pfig.add_trace(go.Scatter(x=months, y=orders, mode='lines+markers',
                         line_shape='hv', line_color=BLUE))
pfig.update_xaxes(dtick=1, range=[.5, 12.5])
pfig.update_yaxes(range=[0, 320])

finish(2, '阶梯图', mfig, pfig)
