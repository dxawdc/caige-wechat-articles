"""S44 图表与段位动画 v1.2.0 | 2026-09-14。
用法：python 绘图_v1.2.0.py --data 分析结果_私有_v1.2.0.json [--skip-gif]
输入为分析脚本实际输出，不请求网络、不生成模拟统计。
"""
from pathlib import Path
import argparse,json,os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.ticker import PercentFormatter, MaxNLocator

ROOT=Path(__file__).resolve().parent
BG='#FAF8F2'; INK='#21374A'; TEAL='#267C82'; GOLD='#B68734'; CORAL='#BC725B'; GREY='#71808A'; GRID='#E1E5E2'
SILVER='#8FA8B9'; PALE='#B9CFCD'

def setup():
    font=os.environ.get('CJK_FONT',r'C:\Windows\Fonts\msyh.ttc')
    if Path(font).exists():
        font_manager.fontManager.addfont(font)
        family=font_manager.FontProperties(fname=font).get_name()
    else:
        available={f.name for f in font_manager.fontManager.ttflist}
        family=next((x for x in ['Noto Sans CJK SC','Microsoft YaHei','SimHei','Arial Unicode MS'] if x in available),None)
        if family is None:raise RuntimeError('请安装中文字体，或设置 CJK_FONT 为字体路径。')
    plt.rcParams.update({'font.family':family,'font.size':13,'axes.titlesize':19,
        'axes.labelsize':12,'xtick.labelsize':11,'ytick.labelsize':12,
        'axes.unicode_minus':False,'figure.facecolor':BG,'axes.facecolor':BG,
        'text.color':INK,'axes.labelcolor':GREY,'xtick.color':GREY,'ytick.color':GREY,
        'axes.edgecolor':GRID,'savefig.facecolor':BG,'svg.fonttype':'path'})

def fig(title,sub='',size=(10,6.5)):
    f=plt.figure(figsize=size,dpi=160)
    f.text(.055,.952,title,size=22,weight='bold',va='top',color=INK)
    f.text(.055,.89,sub,size=11,color=GREY,va='top')
    f.add_artist(plt.Line2D([.055,.945],[.853,.853],transform=f.transFigure,color=GRID,linewidth=1))
    f.text(.055,.024,'可以叫我才哥   /   S44 排位手记',size=10,color=GREY)
    f.text(.945,.024,'DATA / 2026',size=9,color=GOLD,ha='right')
    return f

def clean(ax,grid='y'):
    for s in ['top','right']:ax.spines[s].set_visible(False)
    ax.set_axisbelow(True)
    if grid:ax.grid(axis=grid,color=GRID,linewidth=.7)
    ax.tick_params(length=0,pad=7)

def save(f,path):
    f.savefig(str(path)+'.png',dpi=160)
    f.savefig(str(path)+'.svg')
    plt.close(f)

def wilson(w,n):
    p=w/n;z=1.96;den=1+z*z/n
    mid=(p+z*z/(2*n))/den;rad=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-rad,mid+rad

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,default=ROOT/'分析结果_私有_v1.2.0.json')
    ap.add_argument('--skip-gif',action='store_true');args=ap.parse_args()
    data=json.loads(args.data.read_text(encoding='utf-8'));s=data['summary'];t={k:pd.DataFrame(v) for k,v in data['tables'].items()}
    r=pd.DataFrame(data['trajectory']);out=ROOT/'图表_v1.2.0';out.mkdir(exist_ok=True);setup()
    def export(f,name):save(f,out/(name+'_v1.2.0'))
    f=fig('我的 S44，净增了 95 星','仅排位赛｜2026.07.03—09.13 有记录｜采集截至 09.14',size=(10,7.7))
    f.text(.06,.60,'+95',size=98,weight='bold',color=GOLD)
    f.text(.46,.635,'星 · 赛季净增',size=23,weight='bold')
    f.text(.46,.565,'钻石 IV 1 星 → 荣耀王者 51 星',size=16,color=GREY)
    f.text(.065,.48,'累计升星 227  −  累计掉星 132  =  净增 95',size=19,color=INK)
    for x,value,label in [(.065,'332','场排位'),(.38,'56.3%','胜率 · 187 胜 145 负'),(.72,'23.2%','MVP 率 · 77 / 332')]:
        f.text(x,.31,value,size=35,weight='bold',color=TEAL)
        f.text(x,.255,label,size=12,color=GREY)
    f.text(.065,.15,'77 次 MVP = 胜方 37 + 败方 40',size=15,weight='bold')
    f.text(.065,.087,'47 个排位日   ·   37 位英雄   ·   86.0 小时纯对局',size=13,color=GREY)
    export(f,'01_赛季总览')

    g=t['组队'];f=fig('三排胜率最高，单排是主要战场','MVP 含胜方与败方；组队样本、段位构成不同，不作因果比较',size=(10,6.8))
    ax=f.add_axes([.08,.18,.36,.59]);clean(ax,'x');y=np.arange(len(g));ax.barh(y,g['场次'],color=TEAL,height=.55)
    ax.set_yticks(y,['单排','双排','三排','五排']);ax.invert_yaxis();ax.set_xlim(0,315);ax.set_xlabel('场次')
    for i,n in enumerate(g['场次']):ax.text(n+5,i,str(int(n)),va='center',weight='bold')
    ax2=f.add_axes([.56,.18,.39,.59]);ax2.axis('off');ax2.set_xlim(0,1);ax2.set_ylim(3.7,-.7)
    for x,label in [(0,'胜率'),(.47,'MVP 率')]:ax2.text(x,-.61,label,color=GREY,size=12)
    for i,row in g.iterrows():
        ax2.text(0,i,f"{row['胜率']:.1%}",size=22,va='center',weight='bold',color=TEAL)
        ax2.text(.47,i,f"{row['MVP率']:.1%}",size=20,va='center',color=INK)
        ax2.text(.89,i,f"{int(row['MVP次数'])} 次",size=11,va='center',color=GREY)
    export(f,'02_组队比较')

    def rank_base(animated=False):
        f=fig('从钻石 IV 到荣耀王者','逐场记录的段位轨迹｜横轴为排位场序号｜段位时点推定为赛后',size=(10,6.8))
        ax=f.add_axes([.15,.18,.8,.61]);clean(ax)
        ax.axhspan(50,75,color=TEAL,alpha=.04);ax.axhspan(75,100,color=GOLD,alpha=.055)
        for v in [75,100,150]:ax.axhline(v,color=GOLD if v==150 else GRID,lw=1,ls='--')
        ax.set_xlim(0,len(r)+7);ax.set_ylim(50,167)
        ax.set_xticks([0,50,100,150,200,250,300,332]);ax.set_xlabel('本赛季排位场序号（0 为用户确认的初始段位）')
        ax.set_yticks([55,75,100,120,140,150],['钻石 IV','星耀 V','王者 0 星','王者 20 星','王者 40 星','荣耀 50 星'])
        f.text(.15,.075,'纵轴为跨段位统一刻度，仅用于展示；满星边界可能重合，晋级以段位编码核实。',size=10,color=GREY)
        return f,ax
    f,ax=rank_base();ax.plot([0,*r.seq],[s['initial_rank_score'],*r.rank_score],color=TEAL,lw=2)
    for m,offset in zip(s['milestones'],[(-75,42),(-137,17)]):
        ax.scatter(m['序号'],m['刻度'],s=70,color=GOLD,zorder=5,edgecolor=BG,linewidth=2)
        ax.annotate(f"{m['里程碑']}  {m['日期'][5:]}\n第 {m['序号']} 场 · {m['英雄']}",xy=(m['序号'],m['刻度']),xytext=offset,textcoords='offset points',fontsize=11,weight='bold',
            bbox=dict(boxstyle='round,pad=.55',facecolor=BG,edgecolor=GOLD),arrowprops=dict(arrowstyle='-',color=GOLD))
    ax.text(6,57,'初始：钻石 IV 1 星',size=10,color=GREY);export(f,'03_段位静态轨迹')

    if not args.skip_gif:
        f,ax=rank_base(True);f.set_dpi(100)
        line,=ax.plot([],[],color=TEAL,lw=2.3);dot,=ax.plot([],[],marker='o',color=GOLD,ms=7)
        label=ax.text(.02,.97,'',transform=ax.transAxes,va='top',size=12,weight='bold')
        marks=[]
        for m,xy in zip(s['milestones'],[(.40,.65),(.57,.84)]):
            txt=ax.text(*xy,f"{m['日期'][5:]}  {m['里程碑']}\n第 {m['序号']} 场 · {m['英雄']}",transform=ax.transAxes,
                size=11,color=GOLD,weight='bold',bbox=dict(facecolor=BG,edgecolor='none',alpha=.93));txt.set_visible(False);marks.append((m,txt))
        frames=sorted(set([1,*range(4,len(r)+1,4),*[m['序号'] for m in s['milestones']],len(r)]))+[len(r)]*12
        def update(n):
            part=r.iloc[:n];last=part.iloc[-1];line.set_data([0,*part.seq],[s['initial_rank_score'],*part.rank_score]);dot.set_data([last.seq],[last.rank_score])
            label.set_text(f"第 {n:03d} 场  |  {last.settle_date[5:]}  |  {last['历史段位含星']}")
            for m,txt in marks:txt.set_visible(n>=m['序号'])
            return line,dot,label
        animation=FuncAnimation(f,update,frames=frames,interval=110,blit=False)
        animation.save(out/'04_段位动态轨迹_v1.2.0.gif',writer=PillowWriter(fps=9),dpi=100)
        plt.close(f)

    g=t['英雄'].head(12).reset_index(drop=True);f=fig('后羿是使用最多的英雄，也是主要胜场来源','展示使用次数前 12 位；其余 25 位英雄保留在完整统计表中',size=(10,9.2))
    ax=f.add_axes([.12,.13,.34,.69]);clean(ax,'x');y=np.arange(len(g));ax.barh(y,g['场次'],color=[TEAL]+['#ACC9C8']*(len(g)-1),height=.63)
    ax.set_yticks(y,g['英雄']);ax.invert_yaxis();ax.set_xlim(0,75);ax.set_xlabel('使用场次')
    for i,n in enumerate(g['场次']):ax.text(n+1.1,i,str(int(n)),va='center',size=11)
    ax2=f.add_axes([.52,.13,.41,.69]);clean(ax2,'x');ax2.set_yticks([]);ax2.set_ylim(len(g)-.5,-.5);ax2.set_xlim(0,1);ax2.xaxis.set_major_formatter(PercentFormatter(1));ax2.set_xlabel('胜率与 Wilson 95% 区间（描述性）')
    ax2.axvline(s['win_rate'],color=GOLD,ls='--',lw=1)
    for i,row in g.iterrows():
        lo,hi=wilson(row['胜场'],row['场次']);p=row['胜率']
        ax2.plot([lo,hi],[i,i],color='#ACC9C8',lw=3);ax2.scatter(p,i,s=40,color=TEAL,zorder=3)
        ax2.text(.98,i,f'{p:.1%}',ha='right',va='center',size=11,bbox=dict(facecolor=BG,edgecolor='none',pad=1))
    f.text(.12,.055,'虚线为个人整体胜率 56.3%；区间仅提示样本量，未校正组队、段位及重复玩家等影响。',size=10,color=GREY)
    export(f,'05_英雄使用与胜率')

    g=t['星期'];f=fig('周一打得最多，周末并未包揽排位','按开局时间归属星期，北京时间；总量与每个日历日平均场次一起看')
    ax=f.add_axes([.08,.21,.87,.59]);clean(ax);x=np.arange(7);ax.bar(x,g['场次'],color=[TEAL]+['#ACC9C8']*6,width=.58)
    ax.set_xticks(x,['周一','周二','周三','周四','周五','周六','周日']);ax.set_ylim(0,75);ax.set_ylabel('场次')
    for i,row in g.iterrows():ax.text(i,row['场次']+1.5,str(int(row['场次'])),ha='center',weight='bold')
    f.text(.08,.12,'每个日历日平均：'+ ' / '.join(f'{v:.1f}' for v in g['每个日历日平均场次'])+' 场（周一至周日）',size=11,color=GREY)
    export(f,'06_星期分布')

    g=t['小时'];f=fig('最常在几点开一局','按开局小时归属，00—23 点均展示；不是各时段胜率排名')
    ax=f.add_axes([.08,.18,.87,.62]);clean(ax);ax.bar(g.hour,g['场次'],color=[TEAL if x>=18 else '#ACC9C8' for x in g.hour],width=.72)
    ax.set_xticks(range(0,24,2));ax.set_xlim(-.7,23.7);ax.set_xlabel('开局小时（北京时间）');ax.set_ylabel('场次');ax.set_ylim(0,g['场次'].max()*1.18)
    for _,row in g[g['场次']>=20].iterrows():ax.text(row.hour,row['场次']+1,str(int(row['场次'])),ha='center',size=11)
    export(f,'07_小时分布')

    a=np.array(data['heatmap']);f=fig('星期 × 小时：我的排位时间指纹','单元格为开局场次；零场次留白，完整数值见配套 7×24 矩阵',size=(10,6))
    ax=f.add_axes([.09,.22,.85,.53]);cmap=LinearSegmentedColormap.from_list('camp',[BG,'#B8D6D2',TEAL])
    im=ax.imshow(a,aspect='auto',cmap=cmap,vmin=0,vmax=a.max());ax.set_yticks(range(7),['周一','周二','周三','周四','周五','周六','周日']);ax.set_xticks(range(0,24,2));ax.set_xlabel('开局小时（北京时间）');ax.tick_params(length=0)
    for (i,j),v in np.ndenumerate(a):
        if v:ax.text(j,i,str(v),ha='center',va='center',size=9,color=BG if v>a.max()*.68 else INK)
    for sp in ax.spines.values():sp.set_visible(False)
    export(f,'08_星期小时热力图')

    g=t['每日升降星'];f=fig('每日净星数：35 天上升，8 天回落','按结算日期｜4 天持平｜正值为净上星，负值为净掉星',size=(10,7.0))
    ax=f.add_axes([.08,.24,.87,.55]);clean(ax);x=np.arange(len(g));vals=g['净升星'].fillna(0)
    ax.bar(x,vals,color=[TEAL if v>0 else CORAL if v<0 else SILVER for v in vals],width=.72)
    ax.axhline(0,color=GREY,lw=1);ax.set_ylabel('当日净星数');ax.set_ylim(-3.7,12.5)
    dates=g.settle_date.str[5:];ticks=sorted(set([0,*range(4,len(g)-3,5),len(g)-1]));ax.set_xticks(ticks,dates.iloc[ticks]);ax.set_xlabel('有排位结算的日期（间隔不等距）')
    idx=int(g.index[g['净升星']==10][0]);ax.annotate('08-18  +10',xy=(idx,10),xytext=(idx-12,10.8),color=TEAL,size=12,weight='bold',arrowprops=dict(arrowstyle='-',color=TEAL))
    for i,value in enumerate(vals):
        if value<0:ax.text(i,value-.24,str(int(value)),ha='center',va='top',size=9,color=CORAL)
    f.text(.08,.12,'日净额合计：+108 − 13 = +95 星。每天净额已抵消当日内的升降。',size=12,color=INK)
    export(f,'09_每日升降星')

    g=t['时长分布'];f=fig('一局通常要多久','所有 332 场都有时长；区间左闭右开，例如 10–15 表示 [10,15) 分钟')
    ax=f.add_axes([.08,.25,.87,.54]);clean(ax);bars=ax.bar(g.duration_bin,g['场次'],color=TEAL,width=.57);ax.set_xlabel('单局时长 / 分钟');ax.set_ylabel('场次');ax.set_ylim(0,g['场次'].max()*1.24)
    for bar,n in zip(bars,g['场次']):ax.text(bar.get_x()+bar.get_width()/2,n+2,f'{int(n)}\n{n/332:.1%}',ha='center',size=11)
    f.text(.08,.12,'平均 15 分 33 秒  ·  中位数 15 分 11 秒  ·  最短 6 分 07 秒  ·  最长 31 分 05 秒',size=11,color=GREY)
    export(f,'10_对局时长分布')

    g=t['单局击杀分布'];f=fig('平均每局 3.44 次击杀，最常见是几杀','单局击杀数分布：每一局作为一个样本；另附每日场均击杀分布')
    ax=f.add_axes([.08,.2,.87,.59]);clean(ax);ax.bar(g['击杀'],g['场次'],color=TEAL,width=.7);ax.set_xticks(range(18));ax.set_xlabel('单局击杀次数');ax.set_ylabel('场次');ax.set_ylim(0,g['场次'].max()*1.2)
    for _,row in g.iterrows():
        if row['场次']:ax.text(row['击杀'],row['场次']+1,str(int(row['场次'])),ha='center',size=10)
    ax.axvline(s['kills_mean'],color=GOLD,ls='--',lw=1.5)
    export(f,'11_单局击杀分布')

    g=t['每日场均击杀分布'];f=fig('换一个口径：每天的场均击杀','47 个有排位的日期，每天一个样本；日均值的分布不等于单局分布')
    ax=f.add_axes([.08,.2,.87,.59]);clean(ax);bars=ax.bar(g['日均击杀区间'],g['天数'],color=TEAL,width=.57);ax.set_xlabel('当天总击杀 / 当天场次');ax.set_ylabel('天数');ax.set_ylim(0,g['天数'].max()*1.2)
    for b,n in zip(bars,g['天数']):ax.text(b.get_x()+b.get_width()/2,n+.5,str(int(n)),ha='center')
    export(f,'12_每日场均击杀分布')

    g=t['局评价'];f=fig('59 场尽力局，75 场实力局','接口评价原文；未标注占 149 场，不能将空白视作“没有贡献”',size=(10,7))
    ax=f.add_axes([.14,.15,.8,.66]);clean(ax,'x');ax.barh(g['对局评价'],g['场次'],color=[GREY if x=='未标注' else CORAL if x=='尽力局' else TEAL for x in g['对局评价']],height=.62);ax.invert_yaxis();ax.set_xlim(0,175);ax.set_xlabel('场次')
    for i,n in enumerate(g['场次']):ax.text(n+2,i,str(int(n)),va='center',size=11)
    export(f,'13_局评价分布')

    f=fig('上分并非一路平滑：最近 20 场胜率','每个点包含当前局与之前 19 场；不足 20 场不绘制')
    ax=f.add_axes([.09,.2,.85,.59]);clean(ax);ax.plot(r.seq,r.rolling20,color=TEAL,lw=2);ax.axhline(.5,color=GOLD,ls='--',lw=1)
    ax.set_ylim(0,1);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_xlim(1,332);ax.set_xticks([1,50,100,150,200,250,300,332]);ax.set_xlabel('本赛季排位场序号');ax.set_ylabel('最近 20 场胜率')
    export(f,'14_滚动胜率')

    f=fig('一些值得收藏的赛季小纪录','同一玩家、同一赛季的描述性统计；保留有意思的细节，也保留样本量',size=(10,9))
    items=[(.07,.68,'34','场零死亡','其中 31 胜，胜率 91.2%',TEAL),(.55,.68,'17 / 1 / 11','最高击杀局','07-09 · 后羿 · 带飞局',GOLD),
        (.07,.43,'9','最长连续排位胜利','08-18 至 08-19，跨日 9 连胜',GOLD),(.55,.43,'20','单日最多排位','08-29 首次荣耀日 · 5.2 小时',TEAL),
        (.07,.18,'17','姜子牙 MVP 次数','胜方 7 + 败方 10；全英雄最多',TEAL),(.55,.18,'8 / 31','零击杀局也能赢','31 场零击杀里赢了 8 场',GOLD)]
    for x,y,big,label,note,color in items:
        f.text(x,y,big,size=34 if len(big)<6 else 29,color=color,weight='bold');f.text(x,y-.05,label,size=14,weight='bold');f.text(x,y-.093,note,size=11,color=GREY)
    export(f,'17_赛季趣味纪录')

    f=fig('三连之后，下一局打得怎么样','每段首次达到 3 连胜 / 3 连败后取下一局；每段只计一次',size=(10,7.3))
    ax=f.add_axes([.18,.30,.70,.43]);clean(ax,'x');g=t['三连后下一局胜率'];g=g[g['口径']=='首次达到3场'].reset_index(drop=True)
    ax.set_xlim(0,1);ax.set_ylim(1.6,-.7);ax.set_yticks([0,1],['3 连胜后','3 连败后']);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.set_xlabel('下一局胜率（细线为 Wilson 95% 区间）')
    ax.axvline(s['win_rate'],color=GREY,ls='--',lw=1)
    for i,row in g.iterrows():
        rate=row['下一局胜率'];color=TEAL if i==0 else CORAL
        ax.plot([row['Wilson95下界'],row['Wilson95上界']],[i,i],color=color,lw=3,alpha=.6)
        ax.scatter(rate,i,s=110,color=color,zorder=5,edgecolor=BG,linewidth=2)
        ax.text(rate,i-.21,f'{rate:.2%}',ha='center',size=22,weight='bold',color=color)
        ax.text(.02,i+.24,f"{int(row['下一局胜场'])} 胜 {int(row['下一局负场'])} 负  /  {int(row['下一局场次'])} 次触发",size=12,color=GREY)
    f.text(.18,.16,'虚线：全赛季胜率 56.3%。样本较少，且没有控制队友、段位与休息。',size=11,color=GREY)
    f.text(.18,.095,'滚动口径交叉核对：最近 3 场全胜后 33/58，全败后 16/19。',size=11,color=GREY)
    export(f,'18_三连后下一局胜率')

    g=t['金银牌分路'];f=fig('60 次金银牌，中路贡献了 38 次','全赛季 332 场｜金牌 26 次，银牌 34 次｜金银牌率 18.1%',size=(10,7))
    ax=f.add_axes([.12,.22,.81,.54]);clean(ax,'x');y=np.arange(len(g))
    ax.barh(y,g['金牌'],color=GOLD,height=.55,label='金牌');ax.barh(y,g['银牌'],left=g['金牌'],color=SILVER,height=.55,label='银牌')
    ax.set_yticks(y,g['牌子分路']);ax.invert_yaxis();ax.set_xlim(0,43);ax.set_xlabel('获得次数');ax.legend(frameon=False,loc='lower right',ncol=2)
    for i,row in g.iterrows():
        a,b=int(row['金牌']),int(row['银牌'])
        if a:ax.text(a/2,i,str(a),color='white',ha='center',va='center',weight='bold')
        if b:ax.text(a+b/2,i,str(b),color=INK,ha='center',va='center',weight='bold')
        ax.text(a+b+1,i,str(a+b),va='center',weight='bold')
    f.text(.12,.12,'金牌：中路 16 / 游走 6 / 发育路 4；银牌：中路 22 / 发育路 7 / 游走 5。',size=11,color=GREY)
    export(f,'19_金银牌分路分布')

    g=t['金银牌英雄'];f=fig('姜子牙 13 次，拿到最多金银牌','按金银牌合计排序｜金色为金牌，蓝灰色为银牌｜展示全部获牌英雄',size=(10,9))
    ax=f.add_axes([.15,.13,.78,.69]);clean(ax,'x');y=np.arange(len(g))
    ax.barh(y,g['金牌'],color=GOLD,height=.6,label='金牌');ax.barh(y,g['银牌'],left=g['金牌'],color=SILVER,height=.6,label='银牌')
    ax.set_yticks(y,g['英雄']);ax.invert_yaxis();ax.set_xlim(0,15);ax.set_xlabel('金银牌次数');ax.xaxis.set_major_locator(MaxNLocator(integer=True));ax.legend(frameon=False,loc='lower right')
    for i,row in g.iterrows():
        a,b=int(row['金牌']),int(row['银牌'])
        if a:ax.text(a/2,i,str(a),ha='center',va='center',color='white',size=11)
        if b:ax.text(a+b/2,i,str(b),ha='center',va='center',color=INK,size=11)
        ax.text(a+b+.25,i,str(a+b),va='center',weight='bold',size=11)
    export(f,'20_金银牌英雄分布')

    g=t['完整详情牌子分布'];g=g[g['牌子等级'].isin(['金牌','银牌','铜牌','未获牌'])]
    f=fig('完整详情样本：8 金、12 银、7 铜','仅 98 场完整详情｜其中 71 场编码为 0（未获牌）｜不代表全赛季铜牌率',size=(10,6.6))
    ax=f.add_axes([.1,.22,.84,.57]);clean(ax);colors=[GOLD,SILVER,'#B98563','#D8DDDA']
    bars=ax.bar(g['牌子等级'],g['场次'],color=colors,width=.52);ax.set_ylabel('场次');ax.set_ylim(0,85)
    for bar,n in zip(bars,g['场次']):ax.text(bar.get_x()+bar.get_width()/2,n+2,f'{int(n)}\n{n/98:.1%}',ha='center',size=14,weight='bold')
    f.text(.1,.11,'较早 234 场无法确认铜牌；因此 7 次是已确认数量，不能视为全赛季总数。',size=11,color=GREY)
    export(f,'21_完整详情牌子分布')
    g=t['对局评分分布'];rating=s['rating']
    f=fig('我的对局评分，集中在哪一档','332 场评分完整｜按每局结算评分统计｜区间左闭右开',size=(10,9.2))
    for x,value,label,color in [(.08,f"{rating['mean']:.2f}",'平均评分',TEAL),
        (.39,f"{rating['median']:.1f}",'中位数',INK),
        (.70,f"{rating['at_least_10']}",'评分 ≥10 的场次',GOLD)]:
        f.text(x,.76,value,size=34,weight='bold',color=color);f.text(x,.714,label,size=12,color=GREY)
    ax=f.add_axes([.10,.32,.84,.32]);clean(ax)
    centers=(g['下界']+g['上界'])/2
    bars=ax.bar(centers,g['场次'],width=1.68,color=[GOLD if v>=10 else TEAL for v in g['下界']])
    ax.set_xticks(centers,[f'{int(lo)}–{int(hi)}' for lo,hi in zip(g['下界'],g['上界'])])
    ax.set_ylabel('场次');ax.set_xlabel('对局评分区间');ax.set_ylim(0,g['场次'].max()*1.3)
    for bar,n in zip(bars,g['场次']):ax.text(bar.get_x()+bar.get_width()/2,n+2,f'{int(n)}\n{n/332:.1%}',ha='center',size=11)
    f.add_artist(plt.Line2D([.08,.92],[.225,.225],transform=f.transFigure,color=GRID,lw=1))
    f.text(.08,.179,'14.4',size=30,weight='bold',color=GOLD);f.text(.25,.193,'最高 · 后羿 · 胜利',size=13,weight='bold')
    f.text(.08,.126,'07-09 22:24  /  17 杀 1 死 11 助攻',size=11,color=GREY)
    f.text(.54,.179,'2.9',size=30,weight='bold',color=CORAL);f.text(.67,.193,'最低 · 姜子牙 · 失败',size=12,weight='bold')
    f.text(.54,.126,'07-22 19:39  /  0 杀 1 死 1 助攻',size=11,color=GREY)
    f.text(.08,.079,'两项极值各出现 1 次；时间为北京时间开局时间。评分用于描述本季表现。',size=10,color=GREY)
    export(f,'22_对局评分分布')
    print('charts saved',out)

if __name__=='__main__':main()
