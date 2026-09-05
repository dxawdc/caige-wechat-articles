"""v1.0.0 | 2026-09-06 | 36 帕累托图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('问题数量与累计占比', '问题类型', '问题数（个）')
ax.bar(issues,issue_counts,color=BLUE,width=.6)
ax.set_ylim(0,60)
right=ax.twinx()
right.plot(issues,cumulative,color=ORANGE,marker='o',linewidth=2)
right.set(ylim=(0,105),ylabel='累计占比（%）')
right.grid(False)
right.spines['right'].set_visible(True)

# Plotly：实际执行的完整绘图段
pfig = new_p('问题数量与累计占比', '问题类型', '问题数（个）')
pfig.add_trace(go.Bar(x=issues,y=issue_counts,marker_color=BLUE,width=.6,name='问题数'))
pfig.add_trace(go.Scatter(x=issues,y=cumulative,mode='lines+markers',line_color=ORANGE,
                         yaxis='y2',name='累计占比'))
pfig.update_layout(margin_r=75,yaxis2=dict(title='累计占比（%）',overlaying='y',side='right',range=[0,105],showgrid=False))
pfig.update_yaxes(range=[0,60],selector=dict(anchor='x'))
pfig.layout.yaxis.range=[0,60]
pfig.layout.yaxis2.range=[0,105]
pfig.layout.yaxis2.tickvals=[0,20,40,60,80,100]

finish(36, '帕累托图', mfig, pfig)
