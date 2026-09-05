"""v1.0.0 | 2026-09-06 | 19 直方图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('使用时长分布：每箱 5 分钟', '使用时长（分钟）', '样本数（个）')
ax.bar(bins[:-1], hist_counts, width=np.diff(bins), align='edge', color=BLUE, edgecolor='white')
ax.set(xlim=(0,80), ylim=(0,55))

# Plotly：实际执行的完整绘图段
pfig = new_p('使用时长分布：每箱 5 分钟', '使用时长（分钟）', '样本数（个）')
pfig.add_trace(go.Bar(x=(bins[:-1]+bins[1:])/2, y=hist_counts,
                     width=np.diff(bins), marker=dict(color=BLUE,line=dict(color='white',width=1))))
pfig.update_xaxes(range=[0,80])
pfig.update_yaxes(range=[0,55])

finish(19, '直方图', mfig, pfig)
