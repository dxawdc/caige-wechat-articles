from pathlib import Path
from datetime import date
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import LinearSegmentedColormap,TwoSlopeNorm
from matplotlib.patches import Rectangle
BASE=Path(__file__).resolve().parent;R=json.loads((BASE/'结果/研究结果.json').read_text(encoding='utf-8'))
A=BASE/'图片';B=BASE/'图片';
INK='#202B54';MUTED='#626B86';GRID='#E4E6F1';PAPER='#FAFAFE';HOLD='#4457C4';TIMING='#DB655A';CASH='#9471BE';COLORS=[HOLD,TIMING,CASH];CODES=list(R['funds']);NAMES=['红利低波 512890','中证红利 515080','红利低波100 515100']
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei','SimHei','DejaVu Sans'],'axes.unicode_minus':False,'font.size':13,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False,'savefig.facecolor':PAPER})
def canvas(title,subtitle='',h=6):
    fig=plt.figure(figsize=(9,h),facecolor=PAPER);fig.add_artist(plt.Line2D([.07,.115],[.966,.966],transform=fig.transFigure,color=TIMING,lw=4));fig.text(.07,.918,title,fontsize=21,color=INK,weight='bold');fig.text(.07,.865,subtitle,fontsize=10.5,color=MUTED);return fig
def finish(fig,folder,name,note='2022.01—2026.09 · 分红理论再投 · 单边费用0.03%'):
    folder.mkdir(parents=True,exist_ok=True);fig.text(.07,.027,note,fontsize=8.5,color=MUTED);fig.text(.94,.027,'可以叫我才哥',ha='right',fontsize=9,color=MUTED);fig.savefig(folder/name,dpi=180);plt.close(fig)
def clean(ax,pct=False):
    ax.set_facecolor(PAPER);ax.grid(axis='y',color=GRID,lw=.8);ax.set_axisbelow(True);ax.tick_params(length=0,pad=7)
    if pct:ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v:g}%'))
def dates(p):return md.date2num([date.fromisoformat(v) for v in p['dates']])
def year_ticks(ax):ax.xaxis.set_major_locator(md.YearLocator());ax.xaxis.set_major_formatter(md.DateFormatter('%Y'))
def article_a():
    fig=canvas('等买点，占去了大部分时间','200日均线 ±5% · 共1150个收益观察交易日',5.8);ax=fig.add_axes([.23,.23,.68,.56])
    for j,c in enumerate(CODES):
        p=R['results'][c]['timing'];held=sum(p['positions'][1:]);flat=1150-held;y=2-j
        ax.barh(y,held/1150*100,height=.48,color=COLORS[j]);ax.barh(y,flat/1150*100,left=held/1150*100,height=.48,color='#E9E9F4');ax.text(held/1150*50,y,f'{held}天',ha='center',va='center',fontsize=11,color='white');ax.text(held/1150*100+flat/1150*50,y,f'空仓 {flat}天',ha='center',va='center',color=INK);ax.text(100,y-.34,f'最长连续空仓 {p["summary"]["max_cash_streak"]}个交易日',ha='right',fontsize=10,color=MUTED)
    ax.set_yticks([2,1,0],CODES);ax.set_xticks([0,25,50,75,100],['0%','25%','50%','75%','100%']);ax.set_xlim(0,100);ax.set_ylim(-.65,2.6);ax.tick_params(length=0);ax.set_xlabel('彩色为持仓，浅色为空仓');finish(fig,A,'图1_时间账本.png')
    fig=canvas('回撤缩小，收益却没有一起变好','比较年化收益与最大回撤幅度，分别看两个维度',7.8)
    for panel,(metric,title) in enumerate([('cagr','年化收益率'),('max_drawdown','最大回撤幅度（越小越浅）')]):
        ax=fig.add_axes([.17,.49-panel*.32,.76,.24]);x=np.arange(3)
        for j,(k,label,col) in enumerate([('hold','持有',HOLD),('timing','区间交易',TIMING)]):
            vals=[abs(R['results'][c][k]['summary'][metric])*100 for c in CODES];bars=ax.bar(x+(j-.5)*.32,vals,.29,color=col,label=label)
            for bar,v in zip(bars,vals):ax.text(bar.get_x()+bar.get_width()/2,v+.4,f'{v:.2f}%',ha='center',fontsize=11,color=col)
        ax.set_ylim(0,25 if panel==0 else 20);ax.set_xticks(x,CODES);clean(ax,True);ax.set_title(title,loc='left',fontsize=12,color=INK,pad=9)
        if panel==0:ax.legend(frameon=False,loc='upper right',ncol=2,fontsize=10)
    finish(fig,A,'图2_收益与回撤.png')
    fig=canvas('有些年份，收益停在原地','2026年为前三季度；格内为账户当期收益率',6.8);ax=fig.add_axes([.24,.17,.68,.62]);vals=[];labels=[]
    for c in CODES:
        for k,label in [('hold','持有'),('timing','区间交易')]:vals.append([R['results'][c][k]['summary']['annual'][str(y)]*100 for y in range(2022,2027)]);labels.append(c+' / '+label)
    arr=np.array(vals);cmap=LinearSegmentedColormap.from_list('annual',[HOLD,'#F2F1F9',TIMING]);ax.imshow(arr,aspect='auto',cmap=cmap,norm=TwoSlopeNorm(vmin=-8,vcenter=0,vmax=50))
    for (i,j),v in np.ndenumerate(arr):ax.text(j,i,f'{v:+.1f}%',ha='center',va='center',fontsize=12,color='white' if v>32 else INK)
    ax.set_xticks(range(5),['2022','2023','2024','2025','2026\n前三季度']);ax.set_yticks(range(6),labels,fontsize=11);ax.tick_params(length=0);finish(fig,A,'图3_年度收益.png')
    fig=canvas('19.43%的年化，来自怎样的路径？','515080 · 账户从1起步；现金不计息时，空仓呈水平线',6);ax=fig.add_axes([.11,.20,.72,.58])
    for k,col,label in [('hold',HOLD,'持有'),('timing',TIMING,'区间交易')]:
        p=R['results']['515080'][k];xx=dates(p);ax.plot(xx,p['nav'],c=col,lw=2,label=label);ax.text(xx[-1]+18,p['nav'][-1],f'{label}\n{p["nav"][-1]:.2f}',color=col,va='center',fontsize=11)
    ax.set_xlim(xx[0],xx[-1]);ax.set_ylabel('账户净值');year_ticks(ax);clean(ax);ax.legend(frameon=False,loc='upper left',ncol=2);finish(fig,A,'图4_账户路径.png')
    d=json.loads((BASE/'数据/总回报行情.json').read_text(encoding='utf-8'));rows=[x for x in d['515080']['rows'] if '2024-09-02'<=x['date']<='2024-10-18'];xx=md.date2num([date.fromisoformat(x['date']) for x in rows]);v=[x['market_close'] for x in rows]
    fig=canvas('一次开盘，影响了整个回合','515080 · 2024年9—10月 · 线为场内收盘价，点为实际开盘',6.3);ax=fig.add_axes([.12,.21,.80,.57]);ax.plot(xx,v,c=HOLD,lw=2);ax.set_ylim(1.22,1.88);ax.set_xlim(xx[0],xx[-1]);ax.set_ylabel('场内价格 / 元');ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday=md.MO,interval=2));ax.xaxis.set_major_formatter(md.DateFormatter('%m-%d'));clean(ax)
    for day,label,where in [('2024-09-10','买入 09-10',(.10,.75)),('2024-10-08','卖出 10-08',(.60,.95))]:
        row=next(x for x in rows if x['date']==day);x=md.date2num(date.fromisoformat(day));ax.scatter(x,row['market_open'],s=60,c=TIMING,zorder=5);ax.annotate(f'{label}\n开盘 {row["market_open"]:.3f}',xy=(x,row['market_open']),xytext=where,textcoords='axes fraction',fontsize=11,color=INK,bbox=dict(boxstyle='round,pad=.35',fc=PAPER,ec='none'),arrowprops=dict(arrowstyle='-',color=MUTED,lw=1.1),ha='center')
    finish(fig,A,'图5_交易片段.png','事件窗口：2024.09.02—10.18 · 分红计入回合收益，图中展示场内价格')
    fig=canvas('等待期间的利息，会积累成差距','初始1万元 · 点旁为期末万元数 · 2%仅作固定利率假设',5.9);ax=fig.add_axes([.20,.23,.73,.55])
    for j,c in enumerate(CODES):
        a=R['results'][c]['timing']['summary']['terminal'];b=R['results'][c]['cash2']['summary']['terminal'];y=2-j;ax.plot([a,b],[y,y],color=GRID,lw=8);ax.scatter([a,b],[y,y],c=[TIMING,CASH],s=85,zorder=3);ax.annotate(f'{a:.3f}',(a,y),xytext=(0,-21),textcoords='offset points',ha='center',color=TIMING,fontsize=12);ax.annotate(f'{b:.3f}',(b,y),xytext=(0,10),textcoords='offset points',ha='center',color=CASH,fontsize=12)
    ax.set_yticks([2,1,0],CODES);ax.set_xlim(1.2,2.7);ax.set_ylim(-.6,2.7);ax.set_xlabel('期末资产 / 万元');ax.tick_params(length=0);ax.grid(axis='x',color=GRID);ax.scatter([],[],c=TIMING,label='现金不计息');ax.scatter([],[],c=CASH,label='现金年化2%');ax.legend(frameon=False,ncol=2,loc='upper left',fontsize=10);finish(fig,A,'图6_等待成本.png')

def article_b():
    fig=canvas('收益与回撤，放进同一张坐标图','每点为一组参数；圆点：区间交易，菱形：买入持有',10)
    for j,c in enumerate(CODES):
        ax=fig.add_axes([.14,.60-j*.23,.79,.18]);g=R['grid'][c];ax.scatter([-x['full']['max_drawdown']*100 for x in g],[x['full']['cagr']*100 for x in g],c=COLORS[j],s=29,alpha=.65);h=R['results'][c]['hold']['summary'];ax.scatter(-h['max_drawdown']*100,h['cagr']*100,marker='D',s=95,facecolors='none',edgecolors=INK,lw=1.5);ax.set_xlim(-.5,17);ax.set_ylim(-1,25);ax.text(.025,.87,c,transform=ax.transAxes,color=INK,weight='bold');ax.set_ylabel('年化 / %',fontsize=11);clean(ax)
        if j==2:ax.set_xlabel('最大回撤幅度 / %（越向左，回撤越浅）')
    finish(fig,B,'图1_收益回撤分布.png')
    c='512890';g=R['grid'][c];hold=R['results'][c]['hold']['summary']['cagr'];arr=np.array([[next(x for x in g if x['window']==w and x['band']==b)['full']['cagr']*100-hold*100 for b in R['bands']] for w in R['windows']]);fig=canvas('回撤小，不代表收益更高','512890 · 各格为相对持有的年化差，单位：百分点',7.7);ax=fig.add_axes([.13,.17,.73,.64]);cmap=LinearSegmentedColormap.from_list('excess',[HOLD,'#F4F2FA',TIMING]);im=ax.imshow(arr,cmap=cmap,norm=TwoSlopeNorm(vmin=-10,vcenter=0,vmax=10),aspect='auto')
    for (i,j),v in np.ndenumerate(arr):ax.text(j,i,f'{v:+.1f}',ha='center',va='center',fontsize=11,color='white' if abs(v)>6 else INK)
    ax.set_xticks(range(9),[f'±{b:.0%}' for b in R['bands']],fontsize=10);ax.set_yticks(range(9),R['windows']);ax.tick_params(length=0);ax.set_xlabel('买卖两侧使用同一偏离幅度');ax.set_ylabel('均线 / 交易日');ax.add_patch(Rectangle((5-.5,5-.5),1,1,fill=False,lw=2,ec=INK));cb=fig.colorbar(im,cax=fig.add_axes([.89,.17,.018,.64]));cb.set_label('年化差 / 百分点',fontsize=10);finish(fig,B,'图2_相对持有热力图.png','深框：200日 / ±5% · 颜色表示年化差，不代表未来跑赢概率')
    fig=canvas('阈值固定，均线变长会怎样？','固定±5% · 虚线位置是200日演示参数',6.1);ax=fig.add_axes([.12,.20,.81,.59]);markers=['o','s','^']
    for j,c in enumerate(CODES):
        v=[next(x for x in R['grid'][c] if x['window']==w and x['band']==.05)['full']['cagr']*100 for w in R['windows']];ax.plot(R['windows'],v,marker=markers[j],c=COLORS[j],lw=2,ms=5,label=c)
    ax.axvline(200,color=MUTED,ls=':',lw=1);ax.set_ylim(0,25);ax.set_xticks([60,120,180,200,250,300],[60,120,180,200,250,300],fontsize=11);ax.set_xlabel('均线 / 交易日');ax.set_ylabel('年化收益率');clean(ax,True);ax.legend(frameon=False,ncol=3,loc='upper right',fontsize=10);finish(fig,B,'图3_均线敏感性.png')
    fig=canvas('前段挑出的参数，带到后段再运行','只用2022—2023选参，固定用于2024—2026年9月',6);ax=fig.add_axes([.12,.23,.81,.55]);xx=np.arange(3)
    for j,(key,col,label) in enumerate([('test_hold',HOLD,'持有'),('test_default',CASH,'固定200 / ±5%'),('test',TIMING,'前段冠军')]):
        vals=[R['selection'][c][key]['cagr']*100 for c in CODES];ax.bar(xx+(j-1)*.25,vals,.23,color=col,label=label)
        for x,v in zip(xx+(j-1)*.25,vals):ax.text(x,v+.4,f'{v:.2f}',ha='center',fontsize=11,color=col)
    ax.set_ylim(0,27);ax.set_xticks(xx,CODES);ax.set_ylabel('后段年化收益率');clean(ax,True);ax.legend(frameon=False,ncol=3,loc='upper left',fontsize=10);finish(fig,B,'图4_历史留出检验.png','历史时间留出，两段从现金开始；不等于发布后实盘验证')
    arr=[];labels=[]
    for c in CODES:
        g=R['grid'][c];top=sorted(g,key=lambda x:-x['train']['cagr'])[:5];ranks=[1+sum(y['test']['cagr']>x['test']['cagr']+1e-12 for y in g) for x in top];arr.append(ranks);labels.append([f'{x["window"]}日 / ±{x["band"]:.0%}\n第{rank}名' for x,rank in zip(top,ranks)])
    fig=canvas('前五名换个时间，名次还一样吗？','列表示前段第1—5名；格内显示它在后段81组中的名次',5.9);ax=fig.add_axes([.13,.22,.79,.56]);ax.imshow(arr,aspect='auto',cmap=LinearSegmentedColormap.from_list('rank',['#EEEAF7','#9C8FC7',INK]),vmin=1,vmax=81)
    for i in range(3):
        for j in range(5):ax.text(j,i,labels[i][j],ha='center',va='center',fontsize=10.5,color='white' if arr[i][j]>40 else INK)
    ax.set_xticks(range(5),['前段第1','前段第2','前段第3','前段第4','前段第5'],fontsize=11);ax.set_yticks(range(3),CODES);ax.tick_params(length=0);finish(fig,B,'图5_名次迁移.png','按年化收益排序，数值相同采用并列名次；颜色越深，后段名次越靠后')
    fig=canvas('更晚行动，结果不一定同向变化','当日开盘使用1、2、3个交易日前的收盘条件',6);ax=fig.add_axes([.12,.20,.80,.58])
    for j,c in enumerate(CODES):
        vals=[s['cagr']*100 for s in R['sensitivity'][c]['delay']];ax.plot([1,2,3],vals,marker=markers[j],c=COLORS[j],lw=2,ms=6,label=c)
        for x,v in zip([1,2,3],vals):ax.annotate(f'{v:.2f}%',(x,v),xytext=(0,-20 if j==0 else 10),textcoords='offset points',ha='center',fontsize=11,color=COLORS[j])
    ax.set_ylim(4,24);ax.set_xticks([1,2,3],['滞后1日','滞后2日','滞后3日']);ax.set_ylabel('年化收益率');clean(ax,True);ax.legend(frameon=False,ncol=3,fontsize=10,loc='upper right');finish(fig,B,'图6_决策滞后.png','滞后条件结合当时仓位重新决策，不是把原订单机械排队后移')
if __name__=='__main__':article_a();print('6 charts ready')
