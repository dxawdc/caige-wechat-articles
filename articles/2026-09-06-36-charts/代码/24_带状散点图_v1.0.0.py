"""v1.0.0 | 2026-09-06 | 24 带状散点图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('三种方案的原始样本', '方案（横向抖动无业务含义）', '使用时长（分钟）')
for i, a in enumerate(samples):
    ax.scatter(i+jitter[i], a, s=15, color=BLUE, alpha=.45, edgecolors='none')
ax.set(xticks=[0,1,2], xticklabels=group_names, xlim=(-.6,2.6), ylim=(0,85))

# Plotly：实际执行的完整绘图段
pfig = new_p('三种方案的原始样本', '方案（横向抖动无业务含义）', '使用时长（分钟）')
for i, a in enumerate(samples):
    pfig.add_trace(go.Scatter(x=i+jitter[i], y=a, mode='markers',name=group_names[i],
                             marker=dict(color=BLUE,size=5,opacity=.45)))
pfig.update_xaxes(tickvals=[0,1,2], ticktext=group_names, range=[-.6,2.6])
pfig.update_yaxes(range=[0,85])

finish(24, '带状散点图', mfig, pfig)
