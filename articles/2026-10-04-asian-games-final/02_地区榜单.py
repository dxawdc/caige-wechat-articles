import pandas as pd
from 图表工具 import D, plt, BLUE, RED, finish

df = pd.read_csv(D / '地区奖牌底表.csv')
special = [710000, 810000, 820000]
mainland = df[df.gold.notna() & ~df.adcode.isin(special)]
mainland = mainland.sort_values(['gold', 'adcode'], ascending=[False, True])
delegations = df[df.adcode.isin(special)].sort_values('gold', ascending=False)
fig, axes = plt.subplots(2, 1, figsize=(9, 10),
                         gridspec_kw={'height_ratios':[3, 1.15]})
fig.subplots_adjust(left=.15, right=.93, top=.82, bottom=.11, hspace=.5)
for ax, part, color in zip(axes, [mainland, delegations], [BLUE, RED]):
    ax.barh(part.region, part.gold, color=color, height=.58)
    for i, value in enumerate(part.gold):
        ax.text(value+.5, i, str(int(value)), va='center')
    ax.invert_yaxis(); ax.set_xlim(0, 39)
    ax.grid(axis='x', alpha=.15); ax.set_axisbelow(True)
axes[0].set_title('已核验的9个内地省份｜地方注册/培养项目贡献', loc='left', fontsize=13)
axes[1].set_title('港澳台单列｜中国香港、中国台北、中国澳门代表团', loc='left', fontsize=13)
axes[1].set_xlabel('金牌数 / 金牌项目贡献（各面板分别解释）')
fig.text(.05,.94,'金牌背后的地区贡献',fontsize=25,weight='bold')
fig.text(.05,.89,'已核验样本比较；内地另22个省级地区待核验，不构成全国最终排名',fontsize=12)
finish(fig,'02_地区金牌比较','2026-10-04 · 地方收官报道 + 赛事官方成绩系统')
