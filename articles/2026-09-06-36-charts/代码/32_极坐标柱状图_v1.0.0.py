"""v1.0.0 | 2026-09-06 | 32 极坐标柱状图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('一天内各时段访问量',polar=True)
theta=hours/24*2*np.pi
ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
ax.bar(theta,hour_values,width=2*np.pi/8*.8,color=BLUE)
ax.set(xticks=theta,xticklabels=[f'{h:02d}时' for h in hours],ylim=(0,60),yticks=[20,40,60])
ax.set_xlabel('径向刻度：访问次数',labelpad=15)

# Plotly：实际执行的完整绘图段
pfig = new_p('一天内各时段访问量')
pfig.add_trace(go.Barpolar(r=hour_values,theta=hours/24*360,width=36,marker_color=BLUE))
pfig.update_layout(polar=dict(radialaxis=dict(range=[0,60],dtick=20),
                     angularaxis=dict(rotation=90,direction='clockwise',tickvals=hours/24*360,
                                      ticktext=[f'{h:02d}时' for h in hours])))
pfig.add_annotation(x=.5,y=-.12,xref='paper',yref='paper',text='径向刻度：访问次数',showarrow=False)

finish(32, '极坐标柱状图', mfig, pfig)
