"""按选手性别比较金牌及全部奖牌的获奖人次结构。"""
from 图表工具 import *

df=pd.read_csv(D/'性别分布.csv')
df=df[(df.gold+df.medals)>0].reset_index(drop=True)
fig,ax=plt.subplots(figsize=(10,7))
fig.subplots_adjust(left=.15,right=.89,top=.78,bottom=.23)
fig.suptitle('金牌与奖牌的获奖性别结构',x=.04,ha='left',y=.96,fontsize=22,fontweight='bold')
fig.text(.04,.89,'按实际获奖选手性别统计；混合项目拆到获奖成员',fontsize=12)
y=np.arange(len(df))
for column,offset,color,label in [('gold',-.18,GOLD,'金牌获奖人次'),('medals',.18,BLUE,'全部奖牌获奖人次')]:
    ax.barh(y+offset,df[column+'_pct'],height=.30,color=color,label=label)
    for i,r in enumerate(df.to_dict('records')):
        ax.text(r[column+'_pct']+.6,i+offset,f'{r[column]:,}人次 · {r[column+"_pct"]:.1f}%',va='center',fontsize=11)
ax.set_yticks(y,df.category,fontsize=16)
ax.invert_yaxis();ax.set_xlim(0,max(df.gold_pct.max(),df.medals_pct.max())+24)
ax.set_xlabel('占对应获奖人次的比例（%）')
ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
ax.legend(loc='upper left',bbox_to_anchor=(0,-.17),ncol=2,frameon=False,fontsize=11)
finish(fig,'10_性别分布','来源：官方选手奖牌清单及简介/报名性别字段；一名选手每获一枚奖牌计1人次。')
