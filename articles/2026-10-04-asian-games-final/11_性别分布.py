"""金牌和全部奖牌分别使用环形图，颜色固定对应选手性别。"""
from 图表工具 import *

df=pd.read_csv(D/'性别分布.csv')
df=df[(df.gold+df.medals)>0].reset_index(drop=True)
fig,axes=plt.subplots(2,1,figsize=(10,12))
fig.subplots_adjust(left=.08,right=.92,top=.84,bottom=.10,hspace=.27)
fig.suptitle('金牌与奖牌的获奖性别结构',x=.04,ha='left',y=.96,fontsize=22,fontweight='bold')
fig.text(.04,.90,'两组分别计算占比｜女性、男性在两个环中使用相同颜色',fontsize=12)
colors={'女':'#C5688D','男':BLUE,'未提供':SILVER}
for ax,column,title in zip(axes,['gold','medals'],['金牌','全部奖牌']):
    part=df[df[column]>0]
    labels=[f'{r["category"]}\n{r[column]:,}人次 · {r[column+"_pct"]:.1f}%'
            for r in part.to_dict('records')]
    ax.pie(part[column],labels=labels,
        colors=[colors[s] for s in part.category],
        startangle=90,counterclock=False,labeldistance=1.12,
        wedgeprops={'width':.29,'edgecolor':'white','linewidth':3},
        textprops={'fontsize':14,'color':INK})
    ax.text(0,.10,f'{int(part[column].sum()):,}',ha='center',va='center',fontsize=26,fontweight='bold')
    ax.text(0,-.20,'获奖人次',ha='center',va='center',fontsize=14,color=INK)
    ax.set_title(title,fontsize=19,pad=14,fontweight='bold')
    ax.set_xlim(-2.15,2.15);ax.set_ylim(-1.17,1.17)
finish(fig,'10_性别分布','来源：官方选手奖牌清单及简介/报名性别字段；一名选手每获一枚奖牌计1人次。')
