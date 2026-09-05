"""v1.0.0 | 2026-09-06 | 29 相关矩阵热力图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('五项指标的 Pearson 相关')
im=ax.imshow(corr,cmap=DCMAP,vmin=-1,vmax=1)
ax.set(xticks=range(5),xticklabels=metric_names,yticks=range(5),yticklabels=metric_names)
for i in range(5):
    for j in range(5):
        ax.text(j,i,f'{corr[i,j]:.2f}',ha='center',va='center',color='white' if abs(corr[i,j])>.6 else '#263445',fontsize=9)
mfig.colorbar(im,ax=ax,label='Pearson r')
ax.grid(False)

# Plotly：实际执行的完整绘图段
pfig = new_p('五项指标的 Pearson 相关')
pfig.add_trace(go.Heatmap(x=metric_names,y=metric_names,z=corr,zmin=-1,zmax=1,
                         colorscale=DIVERGING,colorbar=dict(title='Pearson r',thickness=14)))
for i in range(5):
    for j in range(5):
        pfig.add_annotation(x=metric_names[j],y=metric_names[i],text=f'{corr[i,j]:.2f}',showarrow=False,
                            font=dict(size=13,color='white' if abs(corr[i,j])>.6 else '#263445'))
pfig.update_yaxes(autorange='reversed',showgrid=False)

finish(29, '相关矩阵热力图', mfig, pfig)
