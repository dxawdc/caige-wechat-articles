"""v1.0.0 | 2026-09-06 | 03 面积图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('月度订单规模', '月份', '订单数（笔）')
ax.fill_between(months, orders, color=BLUE, alpha=.25)
ax.plot(months, orders, color=BLUE, linewidth=2)
ax.set(xticks=months, xlim=(1, 12), ylim=(0, 320))

# Plotly：实际执行的完整绘图段
pfig = new_p('月度订单规模', '月份', '订单数（笔）')
pfig.add_trace(go.Scatter(x=months, y=orders, fill='tozeroy',
                         fillcolor='rgba(50,105,180,.25)', line_color=BLUE))
pfig.update_xaxes(dtick=1, range=[1, 12])
pfig.update_yaxes(range=[0, 320])

finish(3, '面积图', mfig, pfig)
