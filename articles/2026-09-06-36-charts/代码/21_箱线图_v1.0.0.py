"""v1.0.0 | 2026-09-06 | 21 箱线图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('三种方案的使用时长：箱线图', '方案', '使用时长（分钟）')
ax.bxp(box_stats, positions=[0,1,2], widths=.5, patch_artist=True,
       boxprops={'facecolor':'#D6E3F4','edgecolor':BLUE}, medianprops={'color':BLUE,'linewidth':2},
       whiskerprops={'color':BLUE}, capprops={'color':BLUE}, flierprops={'marker': 'o','markersize':4})
ax.set_ylim(0,85)

# Plotly：实际执行的完整绘图段
pfig = new_p('三种方案的使用时长：箱线图', '方案', '使用时长（分钟）')
for i, s in enumerate(box_stats):
    pfig.add_trace(go.Box(x=[i], q1=[s['q1']], median=[s['med']], q3=[s['q3']],
                         lowerfence=[s['whislo']], upperfence=[s['whishi']],
                         width=.5, boxpoints=False, fillcolor='#D6E3F4', line_color=BLUE, name=s['label']))
    pfig.add_trace(go.Scatter(x=[i]*len(s['fliers']), y=s['fliers'], mode='markers', marker=dict(color=BLUE,size=6)))
pfig.update_xaxes(tickvals=[0,1,2], ticktext=group_names, range=[-.6,2.6])
pfig.update_yaxes(range=[0,85])

finish(21, '箱线图', mfig, pfig)
