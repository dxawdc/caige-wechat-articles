"""v1.0.0 | 2026-09-06 | 16 旭日图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('渠道预算层级（%）')
ax.pie([60,40], radius=.65, labels=['付费 60%','自有 40%'], labeldistance=.45,
       startangle=90, counterclock=False, colors=[BLUE,ORANGE],
       wedgeprops={'width':.65,'edgecolor':'white'}, textprops={'color':'white','fontsize':9})
ax.pie(tree_values, radius=1, labels=[f'{k} {v}%' for k,v in zip(tree_labels,tree_values)],
       labeldistance=1.05, startangle=90, counterclock=False,
       colors=[BLUE,BLUE,ORANGE,ORANGE,ORANGE],
       wedgeprops={'width':.35,'edgecolor':'white'}, textprops={'fontsize':8})
ax.set_aspect('equal')

# Plotly：实际执行的完整绘图段
pfig = new_p('渠道预算层级（%）')
pfig.add_trace(go.Sunburst(labels=['付费','自有']+tree_labels,
                         parents=['','','付费','付费','自有','自有','自有'],
                         values=[60,40]+tree_values, branchvalues='total', sort=False,
                         marker_colors=[BLUE,ORANGE,BLUE,BLUE,ORANGE,ORANGE,ORANGE],
                         texttemplate='%{label}<br>%{value}%', insidetextorientation='radial'))

finish(16, '旭日图', mfig, pfig)
