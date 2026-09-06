"""v1.0.0 | 2026-09-06 | 教学模拟案例：各渠道留存都涨了，整体为什么反而下降。"""
from pathlib import Path
import runpy
globals().update({k:v for k,v in runpy.run_path(str(Path(__file__).with_name("绘图工具_v1.0.0.py"))).items() if not k.startswith("__")})

df=pd.DataFrame([['旧版本','A',900,450],['旧版本','B',100,20],['新版本','A',100,60],['新版本','B',900,270]],columns=['version','channel','new_users','retained_d1'])
df['rate']=df.retained_d1/df.new_users
totals=df.groupby('version')[['new_users','retained_d1']].sum();totals['rate']=totals.retained_d1/totals.new_users
old=df[df.version.eq('旧版本')].set_index('channel');new=df[df.version.eq('新版本')].set_index('channel')
weights=old.new_users/old.new_users.sum();fixed=(new.rate*weights).sum()
within=fixed-totals.loc['旧版本','rate'];mix=totals.loc['新版本','rate']-fixed
assert totals.loc['旧版本','rate']==.47 and totals.loc['新版本','rate']==.33
assert (new.rate>old.rate).all() and np.isclose(fixed,.57)
assert np.isclose(within,.10) and np.isclose(mix,-.24) and np.isclose(within+mix,-.14)
csv(df,'渠道留存');csv(totals.reset_index(),'总体留存')
fig,ax=figure('每个渠道都涨，整体却从 47% 降到 33%','各版本新增 1000 人；D1 窗口均已成熟；条上为留存率')
x=np.arange(3);v0=[50,20,47];v1=[60,30,33]
ax.bar(x-.18,v0,.34,color=BLUE,label='旧版本');ax.bar(x+.18,v1,.34,color=ORANGE,label='新版本')
for delta,values in [(-.18,v0),(.18,v1)]:
    for i,v in enumerate(values):ax.text(i+delta,v+2,f'{v}%',ha='center',fontsize=11)
ax.set_xticks(x,['渠道A','渠道B','整体']);ax.set_ylim(0,80);ax.set_ylabel('D1 留存率（%）');ax.legend(loc='upper right',fontsize=11);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);save(fig,'01_分组与整体')
fig,ax=figure('改变的是：不同渠道进来了多少人','渠道 A 占比由 90% 降到 10%；每根柱合计 1000 人')
ax.barh(['旧版本','新版本'],[900,100],color=BLUE,label='渠道A');ax.barh(['旧版本','新版本'],[100,900],left=[900,100],color=ORANGE,label='渠道B')
for y,(a,b) in enumerate([(900,100),(100,900)]):
    ax.text(a/2,y,str(a),ha='center',va='center',color='white',weight='bold');ax.text(a+b/2,y,str(b),ha='center',va='center',color=INK,weight='bold')
ax.set_xlim(0,1000);ax.invert_yaxis();ax.set_xlabel('新增用户数（人）');ax.legend(loc='center',bbox_to_anchor=(.5,.5),ncol=2,fontsize=11,frameon=False);save(fig,'02_渠道结构')
result({'passed':True,'old_overall_pct':47,'new_overall_pct':33,'fixed_weight_new_pct':57,'within_effect_pp':10,'mix_effect_pp':-24,'net_change_pp':-14,'checks':5})
