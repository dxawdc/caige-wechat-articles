"""v1.0.0 | 2026-09-06 | 17 瀑布图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('期初到期末的金额变化', '项目', '金额（万元）')
labels = ['期初','新增','退款','复购','成本','期末']
delta = [30,-15,20,-10]
level = 100
ax.bar(0, level, color='#778392', width=.6)
for i, change in enumerate(delta, 1):
    ax.plot([i-1+.3,i-.3], [level,level], color='#AAB4C0', linewidth=1)
    ax.bar(i, abs(change), bottom=min(level,level+change), color=BLUE if change>0 else ORANGE, width=.6)
    ax.text(i, max(level,level+change)+4, f'{change:+}', ha='center', fontsize=9)
    level += change
ax.plot([4.3,4.7],[level,level],color='#AAB4C0',linewidth=1)
ax.bar(5, level, color='#778392', width=.6)
ax.set(xticks=range(6), xticklabels=labels, ylim=(0,160))

# Plotly：实际执行的完整绘图段
pfig = new_p('期初到期末的金额变化', '项目', '金额（万元）')
pfig.add_trace(go.Waterfall(x=['期初','新增','退款','复购','成本','期末'],
                          y=[100,30,-15,20,-10,0], measure=['absolute']+['relative']*4+['total'],
                          text=['100','+30','-15','+20','-10','125'], textposition='outside',
                          increasing_marker_color=BLUE, decreasing_marker_color=ORANGE,
                          totals_marker_color='#778392', connector_line_color='#AAB4C0'))
pfig.update_yaxes(range=[0,160])

finish(17, '瀑布图', mfig, pfig)
