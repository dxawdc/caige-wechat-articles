"""v1.0.0 | 2026-09-06 | 34 甘特图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('五项任务的模拟排期', '日期（2026 年 1 月）', '')
ax.barh(tasks['任务'],(tasks['结束']-tasks['开始']).dt.days,
        left=mdates.date2num(tasks['开始']),height=.55,color=BLUE)
ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax.set_xlim(mdates.date2num(pd.Timestamp('2026-01-01')),mdates.date2num(pd.Timestamp('2026-01-23')))
ax.invert_yaxis(); ax.grid(False)
ax.grid(axis='x',color='#E8ECF2')

# Plotly：实际执行的完整绘图段
pfig = new_p('五项任务的模拟排期', '日期（2026 年 1 月）', '')
timeline=px.timeline(tasks,x_start='开始',x_end='结束',y='任务',color_discrete_sequence=[BLUE])
pfig.add_traces(timeline.data)
pfig.update_xaxes(type='date',range=['2026-01-01','2026-01-23'],tickformat='%m-%d',dtick=3*86400000,showgrid=True)
pfig.update_yaxes(autorange='reversed',categoryorder='array',categoryarray=tasks['任务'],showgrid=False)
pfig.update_layout(margin_l=100)

finish(34, '甘特图', mfig, pfig)
