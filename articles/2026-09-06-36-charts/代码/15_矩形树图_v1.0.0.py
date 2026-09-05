"""v1.0.0 | 2026-09-06 | 15 矩形树图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('渠道预算构成（%）')
squarify.plot(sizes=tree_values, label=[f'{k}\n{v}%' for k,v in zip(tree_labels,tree_values)],
              color=COLORS, ax=ax, pad=True, text_kwargs={'color':'white','fontsize':11})
ax.axis('off')

# Plotly：实际执行的完整绘图段
pfig = new_p('渠道预算构成（%）')
pfig.add_trace(go.Treemap(labels=tree_labels, parents=['']*5, values=tree_values,
                         marker_colors=COLORS, texttemplate='%{label}<br>%{value}%',
                         textfont=dict(color='white', size=18), tiling_pad=3,
                         pathbar_visible=False))

finish(15, '矩形树图', mfig, pfig)
