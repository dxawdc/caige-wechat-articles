"""按获奖人次比较金牌及全部奖牌的年龄结构；缺生日单列。"""
from 图表工具 import *

df=pd.read_csv(D/'年龄分布.csv')
df=df[(df.gold+df.medals)>0].reset_index(drop=True)
fig,axes=plt.subplots(2,1,figsize=(10,12))
fig.subplots_adjust(left=.22,right=.92,top=.84,bottom=.13,hspace=.48)
fig.suptitle('金牌与奖牌，集中在哪些年龄？',x=.04,ha='left',y=.96,fontsize=22,fontweight='bold')
fig.text(.04,.89,'比较占比，同时标出实际获奖人次',fontsize=12)
for ax,column,color,title in zip(axes,['gold','medals'],[GOLD,BLUE],['金牌获奖人次','全部奖牌获奖人次']):
    ax.barh(np.arange(len(df)),df[column+'_pct'],color=color,height=.60)
    for y,r in enumerate(df.to_dict('records')):
        ax.text(r[column+'_pct']+.6,y,f'{r[column]:,}人次\n{r[column+"_pct"]:.1f}%',va='center',fontsize=10)
    ax.set_title(f'{title}：{int(df[column].sum()):,}',fontsize=16,pad=15)
    ax.set_xlim(0,max(df.gold_pct.max(),df.medals_pct.max())+16)
    ax.set_xlabel('占对应获奖人次的比例（%）',fontsize=11)
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    ax.set_yticks(np.arange(len(df)),df.category,fontsize=15)
    ax.invert_yaxis()
fig.text(.04,.083,'年龄为开幕日2026-09-19周岁；一名选手多枚奖牌计多次，团体按实际获奖成员计数。',fontsize=10,color=INK)
finish(fig,'09_年龄分布','来源：官方选手奖牌清单与生日字段；未提供生日的获奖人次单列，保留在分母中。')
