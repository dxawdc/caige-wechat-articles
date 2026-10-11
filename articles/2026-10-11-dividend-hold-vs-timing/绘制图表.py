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
INK='#233b3a';MUTED='#617673';GRID='#e2e9e5';PAPER='#fcfcf8';HOLD='#547992';TIMING='#bd7138';CASH='#75927a';COLORS=['#277c81','#b57f35','#a36a7c'];NAMES=['红利低波\n512890','中证红利\n515080','红利低波100\n515100'];CODES=list(R['funds'])
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei','SimHei','DejaVu Sans'],'axes.unicode_minus':False,'font.size':13,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False,'savefig.facecolor':PAPER})
def canvas(title,subtitle='',h=5.5):
    fig=plt.figure(figsize=(9,h),facecolor=PAPER);fig.text(.07,.945,title,fontsize=20,color=INK,weight='bold');fig.text(.07,.887,subtitle,fontsize=11,color=MUTED);return fig
def finish(fig,folder,name,note='2022.01—2026.09｜含分红理论再投｜单边费用0.03%'):
    folder.mkdir(parents=True,exist_ok=True)
    fig.text(.07,.027,note,fontsize=9,color=MUTED);fig.text(.94,.027,'可以叫我才哥',ha='right',fontsize=10,color=MUTED);fig.savefig(folder/name,dpi=180);plt.close(fig)
def clean(ax,pct=False):
    ax.set_facecolor(PAPER);ax.grid(axis='y',color=GRID,lw=.8);ax.set_axisbelow(True);ax.tick_params(length=0,pad=7)
    if pct:ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v:g}%'))
def dates(path):return md.date2num([date.fromisoformat(v) for v in path['dates']])
def year_ticks(ax):
    ax.xaxis.set_major_locator(md.YearLocator());ax.xaxis.set_major_formatter(md.DateFormatter('%Y'));ax.tick_params(axis='x',labelsize=11)

def article_a():
    fig=canvas('同样1万元，期末差多少？','同一套 MA182 / 7% 价格条件，放到3只红利ETF',5.8);ax=fig.add_axes([.10,.22,.84,.60]);x=np.arange(3)
    for j,(k,label,col) in enumerate([('hold','买入持有',HOLD),('timing','均线择时',TIMING)]):
        v=[R['results'][c][k]['summary']['terminal'] for c in CODES];bars=ax.bar(x+(j-.5)*.34,v,.31,color=col,label=label)
        for b,vv in zip(bars,v):ax.text(b.get_x()+b.get_width()/2,vv+.04,f'{vv:.2f}',ha='center',fontsize=13,color=col,weight='bold')
    ax.set_ylim(0,2.65);ax.set_ylabel('期末资产 / 万元');ax.set_xticks(x,NAMES);clean(ax);ax.legend(frameon=False,loc='upper left',ncol=2,fontsize=12);finish(fig,A,'图1_期末资产.png')
    fig=canvas('收益不是匀速积累的','以512890为例，统一从1开始记录账户净值',6);ax=fig.add_axes([.10,.19,.70,.62]);path=R['results']['512890']['hold'];xx=dates(path)
    for k,col,label in [('hold',HOLD,'持有'),('timing',TIMING,'择时')]:
        p=R['results']['512890'][k];ax.plot(xx,p['nav'],c=col,lw=2.2,label=label);ax.text(xx[-1]+15,p['nav'][-1],f'{label}\n{p["nav"][-1]:.2f}',color=col,va='center',fontsize=13)
    clean(ax);year_ticks(ax);ax.set_xlim(xx[0],xx[-1]);ax.set_ylabel('账户净值');ax.legend(frameon=False,loc='upper left');finish(fig,A,'图2_净值走势.png')
    fig=canvas('择时依然会经历回撤','最大回撤取每日收盘净值相对历史高点的跌幅',8.5)
    for j,c in enumerate(CODES):
        ax=fig.add_axes([.12,.64-j*.235,.82,.19]);
        for k,col,label in [('hold',HOLD,'持有'),('timing',TIMING,'择时')]:
            p=R['results'][c][k];ax.plot(dates(p),np.array(p['drawdown'])*100,c=col,lw=1.5,label=label)
        ax.set_ylim(-21,1);ax.set_yticks([-20,-10,0]);clean(ax,True);year_ticks(ax);ax.text(.015,.08,NAMES[j].replace('\n',' · '),transform=ax.transAxes,fontsize=12,color=INK)
        if j==0:ax.legend(frameon=False,loc='lower right',ncol=2,fontsize=11)
    finish(fig,A,'图3_回撤曲线.png')
    fig=canvas('每一年，都能跑赢持有吗？','2026年仅统计前三季度；各格为当期账户收益率',6.2);ax=fig.add_axes([.25,.16,.69,.66]);years=['2022','2023','2024','2025','2026'];vals=[];labels=[]
    for c,name in zip(CODES,NAMES):
        for k,label in [('hold','持有'),('timing','择时')]:vals.append([R['results'][c][k]['summary']['annual'][y]*100 for y in years]);labels.append(name.replace('\n',' ')+'\n'+label)
    arr=np.array(vals);cmap=LinearSegmentedColormap.from_list('returns',['#56839a','#f4f3ec','#bb793e']);ax.imshow(arr,aspect='auto',cmap=cmap,norm=TwoSlopeNorm(vmin=-8,vcenter=0,vmax=40))
    for (i,j),v in np.ndenumerate(arr):ax.text(j,i,f'{v:+.1f}%',ha='center',va='center',fontsize=12,color='white' if v>25 else INK)
    ax.set_xticks(range(5),['2022','2023','2024','2025','2026\n前三季度']);ax.set_yticks(range(6),labels,fontsize=10);ax.tick_params(length=0);finish(fig,A,'图4_年度收益.png')
    fig=canvas('空仓，也是一种需要承受的状态','彩色表示收盘持仓，浅灰表示空仓；天数指交易日',5.8);ax=fig.add_axes([.10,.24,.70,.51]);
    for j,c in enumerate(CODES):
        p=R['results'][c]['timing'];xx=dates(p);pos=np.array(p['positions']);ax.broken_barh([(xx[0],xx[-1]-xx[0])],(2-j-.22,.44),facecolors='#e7ece7');start=None
        for i,v in enumerate(pos):
            if v and start is None:start=i
            if start is not None and (not v or i==len(pos)-1):
                end=i;ax.broken_barh([(xx[start],xx[end]-xx[start])],(2-j-.22,.44),facecolors=COLORS[j]);start=None
        s=p['summary'];ax.text(xx[-1]+12,2-j,f'在场 {s["exposure"]:.0%}\n最长空仓 {s["max_cash_streak"]}天',va='center',fontsize=11,color=INK)
    ax.set_yticks([2,1,0],[c for c in CODES]);ax.set_ylim(-.65,2.65);ax.set_xlim(xx[0],xx[-1]);year_ticks(ax);ax.tick_params(length=0);finish(fig,A,'图5_持仓与空仓.png')
    fig=canvas('给现金加上利息，结果会变多少？','现金年化2%仅作假设，不代表国债ETF的实际收益',5.5);ax=fig.add_axes([.13,.22,.80,.58]);x=np.arange(3)
    for j,(k,col,label) in enumerate([('timing',TIMING,'现金不计息'),('cash2',CASH,'现金年化2%')]):
        vals=[R['results'][c][k]['summary']['cagr']*100 for c in CODES];ax.bar(x+(j-.5)*.34,vals,.31,color=col,label=label)
        for a,v in zip(x+(j-.5)*.34,vals):ax.text(a,v+.4,f'{v:.2f}%',ha='center',fontsize=12,color=col)
    ax.set_ylim(0,25);ax.set_xticks(x,NAMES);ax.set_ylabel('年化收益');clean(ax,True);ax.legend(frameon=False,ncol=2,loc='upper right',fontsize=11);finish(fig,A,'图6_现金假设.png')

def heatmap(c,part,folder,name,title,subtitle):
    vals=np.array([[next(g for g in R['grid'][c] if g['window']==w and g['band']==b)[part]['cagr']*100 for b in R['bands']] for w in R['windows']]);fig=canvas(title,subtitle,7.3);ax=fig.add_axes([.14,.19,.72,.63]);cmap=LinearSegmentedColormap.from_list('grid',['#f4ead8','#9fbdb0','#267271']);im=ax.imshow(vals,cmap=cmap,vmin=0,vmax=25,aspect='auto')
    for (i,j),v in np.ndenumerate(vals):ax.text(j,i,f'{v:.1f}',ha='center',va='center',fontsize=11,color='white' if v>18 else INK)
    ax.set_xticks(range(len(R['bands'])),[f'{b:.0%}' for b in R['bands']]);ax.set_yticks(range(len(R['windows'])),R['windows']);ax.set_xlabel('卖出乖离阈值');ax.set_ylabel('均线 / 交易日');ax.tick_params(length=0);ax.add_patch(Rectangle((R['bands'].index(.07)-.5,R['windows'].index(182)-.5),1,1,fill=False,lw=2.5,ec='#c37c35'))
    cb=fig.colorbar(im,cax=fig.add_axes([.89,.19,.018,.63]));cb.set_label('年化收益 / %',fontsize=11);finish(fig,folder,name,'橙框：182日 / 7%｜同一色阶｜总回报价格条件实验')

def article_b():
    heatmap('512890','full',B,'图1_81组参数.png','182 / 7%，周围是什么样？','512890｜2022.01—2026.09｜9种均线 × 9种卖出阈值')
    heatmap('512890','train',B,'图2_前段参数.png','只看前两年，最高点在哪？','512890｜2022—2023｜各格为年化收益率')
    heatmap('512890','test',B,'图3_后段参数.png','换到后半段，再看同一张网格','512890｜2024.01—2026.09｜重新从现金开始')
    fig=canvas('前段冠军，带到后段会怎样？','只用2022—2023挑参数，再固定到2024—2026年9月',6);ax=fig.add_axes([.11,.24,.83,.56]);x=np.arange(3)
    for j,(key,col,label) in enumerate([('test_hold',HOLD,'后段持有'),('test',CASH,'前段冠军'),('test_default',TIMING,'固定182 / 7%')]):
        vals=[R['selection'][c][key]['cagr']*100 for c in CODES];ax.bar(x+(j-1)*.25,vals,.23,color=col,label=label)
        for a,v in zip(x+(j-1)*.25,vals):ax.text(a,v+.35,f'{v:.1f}',ha='center',fontsize=11,color=col)
    ax.set_ylim(0,26);ax.set_xticks(x,NAMES);clean(ax,True);ax.set_ylabel('后段年化收益');ax.legend(frameon=False,ncol=3,loc='upper left',fontsize=10);finish(fig,B,'图4_历史留出检验.png','历史留出检验，不等于真实发布后的样本外验证')
    fig=canvas('换一只ETF，“最优参数”也会变','全区间81组参数；线段为最低—最高，圆点为中位数',5.8);ax=fig.add_axes([.13,.23,.74,.58])
    for j,c in enumerate(CODES):
        vals=[g['full']['cagr']*100 for g in R['grid'][c]];ax.plot([min(vals),max(vals)],[2-j]*2,color=COLORS[j],lw=7,solid_capstyle='round');ax.scatter(np.median(vals),2-j,s=95,c=INK,zorder=4);best=max(R['grid'][c],key=lambda g:g['full']['cagr']);ax.text(max(vals)+.35,2-j,f'{max(vals):.2f}%\n{best["window"]}日 / {best["band"]:.0%}',va='center',fontsize=11,color=COLORS[j])
    ax.set_yticks([2,1,0],CODES);ax.set_xlim(0,25);ax.set_ylim(-.6,2.6);ax.set_xlabel('年化收益 / %');ax.grid(axis='x',color=GRID);ax.tick_params(length=0);finish(fig,B,'图5_跨标的参数.png')
    fig=canvas('成交慢一天，差多少？','信号分别延迟1、2、3个交易日，在开盘成交',5.8);ax=fig.add_axes([.13,.20,.70,.60])
    for j,c in enumerate(CODES):
        vals=[s['cagr']*100 for s in R['sensitivity'][c]['delay']];ax.plot([1,2,3],vals,'o-',color=COLORS[j],lw=2,ms=7,label=c)
        for x,v in zip([1,2,3],vals):ax.annotate(f'{v:.2f}%',(x,v),xytext=(0,-20 if j==1 else 10),textcoords='offset points',ha='center',fontsize=11,color=COLORS[j])
    ax.set_ylim(5,22);ax.set_xticks([1,2,3],['次日开盘','隔2日开盘','隔3日开盘']);clean(ax,True);ax.set_ylabel('年化收益');ax.legend(frameon=False,ncol=3,fontsize=11,loc='upper right');finish(fig,B,'图6_成交延迟.png')
if __name__=='__main__':article_a();print('6 charts ready')
