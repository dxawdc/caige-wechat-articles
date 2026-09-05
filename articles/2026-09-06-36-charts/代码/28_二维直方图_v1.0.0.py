"""v1.0.0 | 2026-09-06 | 28 二维直方图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('预算与订单的二维频数', '预算（千元）', '订单数（笔）')
mesh = ax.pcolormesh(xedges,yedges,hist2d.T,cmap=CMAP,vmin=0,vmax=hist2d.max(),shading='flat')
mfig.colorbar(mesh,ax=ax,label='样本数（个）')
ax.set(xlim=(0,110),ylim=(0,550))
ax.grid(False)

# Plotly：实际执行的完整绘图段
pfig = new_p('预算与订单的二维频数', '预算（千元）', '订单数（笔）')
pfig.add_trace(go.Heatmap(x=(xedges[:-1]+xedges[1:])/2,y=(yedges[:-1]+yedges[1:])/2,
                         z=hist2d.T,zmin=0,zmax=hist2d.max(),colorscale=SEQUENTIAL,
                         colorbar=dict(title='样本数',thickness=14)))
pfig.update_xaxes(range=[0,110])
pfig.update_yaxes(range=[0,550],showgrid=False)

finish(28, '二维直方图', mfig, pfig)
