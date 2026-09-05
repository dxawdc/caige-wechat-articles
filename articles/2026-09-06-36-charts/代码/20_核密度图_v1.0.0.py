"""v1.0.0 | 2026-09-06 | 20 核密度图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('使用时长的核密度估计', '使用时长（分钟）', '概率密度（1/分钟）')
ax.plot(density_grid, density, color=BLUE, linewidth=2)
ax.fill_between(density_grid, density, color=BLUE, alpha=.2)
ax.set(xlim=(0,80), ylim=(0,.065))

# Plotly：实际执行的完整绘图段
pfig = new_p('使用时长的核密度估计', '使用时长（分钟）', '概率密度（1/分钟）')
pfig.add_trace(go.Scatter(x=density_grid, y=density, line_color=BLUE,
                         fill='tozeroy', fillcolor='rgba(50,105,180,.2)'))
pfig.update_xaxes(range=[0,80])
pfig.update_yaxes(range=[0,.065])

finish(20, '核密度图', mfig, pfig)
