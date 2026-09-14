"""v1.0.0 | Publication charts, reproducible from aggregate JSON without raw reviews."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import PercentFormatter

ROOT=Path(__file__).parent;OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
R=json.loads((OUT/'analysis_v1.0.0.json').read_text(encoding='utf8'))
C=json.loads((OUT/'collection_summary_v1.0.0.json').read_text(encoding='utf8'))
GREEN='#168B78';TEAL='#46B8AF';RED='#DB7462';GOLD='#DAB25F';INK='#183C3A';MUTED='#647C7A';BG='#F5F7F2';GRID='#DDE7DF'
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,
 'font.size':16,'axes.labelsize':16,'xtick.labelsize':14,'ytick.labelsize':16,
 'axes.facecolor':BG,'figure.facecolor':BG,'text.color':INK,'axes.labelcolor':MUTED,
 'xtick.color':MUTED,'ytick.color':INK,'svg.fonttype':'path','savefig.dpi':180})

def frame(title,subtitle,height=7.5):
    f=plt.figure(figsize=(9,height));f.text(.055,.945,title,fontsize=24,weight='bold',va='top')
    f.text(.055,.885,subtitle,fontsize=13,color=MUTED,va='top',linespacing=1.6)
    f.text(.055,.025,'可以叫我才哥  ·  TapTap 玩家评价分析',fontsize=12,color=MUTED)
    f.text(.945,.025,'采集 2026.09.14',fontsize=11,color=MUTED,ha='right')
    return f

def clean(ax,grid='x'):
    for s in ax.spines.values():s.set_visible(False)
    ax.tick_params(length=0,pad=9)
    ax.set_axisbelow(True)
    if grid:ax.grid(axis=grid,color=GRID,linewidth=.8)

def save(f,name):
    f.savefig(OUT/(name+'_v1.0.0.png'),facecolor=BG)
    f.savefig(OUT/(name+'_v1.0.0.svg'),facecolor=BG)
    plt.close(f)

# 01: five-star distribution, counts and denominator explicitly visible.
f=frame('星级分布：均分之外的评价结构',f"去重后 {C['n']:,} 条公开评价；4–5星为本文的高星口径")
ax=f.add_axes([.12,.27,.72,.53]);stars=[1,2,3,4,5];values=[R['rating_counts'].get(str(s),0) for s in stars]
ax.barh(stars,values,color=[RED,'#E4A393',GOLD,'#79BCA4',GREEN],height=.58)
for s,n in zip(stars,values):ax.text(n+max(values)*.025,s,f'{n:,}  ·  {n/C["n"]:.1%}',va='center',fontsize=17)
ax.set_yticks(stars,[f'{s} 星' for s in stars]);ax.set_xlim(0,max(values)*1.43);ax.set_xlabel('评价条数');clean(ax)
f.text(.12,.10,f"高星 {R['overall']['high_rate']:.1%}     中星 {R['overall']['middle']/C['n']:.1%}     低星 {R['overall']['low_rate']:.1%}",fontsize=17,weight='bold')
save(f,'01_rating_distribution')

# 02: daily count and daily high/low proportions; never show a zero rate for empty dates.
f=frame('首发附近，评价量与星级怎样变？','按当前可见版本时间归日；9月14日尚未完整\n9月10日含开服前7小时，精确前后比较见下一图',9)
days=pd.date_range('2026-08-27','2026-09-14');ns=np.array([R['daily'].get(str(t.date()),{}).get('n',0) for t in days]);x=np.arange(len(days))
ax=f.add_axes([.12,.55,.82,.24]);ax.bar(x,ns,color=[GREEN if t.day>=10 and t.month==9 else '#9BCABB' for t in days],width=.68)
ax.axvline(14,ls='--',color=RED,lw=1.5);ax.text(14.2,max(ns)*.86,'9/10 开服日',fontsize=13,color=RED)
ax.set_ylabel('评价条数');ax.set_xticks([]);ax.set_xlim(-.6,len(days)-.4);clean(ax,'y')
ax=f.add_axes([.12,.19,.82,.27]);
for key,label,color in [('high_rate','4–5星',GREEN),('low_rate','1–2星',RED)]:
    y=[R['daily'].get(str(t.date()),{}).get(key,np.nan) for t in days];ax.plot(x,y,'o-',lw=2.2,ms=5,label=label,color=color)
ax.axvline(14,ls='--',color=RED,lw=1.3);ax.set_ylim(-.03,1.06);ax.set_xlim(-.6,len(days)-.4);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_ylabel('当日占比')
ticks=[0,4,8,12,14,16,18];ax.set_xticks(ticks,[days[i].strftime('%m/%d') for i in ticks],rotation=30)
ax.legend(loc='upper left',bbox_to_anchor=(0,1.27),ncol=2,frameon=False,fontsize=14);clean(ax,'y')
save(f,'02_daily_trend')

# 03: equal-duration windows and conditional Wilson intervals.
f=frame('同为96小时：首发前后对照','北京时间 9/10 07:00 为界；按可见版本时间划分\n线段为95% Wilson区间，不消除平台选择偏差',8)
ax=f.add_axes([.27,.25,.65,.49]);labels=list(R['matched']);ys=[1,0]
for i,label in enumerate(labels):
    m=R['matched'][label]
    for off,key,col in [(.11,'high',GREEN),(-.11,'low',RED)]:
        rate=m[key+'_rate'];lo,hi=m[key+'_ci'];ax.errorbar(rate,ys[i]+off,xerr=[[rate-lo],[hi-rate]],fmt='o',color=col,markersize=10,capsize=5,lw=2)
        ax.text(hi+.025,ys[i]+off,f'{rate:.1%}',va='center',fontsize=18,color=col)
ax.set_yticks(ys,[f'{s}\nn={R["matched"][s]["n"]:,}' for s in labels]);ax.set_xlim(0,1.09);ax.set_ylim(-.5,1.5);ax.xaxis.set_major_formatter(PercentFormatter(1));clean(ax)
f.text(.18,.14,'● 4–5星',color=GREEN,fontsize=17);f.text(.5,.14,'● 1–2星',color=RED,fontsize=17)
save(f,'03_launch_comparison')

# 04: stage labels, not inferred true playing status.
f=frame('“玩过”与“期待”，分开看','平台展示状态；“期待”不等于证实未玩过\n没有游玩时长，也不能归入“没玩过”',8)
ax=f.add_axes([.20,.24,.74,.48]);items=sorted(R['stages'].items(),key=lambda p:p[1]['n'],reverse=True)
for i,(label,m) in enumerate(items):
    left=0
    for key,col in [('high',GREEN),('middle',GOLD),('low',RED)]:
        width=m[key]/m['n'];ax.barh(i,width,left=left,color=col,height=.48)
        if width>.11:ax.text(left+width/2,i,f'{width:.0%}',va='center',ha='center',color='white',fontsize=16,weight='bold')
        left+=width
ax.set_yticks(range(len(items)),[f'{k}\nn={m["n"]:,}' for k,m in items]);ax.invert_yaxis();ax.set_xlim(0,1);ax.xaxis.set_major_formatter(PercentFormatter(1));clean(ax)
for x,key,color in [(.20,'4–5星',GREEN),(.43,'3星',GOLD),(.60,'1–2星',RED)]:f.text(x,.13,'● '+key,color=color,fontsize=16)
save(f,'04_player_status')

# 05: playing time availability and selection bias.
f=frame('展示了游玩时长的评价，怎样打分？',f"仅 {C['played_hours_available']:,}/{C['n']:,} 条展示评价时游玩时长\n时长来自平台记录，缺失不补零；区间为95% Wilson",8)
ax=f.add_axes([.25,.21,.66,.55]);groups=['不足1小时','1–5小时','5–20小时','20小时及以上','未展示评价时长']
for i,g in enumerate(groups):
    m=R['hours'].get(g)
    if not m:continue
    p=m['high_rate'];lo,hi=m['high_ci'];color=GREEN if i<4 else MUTED
    ax.errorbar(p,i,xerr=[[p-lo],[hi-p]],fmt='o',color=color,ms=9,capsize=4,lw=2)
    ax.text(min(hi+.025,.94),i,f'{p:.1%}',va='center',fontsize=16,color=color)
ax.set_yticks(range(5),[g+'\nn='+str(R['hours'].get(g,{}).get('n',0)) for g in groups]);ax.invert_yaxis();ax.set_xlim(0,1.13);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.set_xlabel('组内4–5星占比');clean(ax)
save(f,'05_playtime')

# 06: multi-label prevalence; no topic sentiment claim.
f=frame('玩家关注点：哪些主题被提得最多？',f"主题词典匹配；每条评价对同一主题只计一次\n一条可命中多个主题，分母均为 {C['n']:,} 条评价",10)
ax=f.add_axes([.26,.16,.60,.64]);items=sorted(R['themes'].items(),key=lambda p:p[1]['mentions'],reverse=True)
ys=np.arange(len(items));ax.barh(ys,[m['mention_rate'] for _,m in items],color=[GREEN if i<3 else '#94C5B5' for i in ys],height=.6)
for i,(_,m) in enumerate(items):ax.text(m['mention_rate']+.01,i,f'{m["mention_rate"]:.1%} · {m["mentions"]}',va='center',fontsize=15)
ax.set_yticks(ys,[k for k,_ in items]);ax.invert_yaxis();ax.set_xlim(0,max(m['mention_rate'] for _,m in items)*1.43);ax.set_xticks([0,.1,.2,.3,.4]);ax.xaxis.set_major_formatter(PercentFormatter(1,decimals=0));clean(ax)
save(f,'06_theme_prevalence')

# 07: prevalence per phase with denominators, not raw volume.
periods=list(R['periods']);f=frame('关注点演变：比较占比，不只数条数','颜色越深，表示该阶段提到主题的评价比例越高\n多标签口径；第5天尚未完整，不能解释为长期趋势',10)
keys=[k for k,_ in items];matrix=np.array([[R['theme_periods'][k][p]['rate'] for p in periods] for k in keys])
ax=f.add_axes([.24,.20,.70,.59]);cmap=LinearSegmentedColormap.from_list('jade',['#EDF5EA','#A3D7C4','#168B78','#125950'])
ax.imshow(matrix,aspect='auto',cmap=cmap,vmin=0,vmax=max(.45,matrix.max()))
for y in range(len(keys)):
    for x in range(len(periods)):ax.text(x,y,f'{matrix[y,x]:.0%}',ha='center',va='center',fontsize=15,color='white' if matrix[y,x]>.28 else INK)
ax.set_yticks(range(len(keys)),keys);ax.set_xticks(range(4),[f'{p}\nn={R["periods"][p]["n"]}' for p in periods],rotation=25,ha='right',fontsize=12);clean(ax,None)
save(f,'07_theme_evolution')

# 08: TF-IDF cohort words (shared corpus fit).
f=frame('从文字中提取：首发前后的代表词','同一TF-IDF词表；各阶段文档向量取均值\n先去重相同正文，权重不是人数或情绪分数',10)
for top,p in [(.74,'首发前7天'),(.37,'首发第2–4天')]:
    terms=R['keywords'][p]['terms'][:7];ax=f.add_axes([.20,top-.25,.63,.23])
    vals=[x['weight'] for x in terms];ax.barh(range(7),vals,color=GREEN if top>.5 else TEAL,height=.58)
    ax.set_yticks(range(7),[x['term'] for x in terms],fontsize=15);ax.invert_yaxis();ax.set_xlim(0,max(vals)*1.22);clean(ax)
    f.text(.12,top+.025,p+f" · 有效文档 {R['keywords'][p]['n']}",fontsize=18,weight='bold')
save(f,'08_tfidf_keywords')

# 09: topic cards, transparent top terms and group size.
f=frame('NMF主题探索：让共现词给我们线索',f"{R['nmf']['documents']:,} 条去重且向量非零的文本，探索性分为6组\n按最大主题权重归组；组名需回读原文解释",11)
for i,t in enumerate(R['nmf']['topics']):
    y=.75-i*.108
    card=FancyBboxPatch((.055,y-.055),.89,.085,boxstyle='round,pad=0.008,rounding_size=0.014',transform=f.transFigure,facecolor='#E8F0E9',edgecolor='none');f.add_artist(card)
    f.text(.08,y+.006,f"主题 {i+1:02d}",fontsize=17,weight='bold',color=GREEN)
    f.text(.90,y+.006,f"{t['n']:,} 条",fontsize=15,ha='right',color=MUTED)
    words=t['terms'][:6];f.text(.08,y-.03,' / '.join(words),fontsize=15)
save(f,'09_nmf_topics')

# Cover: original editorial design derived from aggregate counts.
f=plt.figure(figsize=(10,4.3),facecolor=INK)
f.text(.055,.80,'PYTHON × 玩家评价',fontsize=18,color='#94C5B5',weight='bold')
f.text(.055,.57,'从爬虫到游戏舆情分析',fontsize=32,color='white',weight='bold')
f.text(.055,.35,f"王者万象棋  |  {C['n']:,}条公开评价实战",fontsize=20,color='#E2EBDD')
f.text(.055,.13,'可以叫我才哥',fontsize=16,color='#94C5B5')
for i,v in enumerate(values):f.add_artist(FancyBboxPatch((.75+i*.035,.12),.021,.13+v/max(values)*.13,boxstyle='round,pad=0.002',transform=f.transFigure,facecolor=[RED,'#E4A393',GOLD,TEAL,GREEN][i],edgecolor='none'))
f.savefig(OUT/'00_cover_v1.0.0.png',dpi=180,facecolor=INK);plt.close(f)
print('9 charts and cover saved.')
