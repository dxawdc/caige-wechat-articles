"""v1.0.0 | 2026-09-06 | 30 等高线图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('两个输入与模拟响应值', '输入 X（无量纲）', '输入 Y（无量纲）')
cf=ax.contourf(gx,gy,ZZ,levels=contour_levels,cmap=CMAP,vmin=0,vmax=100)
lines=ax.contour(gx,gy,ZZ,levels=[20,40,60,80],colors='#536D8D',linewidths=.6)
ax.clabel(lines,fmt='%d',fontsize=8)
mfig.colorbar(cf,ax=ax,label='模拟响应值')
ax.grid(False)

# Plotly：实际执行的完整绘图段
pfig = new_p('两个输入与模拟响应值', '输入 X（无量纲）', '输入 Y（无量纲）')
pfig.add_trace(go.Contour(x=gx,y=gy,z=ZZ,zmin=0,zmax=100,colorscale=SEQUENTIAL,
                         contours=dict(start=0,end=100,size=10,showlabels=True,coloring='fill'),
                         line=dict(width=.6,color='#536D8D'),colorbar=dict(title='响应值',thickness=14)))
pfig.update_xaxes(range=[0,10])
pfig.update_yaxes(range=[0,8],showgrid=False)

finish(30, '等高线图', mfig, pfig)
