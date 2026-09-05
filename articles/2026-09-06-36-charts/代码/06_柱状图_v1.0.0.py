"""v1.0.0 | 2026-09-06 | 06 柱状图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('各渠道订单', '渠道', '订单数（笔）')
bars = ax.bar(channels, values, color=BLUE, width=.6)
ax.bar_label(bars, padding=4)
ax.set_ylim(0, 500)

# Plotly：实际执行的完整绘图段
pfig = new_p('各渠道订单', '渠道', '订单数（笔）')
pfig.add_trace(go.Bar(x=channels, y=values, marker_color=BLUE,
                     text=values, textposition='outside', width=.6))
pfig.update_yaxes(range=[0, 500])

finish(6, '柱状图', mfig, pfig)
