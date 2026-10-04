import pandas as pd
from 图表工具 import D, plt, RED, BLUE, finish
from 映射 import ORG_ZH

daily = pd.read_csv(D / '每日金牌.csv')
daily['date'] = pd.to_datetime(daily['date'])
dates = pd.date_range(daily.date.min(), daily.date.max())
matrix = daily.pivot(index='date', columns='noc', values='gold')
matrix = matrix.reindex(dates).fillna(0).cumsum()
standings = pd.read_csv(D / '国家地区奖牌榜.csv').set_index('noc')
for org in matrix.columns:
    assert matrix[org].iloc[-1] == standings.loc[org,'gold']
fig, ax = plt.subplots(figsize=(9,6))
fig.subplots_adjust(left=.1,right=.89,top=.8,bottom=.18)
for org, color in [('CHN',RED),('JPN',BLUE),('KOR','#578A6C')]:
    ax.plot(dates, matrix[org], color=color, linewidth=2.8, label=ORG_ZH[org])
    ax.text(dates[-1]+pd.Timedelta(hours=8),matrix[org].iloc[-1],
            str(int(matrix[org].iloc[-1])),va='center',color=color)
ticks = dates[::3]
ax.set_xticks(ticks,[d.strftime('%m-%d') for d in ticks])
ax.set_xlim(dates[0],dates[-1]+pd.Timedelta(days=1.5))
ax.set_ylim(0,185); ax.set_ylabel('累计金牌数（枚）')
ax.grid(alpha=.15); ax.legend(frameon=False,loc='upper left')
fig.text(.05,.94,'领先，是怎样累积起来的？',fontsize=25,weight='bold')
fig.text(.05,.875,'中国、日本、韩国｜按官方奖牌记录日期逐日累计',fontsize=12)
finish(fig,'06_累计金牌','赛事官方成绩系统 · 1条缺失日期据国家体育总局报道补核')
