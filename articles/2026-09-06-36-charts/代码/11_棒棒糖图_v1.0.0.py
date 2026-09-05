"""v1.0.0 | 2026-09-06 | 11 棒棒糖图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('各渠道订单：棒棒糖表达', '订单数（笔）', '渠道')
y = np.arange(4)
ax.hlines(y, 0, values, color=BLUE, linewidth=2)
ax.scatter(values, y, s=70, color=BLUE, zorder=3)
ax.set(yticks=y, yticklabels=channels, xlim=(0, 500), ylim=(3.5, -.5))
ax.grid(False)

# Plotly：实际执行的完整绘图段
pfig = new_p('各渠道订单：棒棒糖表达', '订单数（笔）', '渠道')
xs, ys = [], []
for i, value in enumerate(values):
    xs += [0, int(value), None]; ys += [i, i, None]
pfig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', line_color=BLUE))
pfig.add_trace(go.Scatter(x=values, y=np.arange(4), mode='markers', marker=dict(color=BLUE, size=11)))
pfig.update_xaxes(range=[0, 500])
pfig.update_yaxes(tickvals=list(range(4)), ticktext=channels, range=[3.5, -.5], showgrid=False)

finish(11, '棒棒糖图', mfig, pfig)
