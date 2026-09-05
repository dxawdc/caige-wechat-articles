"""v1.0.0 | 2026-09-06 | 23 经验累积分布图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('使用时长的经验累积分布', '使用时长（分钟）', '累计比例')
sx = np.r_[0, np.sort(dist), 80]
sy = np.r_[0, np.arange(1,len(dist)+1)/len(dist), 1]
ax.step(sx, sy, where='post', color=BLUE, linewidth=2)
ax.set(xlim=(0,80), ylim=(0,1.02))
from matplotlib.ticker import PercentFormatter
ax.yaxis.set_major_formatter(PercentFormatter(1))

# Plotly：实际执行的完整绘图段
pfig = new_p('使用时长的经验累积分布', '使用时长（分钟）', '累计比例')
sx = np.r_[0, np.sort(dist), 80]
sy = np.r_[0, np.arange(1,len(dist)+1)/len(dist), 1]
pfig.add_trace(go.Scatter(x=sx, y=sy, line_shape='hv', line_color=BLUE))
pfig.update_xaxes(range=[0,80])
pfig.update_yaxes(range=[0,1.02], tickformat='.0%')

finish(23, '经验累积分布图', mfig, pfig)
