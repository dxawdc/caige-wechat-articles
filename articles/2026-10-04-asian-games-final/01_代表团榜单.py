import numpy as np
import pandas as pd
from 图表工具 import D, plt, GOLD, SILVER, BRONZE, finish

df = pd.read_csv(D / '国家地区奖牌榜.csv')
df = df.sort_values(['gold', 'silver', 'bronze'], ascending=False)
top = df.head(15).reset_index(drop=True)
fig, ax = plt.subplots(figsize=(9, 9))
fig.subplots_adjust(left=.21, right=.94, top=.84, bottom=.13)
left = np.zeros(len(top))
for column, color, label in [('gold', GOLD, '金牌'),
                              ('silver', SILVER, '银牌'),
                              ('bronze', BRONZE, '铜牌')]:
    ax.barh(top.name_zh, top[column], left=left,
            height=.62, color=color, label=label)
    for i, value in enumerate(top[column]):
        if value >= 8:
            ax.text(left[i] + value/2, i, str(value),
                    ha='center', va='center', fontsize=11)
    left += top[column].to_numpy()
for i, total in enumerate(top.total):
    ax.text(total + 4, i, str(total), va='center', fontsize=12)
ax.invert_yaxis()
ax.set_xlim(0, 385)
ax.set_xlabel('奖牌数（枚）')
ax.grid(axis='x', alpha=.15); ax.set_axisbelow(True)
ax.legend(ncol=3, loc='lower right', frameon=False)
fig.text(.05, .94, '169金，中国队收官', fontsize=25, weight='bold')
fig.text(.05, .89, '官方金牌榜前15名｜按金、银、铜依次排序，条末为奖牌总数', fontsize=12)
finish(fig, '01_代表团奖牌榜', '2026-10-04收官快照 · 赛事官方成绩系统')
