"""以中国纪录分布为主，补充全赛会对照；两个面板使用独立数轴。"""
from 图表工具 import *

china=pd.read_csv(D/'中国破纪录分项统计.csv').iloc[::-1]
all_records=pd.read_csv(D/'破纪录分项统计.csv').set_index('discipline').loc[china.discipline].reset_index()
fig,axes=plt.subplots(2,1,figsize=(10,12))
fig.subplots_adjust(left=.22,right=.93,top=.82,bottom=.16,hspace=.54)
fig.suptitle('中国队的纪录突破，集中在哪？',x=.04,ha='left',y=.96,fontsize=22,fontweight='bold')
fig.text(.04,.90,'上：中国代表团  ·  下：全赛会对照  ·  数量均为纪录条目',fontsize=12)

for ax,df,label in zip(axes,[china,all_records],['中国代表团','全赛会']):
    y=np.arange(len(df))
    ax.barh(y,df.broken,color=RED,height=.62,label='打破')
    ax.barh(y,df.equalled,left=df.broken,color=GOLD,height=.62,label='追平')
    for i,r in enumerate(df.itertuples()):
        ax.text(r.entries+df.entries.max()*.015,i,str(r.entries),va='center',fontsize=11)
    ax.set_xlim(0,df.entries.max()*1.22)
    ax.set_title(f'{label}：{df.entries.sum()}条（打破{df.broken.sum()} / 追平{df.equalled.sum()}）',fontsize=16,pad=18)
    ax.set_xlabel('纪录条目数',fontsize=11)
    ax.set_yticks(y,df.sport_zh,fontsize=15)
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
axes[0].legend(loc='lower right',frameon=False,fontsize=11)
fig.text(.04,.10,'两图使用独立数轴，比较具体数量请读数字；中国条目属于全赛会条目的一部分。',fontsize=10)
fig.text(.04,.07,'一次成绩可更新多类纪录；举重含抓举、挺举、总成绩，资格赛类别按原清单保留。',fontsize=10)
finish(fig,'11_破纪录项目分布','来源：官方7个有实际成绩的分项纪录清单；包括世界、亚洲、赛会及相关纪录。')
