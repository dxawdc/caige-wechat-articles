"""v1.0.0 | 2026-09-06 | 18 漏斗图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('同批用户的转化漏斗', '人数（人）', '')
y = np.arange(5)
ax.barh(y, funnel_values, left=-funnel_values/2, color=BLUE, height=.7)
for i,v in enumerate(funnel_values):
    ax.text(0,i,f'{v:,} / {v/funnel_values[0]:.0%}',ha='center',va='center',color='white',fontsize=8)
ax.set(yticks=y, yticklabels=funnel_names, xlim=(-5500,5500), ylim=(4.6,-.6))
ax.set_xticks([])
ax.set_xlabel('条宽表示人数；百分比以首步为分母')
ax.grid(False)

# Plotly：实际执行的完整绘图段
pfig = new_p('同批用户的转化漏斗')
pfig.add_trace(go.Funnel(y=funnel_names, x=funnel_values, marker_color=BLUE,
                        textinfo='value+percent initial', textposition='inside',
                        textfont=dict(color='white',size=13), connector=dict(line_width=0,fillcolor='rgba(0,0,0,0)')))
pfig.update_layout(margin_l=115)
pfig.update_xaxes(showticklabels=False, title='条宽表示人数；百分比以首步为分母')

finish(18, '漏斗图', mfig, pfig)
