import pandas as pd
from 图表工具 import D, plt, BLUE, RED, finish

df = pd.read_csv(D / '中国分项目金牌.csv')
top = df.head(14)[['sport_zh','gold']].copy()
top.loc[len(top)] = [f'其余{len(df)-len(top)}个分项',df.iloc[len(top):].gold.sum()]
assert top.gold.sum() == 169
fig, ax = plt.subplots(figsize=(9,9))
fig.subplots_adjust(left=.24,right=.92,top=.83,bottom=.12)
colors = [RED if x=='游泳' else BLUE for x in top.sport_zh]
bars = ax.barh(top.sport_zh, top.gold, height=.6, color=colors)
ax.bar_label(bars, padding=5, fontsize=13)
ax.invert_yaxis(); ax.set_xlim(0,37)
ax.set_xlabel('金牌数（枚）'); ax.grid(axis='x',alpha=.15); ax.set_axisbelow(True)
fig.text(.05,.94,'169金，来自哪些项目？',fontsize=25,weight='bold')
fig.text(.05,.89,f'38个获金分项｜前14分项合计{int(df.head(14).gold.sum())}金，其余24分项合计{int(df.iloc[14:].gold.sum())}金',fontsize=12)
finish(fig,'05_中国金牌项目','2026-10-04 · 团体项目计1金 · 与官方CHN奖牌总数一致')
