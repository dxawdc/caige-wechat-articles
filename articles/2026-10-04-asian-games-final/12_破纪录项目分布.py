"""同时显示涉及纪录更新的小项数与打破/追平的纪录条目数。"""
from 图表工具 import *

df=pd.read_csv(D/'破纪录分项统计.csv').iloc[::-1]
fig,axes=plt.subplots(2,1,figsize=(10,12))
fig.subplots_adjust(left=.22,right=.93,top=.83,bottom=.15,hspace=.48)
fig.suptitle('哪些项目更新了比赛纪录？',x=.04,ha='left',y=.96,fontsize=22,fontweight='bold')
fig.text(.04,.89,'小项覆盖面与纪录更新次数，放在一起看',fontsize=12)
y=np.arange(len(df))
axes[0].barh(y,df.events,color=BLUE,height=.62)
for i,r in enumerate(df.itertuples()):axes[0].text(r.events+.35,i,str(r.events),va='center',fontsize=11)
axes[0].set_xlim(0,df.events.max()*1.25)
axes[0].set_title('涉及更新的赛事小项数',fontsize=16,pad=16)
axes[0].set_xlabel('小项数（按EvtKey去重）',fontsize=11)
axes[1].barh(y,df.broken,color=RED,height=.62,label='打破')
axes[1].barh(y,df.equalled,left=df.broken,color=GOLD,height=.62,label='追平')
for i,r in enumerate(df.itertuples()):axes[1].text(r.entries+2,i,str(r.entries),va='center',fontsize=11)
axes[1].set_xlim(0,df.entries.max()*1.25)
axes[1].set_title('官方纪录条目数',fontsize=16,pad=16)
axes[1].set_xlabel('按纪录类别记次',fontsize=11)
axes[1].legend(loc='lower right',frameon=False,fontsize=11)
for ax in axes:
    ax.set_yticks(y,df.sport_zh,fontsize=15)
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
fig.text(.04,.10,'同一次成绩可更新多类纪录；举重含抓举、挺举和总成绩，资格赛纪录按原类别保留。',fontsize=10)
finish(fig,'11_破纪录项目分布','来源：官方7个有实际成绩的分项纪录清单；包括世界、亚洲、赛会及相关纪录。')
