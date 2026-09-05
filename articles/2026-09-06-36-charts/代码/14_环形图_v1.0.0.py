"""v1.0.0 | 2026-09-06 | 14 环形图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('订单来源与总量')
ax.pie(values, labels=channels, autopct='%.1f%%', pctdistance=.8, startangle=90,
       counterclock=False, colors=COLORS[:4], wedgeprops={'width':.4,'edgecolor':'white'},
       textprops={'fontsize':9})
ax.text(0, 0, f'{values.sum():,}\n总订单', ha='center', va='center', fontsize=15)
ax.set_aspect('equal')

# Plotly：实际执行的完整绘图段
pfig = new_p('订单来源与总量')
pfig.add_trace(go.Pie(labels=channels, values=values, hole=.6, sort=False, direction='clockwise',
                     rotation=0, marker_colors=COLORS[:4], textinfo='label+percent'))
pfig.add_annotation(x=.5, y=.5, text=f'{values.sum():,}<br>总订单', showarrow=False, font_size=21)

finish(14, '环形图', mfig, pfig)
