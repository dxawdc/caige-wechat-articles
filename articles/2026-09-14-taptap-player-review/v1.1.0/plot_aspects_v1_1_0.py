"""v1.1.0 | Three additional figures from inspectable aggregate / annotation JSON."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).parent/'outputs'
GREEN='#168B78';RED='#DB7462';INK='#183C3A';MUTED='#647C7A';BG='#F5F7F2'
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,
 'font.size':15,'figure.facecolor':BG,'axes.facecolor':BG,'text.color':INK,
 'xtick.color':MUTED,'ytick.color':INK,'svg.fonttype':'path','savefig.dpi':180})
def frame(title,sub,h=9):
    f=plt.figure(figsize=(9,h));f.text(.055,.955,title,fontsize=24,weight='bold',va='top')
    f.text(.055,.90,sub,fontsize=13,color=MUTED,va='top',linespacing=1.6)
    f.text(.055,.025,'可以叫我才哥  ·  TapTap 玩家评价分析',fontsize=12,color=MUTED)
    f.text(.945,.025,'采集 2026.09.14',fontsize=11,color=MUTED,ha='right');return f
def clean(ax):
    for s in ax.spines.values():s.set_visible(False)
    ax.tick_params(length=0,pad=8);ax.set_axisbelow(True);ax.grid(axis='x',color='#DDE7DF',lw=.8)
def save(f,name):
    for ext in ['png','svg']:f.savefig(OUT/f'{name}_v1.1.0.{ext}',facecolor=BG)
    plt.close(f)
m=json.loads((OUT/'rating_theme_mentions_v1.1.0.json').read_text(encoding='utf8'))
themes=sorted(m,key=lambda a:max(m[a][g]['mentions']/m[a][g]['n'] for g in ['高星','低星']),reverse=True)
f=frame('高星、低星评价，分别在谈什么？','全量分组：高星 1,107 条，低星 776 条\n词典主题提及率；提到某方面 ≠ 肯定或批评该方面',10)
ax=f.add_axes([.25,.19,.64,.59]);y=np.arange(len(themes))
for g,offset,col in [('高星',-.17,GREEN),('低星',.17,RED)]:
    vals=[100*m[a][g]['mentions']/m[a][g]['n'] for a in themes]
    ax.barh(y+offset,vals,height=.29,color=col,label=g+'（4–5星）' if g=='高星' else g+'（1–2星）')
    for yy,v in zip(y+offset,vals):ax.text(v+.55,yy,f'{v:.1f}%',va='center',fontsize=12,color=col)
ax.set_yticks(y,themes);ax.invert_yaxis();ax.set_xlim(0,40);ax.set_xticks([0,10,20,30,40],['0%','10%','20%','30%','40%']);clean(ax)
ax.legend(loc='lower left',bbox_to_anchor=(-.22,1.04),ncol=2,frameon=False,fontsize=13)
f.text(.055,.09,'分母取各自星级组；多标签可以重叠，比例不要求合计100%。',fontsize=12,color=MUTED)
save(f,'10_rating_theme_mentions')
s=json.loads((OUT/'aspect_summary_v1.1.0.json').read_text(encoding='utf8'))
for g,p,col,name,title in [('高星','praise',GREEN,'11_praise_reasons','高星评价，具体在给什么点赞？'),('低星','criticism',RED,'12_complaint_reasons','低星评价，具体在吐槽什么？')]:
    data=s['groups'][g];pairs=sorted([(a,n) for a,n in data[p].items() if n],key=lambda t:-t[1])
    h=8 if g=='高星' else 10
    f=frame(title,f'从{g}组随机抽取 40 条，由 Codex 逐条语境标注\n全时段快照样本；以下是明确表达该态度的评价数',h)
    ax=f.add_axes([.25,.30,.64,.48]);yy=np.arange(len(pairs));vals=[n for a,n in pairs]
    ax.barh(yy,vals,color=col,height=.57)
    for yv,(a,n) in zip(yy,pairs):ax.text(n+.22,yv,f'{n}/40',va='center',fontsize=16,weight='bold',color=col)
    ax.set_yticks(yy,[a for a,n in pairs]);ax.invert_yaxis();ax.set_xlim(0,max(vals)+3);ax.set_xlabel('评价条数（同一条可涉及多个方面）',fontsize=12,color=MUTED);clean(ax)
    msg=(f"23条有具体肯定，7条有具体批评，其中4条两者都有。\n14条未表达明确方面态度；预约、提问不算具体点赞。" if g=='高星' else '37条有具体批评，4条有具体肯定，其中3条两者都有。\n2条未表达明确方面态度；玩家指控不视为已证实事实。')
    f.text(.055,.145,msg,fontsize=13,linespacing=1.7,color=INK)
    f.text(.055,.065,'仅描述这40条；单一标注者、未独立复核，不外推为全体玩家比例。',fontsize=11.5,color=MUTED)
    save(f,name)
print('PASS: three figures generated from counts')
