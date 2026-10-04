"""按选手绘制金银铜榜单，团体奖牌计入实际获奖成员。"""
from 图表工具 import *

df=pd.read_csv(D/'选手奖牌榜.csv').query('rank <= 12').iloc[::-1]
fig,ax=plt.subplots(figsize=(10,9))
fig.subplots_adjust(left=.31,right=.94,top=.85,bottom=.12)
fig.suptitle('谁是本届亚运会的多金王？',x=.04,ha='left',y=.97,fontsize=22,fontweight='bold')
fig.text(.04,.91,'选手金牌榜前12名（含并列）｜按金、银、铜排序',fontsize=12,color=INK)
left=np.zeros(len(df))
for col,color,label in [('gold',GOLD,'金牌'),('silver',SILVER,'银牌'),('bronze',BRONZE,'铜牌')]:
    ax.barh(np.arange(len(df)),df[col],left=left,color=color,height=.62,label=label)
    left+=df[col].to_numpy()
for y,r in enumerate(df.itertuples()):
    ax.text(r.total+.12,y,f'{r.gold}金 / 共{r.total}枚',va='center',fontsize=11)
ax.set_yticks(np.arange(len(df)),[f'{r.rank}  {r.name}\n{r.noc_zh} · {r.disciplines}' for r in df.itertuples()],fontsize=10)
ax.set_xlim(0,9.4)
ax.set_xticks(range(8))
ax.set_xlabel('选手奖牌数（枚）')
ax.grid(axis='x',alpha=.15); ax.set_axisbelow(True)
ax.legend(loc='lower right',frameon=False)
finish(fig,'08_选手金牌榜','来源：官方选手奖牌清单；个人及实际获奖团体成员均计入，姓名沿用官方拼写。')
