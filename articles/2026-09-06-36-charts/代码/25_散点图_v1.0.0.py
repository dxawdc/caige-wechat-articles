"""v1.0.0 | 2026-09-06 | 25 散点图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('预算与订单的关系', '预算（千元）', '订单数（笔）')
ax.scatter(budget, sales, s=24, color=BLUE, alpha=.65, edgecolors='none')
ax.set(xlim=(0,110), ylim=(0,550))

# Plotly：实际执行的完整绘图段
pfig = new_p('预算与订单的关系', '预算（千元）', '订单数（笔）')
pfig.add_trace(go.Scatter(x=budget, y=sales, mode='markers',marker=dict(color=BLUE,size=7,opacity=.65)))
pfig.update_xaxes(range=[0,110])
pfig.update_yaxes(range=[0,550])

finish(25, '散点图', mfig, pfig)
