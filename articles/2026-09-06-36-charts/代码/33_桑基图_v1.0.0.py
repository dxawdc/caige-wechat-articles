"""v1.0.0 | 2026-09-06 | 33 桑基图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('来源 → 汇总 → 去向（单位：人）')
Sankey(ax=ax,scale=.004,offset=.15,head_angle=120,format='%.0f',unit=' 人').add(
    flows=[60,55,45,-100,-60],labels=['搜索','推荐','社群','完成','流失'],
    orientations=[1,0,-1,0,-1],pathlengths=[.3,.35,.3,.35,.3],
    trunklength=1.1,facecolor=BLUE,edgecolor='white').finish()
ax.set_aspect('equal',adjustable='box'); ax.axis('off')

# Plotly：实际执行的完整绘图段
pfig = new_p('来源 → 汇总 → 去向（单位：人）')
pfig.add_trace(go.Sankey(arrangement='fixed',
    node=dict(label=['搜索 60','推荐 55','社群 45','汇总 160','完成 100','流失 60'],
              x=[.02,.02,.02,.5,.98,.98],y=[.08,.42,.77,.45,.25,.8],
              color=[BLUE,BLUE,BLUE,BLUE,BLUE,ORANGE],pad=22,thickness=16),
    link=dict(source=[0,1,2,3,3],target=[3,3,3,4,5],value=[60,55,45,100,60],
              color=['rgba(50,105,180,.25)']*4+['rgba(216,137,54,.3)'])))

finish(33, '桑基图', mfig, pfig)
