"""v1.0.0 | 2026-09-06 | 07 条形图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('各渠道订单排名', '订单数（笔）', '渠道')
bars = ax.barh(channels, values, color=BLUE, height=.6)
ax.bar_label(bars, padding=5)
ax.invert_yaxis()
ax.grid(False)
ax.grid(axis='x', color='#E8ECF2')
ax.set_xlim(0, 500)

# Plotly：实际执行的完整绘图段
pfig = new_p('各渠道订单排名', '订单数（笔）', '渠道')
pfig.add_trace(go.Bar(x=values, y=channels, orientation='h', marker_color=BLUE,
                     text=values, textposition='outside', width=.6))
pfig.update_xaxes(range=[0, 500], showgrid=True)
pfig.update_yaxes(autorange='reversed', categoryorder='array', categoryarray=channels, showgrid=False)

finish(7, '条形图', mfig, pfig)
