"""v1.0.0 | 2026-09-06 | 35 K线图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('模拟 OHLC 价格', '日期（2026 年 1 月）', '模拟价格（元）')
x=mdates.date2num(ohlc_dates)
for i,(o,h,l,c) in enumerate(zip(open_prices,high_prices,low_prices,close_prices)):
    color=BLUE if c>=o else ORANGE
    ax.vlines(x[i],l,h,color=color,linewidth=1.2)
    ax.add_patch(Rectangle((x[i]-.3,min(o,c)),.6,max(abs(c-o),.01),facecolor=color,edgecolor=color))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax.set(xlim=(x[0]-1,x[-1]+1),ylim=(low_prices.min()-2,high_prices.max()+2))

# Plotly：实际执行的完整绘图段
pfig = new_p('模拟 OHLC 价格', '日期（2026 年 1 月）', '模拟价格（元）')
pfig.add_trace(go.Candlestick(x=ohlc_dates,open=open_prices,high=high_prices,low=low_prices,close=close_prices,
                             increasing=dict(line_color=BLUE,fillcolor=BLUE),
                             decreasing=dict(line_color=ORANGE,fillcolor=ORANGE)))
pfig.update_xaxes(rangeslider_visible=False,range=[ohlc_dates[0]-pd.Timedelta(days=1),ohlc_dates[-1]+pd.Timedelta(days=1)],
                 tickformat='%m-%d',dtick=2*86400000)
pfig.update_yaxes(range=[low_prices.min()-2,high_prices.max()+2])

finish(35, 'K线图', mfig, pfig)
