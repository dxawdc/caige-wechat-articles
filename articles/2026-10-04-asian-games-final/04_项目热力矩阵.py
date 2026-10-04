import numpy as np
import pandas as pd
from 图表工具 import D, plt, finish
from 映射 import ORG_ZH, DISC_ZH

medals = pd.read_csv(D / '奖牌明细.csv')
gold = medals[medals.medal == 'ME_GOLD']
order = pd.read_csv(D / '国家地区奖牌榜.csv')
orgs = order.sort_values(['gold','silver','bronze'], ascending=False).head(10).noc.tolist()
sports = gold.groupby('discipline').size().sort_values(ascending=False).head(15).index.tolist()
matrix = gold.groupby(['noc','discipline']).size().unstack(fill_value=0)
matrix = matrix.reindex(index=orgs, columns=sports, fill_value=0)
matrix.to_csv(D / '代表团项目热力矩阵.csv', encoding='utf-8-sig')
fig, ax = plt.subplots(figsize=(11, 8))
fig.subplots_adjust(left=.16, right=.92, top=.82, bottom=.23)
image = ax.imshow(matrix, cmap='YlOrRd', vmin=0, vmax=matrix.to_numpy().max(), aspect='auto')
ax.set_yticks(range(len(orgs)), [ORG_ZH[x] for x in orgs])
ax.set_xticks(range(len(sports)), [DISC_ZH[x] for x in sports], rotation=45, ha='right')
for row, col in np.ndindex(matrix.shape):
    value = int(matrix.iat[row,col])
    ax.text(col,row,str(value),ha='center',va='center',fontsize=11,
            color='white' if value>=20 else '#33444E')
fig.colorbar(image,ax=ax,fraction=.035,pad=.025,label='金牌数')
fig.text(.05,.94,'谁在哪些项目上占优势？',fontsize=25,weight='bold')
fig.text(.05,.89,'金牌榜前10代表团 × 全赛会金牌数最多的15个分项',fontsize=12)
finish(fig,'04_代表团项目热力矩阵','完整奖牌明细聚合 · 0表示该代表团在该分项未获金牌')
