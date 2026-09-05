"""v1.0.0 | 2026-09-06 | 13 饼图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('订单来源占比')
ax.pie(values, labels=channels, autopct='%.1f%%', startangle=90, counterclock=False,
       colors=COLORS[:4], textprops={'fontsize': 9}, wedgeprops={'edgecolor':'white'})
ax.set_aspect('equal')

# Plotly：实际执行的完整绘图段
pfig = new_p('订单来源占比')
pfig.add_trace(go.Pie(labels=channels, values=values, sort=False, direction='clockwise',
                     rotation=0, marker_colors=COLORS[:4], textinfo='label+percent',
                     textposition='inside'))

finish(13, '饼图', mfig, pfig)
