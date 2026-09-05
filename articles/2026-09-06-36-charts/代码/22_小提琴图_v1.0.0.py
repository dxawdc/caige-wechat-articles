"""v1.0.0 | 2026-09-06 | 22 小提琴图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('三种方案的使用时长：小提琴图', '方案', '使用时长（分钟）')
for i, (a, d) in enumerate(zip(samples, violin_densities)):
    w = .38*d/d.max()
    ax.fill_betweenx(density_grid, i-w, i+w, facecolor='#D6E3F4', edgecolor=BLUE)
    ax.plot([i-.15,i+.15], [np.median(a)]*2, color=BLUE, linewidth=2)
ax.set(xticks=[0,1,2], xticklabels=group_names, xlim=(-.6,2.6), ylim=(0,85))

# Plotly：实际执行的完整绘图段
pfig = new_p('三种方案的使用时长：小提琴图', '方案', '使用时长（分钟）')
for i, (a, d) in enumerate(zip(samples, violin_densities)):
    w = .38*d/d.max()
    pfig.add_trace(go.Scatter(x=np.r_[i-w,(i+w)[::-1]], y=np.r_[density_grid,density_grid[::-1]],
                             fill='toself', fillcolor='#D6E3F4', line=dict(color=BLUE,width=1)))
    pfig.add_trace(go.Scatter(x=[i-.15,i+.15], y=[np.median(a)]*2, mode='lines',line_color=BLUE))
pfig.update_xaxes(tickvals=[0,1,2], ticktext=group_names, range=[-.6,2.6])
pfig.update_yaxes(range=[0,85])

finish(22, '小提琴图', mfig, pfig)
