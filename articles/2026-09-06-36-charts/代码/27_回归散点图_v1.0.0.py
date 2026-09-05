"""v1.0.0 | 2026-09-06 | 27 回归散点图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('预算与订单：线性拟合', '预算（千元）', '订单数（笔）')
ax.scatter(budget, sales, s=22, color=BLUE, alpha=.5, edgecolors='none')
ax.plot(fit_x, fit_y, color=ORANGE, linewidth=2, label=f'线性拟合 R²={rvalue**2:.3f}')
ax.legend(loc='upper left',fontsize=9)
ax.set(xlim=(0,110), ylim=(0,550))

# Plotly：实际执行的完整绘图段
pfig = new_p('预算与订单：线性拟合', '预算（千元）', '订单数（笔）')
pfig.add_trace(go.Scatter(x=budget, y=sales, mode='markers',marker=dict(color=BLUE,size=6,opacity=.5),showlegend=False))
pfig.add_trace(go.Scatter(x=fit_x,y=fit_y,mode='lines',line_color=ORANGE,name=f'线性拟合 R²={rvalue**2:.3f}'))
pfig.update_layout(showlegend=True)
pfig.update_xaxes(range=[0,110])
pfig.update_yaxes(range=[0,550])

finish(27, '回归散点图', mfig, pfig)
