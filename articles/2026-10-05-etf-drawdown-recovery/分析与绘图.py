"""使用真实价格快照计算回撤、修复及观察时长，生成公众号PNG/SVG。"""
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
from matplotlib.transforms import Bbox
from 回撤计算 import max_drawdown_record, drawdown_events

ROOT = Path(__file__).resolve().parent
DATA, OUT = ROOT / '数据', ROOT / '图表'
INK, BLUE, GOLD, MUTED, GRID = '#172F43','#3B7196','#C8813B','#71818E','#E5EBF0'
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
plt.rcParams.update({'font.family':'Microsoft YaHei','axes.unicode_minus':False,'font.size':11,'svg.fonttype':'none'})


def style(ax):
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color('#BCC8D1')
    ax.tick_params(colors=MUTED,length=0,pad=8)
    ax.grid(axis='x',color=GRID,lw=.7)
    ax.set_axisbelow(True)


def export(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=180,facecolor='white')
    fig.savefig(OUT/(name+'.svg'),facecolor='white')
    plt.close(fig)


def foot(fig,text='腾讯证券前复权日线；2025-09-30—2026-09-30；只计算窗口内的收盘价回撤。'):
    fig.text(.06,.035,text,fontsize=9,color=MUTED)
    fig.text(.95,.018,'可以叫我才哥',ha='right',fontsize=10,color=INK)


def tests():
    # 独立给定结果：已修复与未修复必须分开，时间数相邻间隔。
    f=pd.DataFrame({'date':pd.date_range('2026-01-01',periods=7),'close':[100,90,95,100,105,84,94.5]})
    r=max_drawdown_record(f); e=drawdown_events(f)
    assert math.isclose(r['max_drawdown_pct'],-20) and r['decline_days']==1
    assert r['recovery_days'] is None and r['observed_after_trough_days']==1
    assert len(e)==2 and e[0]['recovery_days']==2 and e[0]['underwater_days']==3
    f['close']=[100,100,90,90,100,110,110]
    r=max_drawdown_record(f)
    assert r['peak_i']==1 and r['trough_i']==2 and r['recovery_i']==4 and r['recovery_days']==2
    f['close']=[100,101,102,103,104,105,106]
    assert max_drawdown_record(f)['status']=='窗口内无回撤' and not drawdown_events(f)


def example_chart(code,frames,records,name,override=None):
    f=frames[code]; r=override if override is not None else records[code]
    p=f.close/r['peak_close']*100
    fig,ax=plt.subplots(figsize=(11,6.5),facecolor='white')
    # 编号标记真实节点；文字就近放在空白处，并以引导线连接。
    fig.subplots_adjust(left=.09,right=.94,top=.75,bottom=.18)
    style(ax); ax.grid(axis='y',color=GRID,lw=.7)
    curve,=ax.plot(f.date,p,color=BLUE,lw=2.3)
    baseline=ax.axhline(100,color=INK,lw=1,ls='--')
    ax.set_xlim(f.date.iloc[0]-pd.Timedelta(days=8),f.date.iloc[-1]+pd.Timedelta(days=18))
    ticks=[f.date.iloc[0], *pd.date_range('2025-12-01','2026-08-01',freq='2MS'), f.date.iloc[-1]]
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.set_ylabel('前复权收盘价 / 该次高点 × 100')
    lo,hi=float(p.min()),float(p.max()); ax.set_ylim(lo-(hi-lo)*.35,hi+(hi-lo)*.28)
    end_i=r.get('recovery_i')
    nodes=[(r['peak_i'],'高点',GOLD),(r['trough_i'],'低点',BLUE),
           (end_i if end_i is not None else len(f)-1,
            '首次修复' if end_i is not None else '观察截止 · 尚未修复',GOLD)]
    points=[]
    for number,(i,label,color) in enumerate(nodes,1):
        is_open=number==3 and end_i is None
        ax.scatter(f.date.iloc[i],p.iloc[i],s=220,facecolors='white' if is_open else color,
                   edgecolors=color if is_open else 'white',linewidths=1.5,zorder=5)
        ax.annotate(str(number),(f.date.iloc[i],p.iloc[i]),ha='center',va='center',
                    fontsize=9,weight='bold',color=color if is_open else 'white',zorder=6)
        points.append(ax.transData.transform((mdates.date2num(f.date.iloc[i]),p.iloc[i])))
    label='一次已修复回撤' if override is not None else '窗口最大回撤事件'
    fig.suptitle(f'{r["name"]}（{code}）：'+label,x=.06,ha='left',y=.96,fontsize=22,weight='bold',color=INK)
    tail=f'修复 {int(r["recovery_days"])} 个交易日' if r['status']=='已修复' else f'低点后已观察 {r["observed_after_trough_days"]} 个交易日，修复时长仍为空'
    fig.text(.06,.87,f'该次回撤 {r["max_drawdown_pct"]:.2f}%  |  下跌 {r["decline_days"]} 个交易日  |  '+tail,color=MUTED,fontsize=11)
    # 根据实际渲染后的文字框挑选位置，同时避开价格线、基准线、其他节点和标注。
    fig.canvas.draw()
    paths=[line.get_path().transformed(line.get_transform()) for line in (curve,baseline)]
    occupied=[]
    preferred={1:[(-65,22),(-70,35),(-75,50),(-100,80),(65,55)],
               2:[(0,-40),(-15,-35),(-35,-55),(-100,-70),(80,-55)],
               3:[(65,-40),(-35,-65),(-130,-65),(60,60)] if end_i is not None else [(-30,-85),(-25,-65),(-50,-45),(-70,65)]}
    for number,(i,label,color) in enumerate(nodes,1):
        candidates=preferred[number]+[(x,y) for y in (-90,-65,55,85,110,135,160,-120,-150)
                                      for x in (-160,-130,-80,0,80,130)]
        placed=False
        for offset in candidates:
            node_text=(f'截至{f.date.iloc[i]:%m-%d}尚未修复' if number==3 and end_i is None
                       else f'{label} {f.date.iloc[i]:%m-%d}')
            note=ax.annotate(f'{node_text}\n归一化价格 {p.iloc[i]:.1f}',
                xy=(f.date.iloc[i],p.iloc[i]),xytext=offset,textcoords='offset points',
                fontsize=10,color=INK,ha='center',va='center',zorder=4,
                bbox={'boxstyle':'round,pad=.3','facecolor':'white','edgecolor':'none'},
                arrowprops={'arrowstyle':'-','color':'#8A9DAA','lw':1,'shrinkA':5,'shrinkB':10})
            fig.canvas.draw()
            box=note.get_bbox_patch().get_window_extent(fig.canvas.get_renderer())
            clear=box.expanded(1.05,1.12)
            inside=ax.bbox.contains(clear.x0,clear.y0) and ax.bbox.contains(clear.x1,clear.y1)
            if (inside and not any(path.intersects_bbox(clear,filled=False) for path in paths)
                and not any(clear.overlaps(b) for b in occupied)
                and not any(clear.overlaps(Bbox.from_bounds(x-12,y-12,24,24)) for x,y in points)):
                occupied.append(clear);placed=True;break
            note.remove()
        assert placed, f'{code}节点{number}未找到不遮挡曲线的标注位置'
    foot(fig)
    export(fig,name)


def main():
    tests()
    snapshot=json.loads((DATA/'ETF行情.json').read_text(encoding='utf-8'))
    metadata=json.loads((DATA/'采集元数据.json').read_text(encoding='utf-8'))
    frames,records,all_events={}, {}, []
    for code,item in snapshot.items():
        f=pd.DataFrame(item['series']); f['date']=pd.to_datetime(f.date)
        assert f.date.is_unique and f.date.is_monotonic_increasing
        r={'code':code,'name':item['name'],**max_drawdown_record(f)}
        records[code]=r;frames[code]=f
        f['running_high']=f.close.cummax()
        f['drawdown_pct']=(f.close/f.running_high-1)*100
        # 与逐项前缀最大值和所有高低组合的穷举比较独立核对。
        brute=min(float(f.close.iloc[j]/max(f.close.iloc[:j+1])-1) for j in range(len(f)))
        assert abs(brute*100-r['max_drawdown_pct'])<1e-10
        for t in range(len(f)):
            assert abs(f.drawdown_pct.iloc[t]-(f.close.iloc[t]/max(f.close.iloc[:t+1])-1)*100)<1e-10
        if r['recovery_i'] is not None:
            assert f.close.iloc[r['recovery_i']]>=r['peak_close']
            assert (f.close.iloc[r['trough_i']+1:r['recovery_i']]<r['peak_close']).all()
            assert r['underwater_days']==r['decline_days']+r['recovery_days']
        else:
            assert r['recovery_days'] is None and (f.close.iloc[r['trough_i']+1:]<r['peak_close']).all()
        for e in drawdown_events(f):all_events.append({'code':code,'name':item['name'],**e})
        f.insert(0,'code',code);f.insert(1,'name',item['name'])
        f.to_csv(DATA/f'{code}_回撤日度.csv',index=False,encoding='utf-8-sig',date_format='%Y-%m-%d')
    table=pd.DataFrame(records.values()).sort_values('max_drawdown_pct').reset_index(drop=True)
    table.to_csv(DATA/'最大回撤与修复.csv',index=False,encoding='utf-8-sig')
    events=pd.DataFrame(all_events)
    events.to_csv(DATA/'全部回撤事件.csv',index=False,encoding='utf-8-sig')
    major=events[events.depth_pct<=-5].copy()
    major.to_csv(DATA/'回撤超过5%的事件.csv',index=False,encoding='utf-8-sig')
    closed=major[major.status=='已修复']; opened=major[major.status=='尚未修复']
    repaired=table[table.status=='已修复']
    closed_code=str(repaired.sort_values('max_drawdown_pct').iloc[0].code) if len(repaired) else None
    closed_example=None
    if closed_code is None and len(closed):
        e=closed.sort_values('depth_pct').iloc[0].to_dict()
        closed_code=str(e['code'])
        f=frames[closed_code]
        lookup={str(d.date()):i for i,d in enumerate(f.date)}
        peak,trough,recovery=lookup[e['peak_date']],lookup[e['trough_date']],lookup[e['recovery_date']]
        closed_example={**e,'max_drawdown_pct':e['depth_pct'],'peak_i':peak,'trough_i':trough,'recovery_i':recovery,
                        'peak_close':float(f.close.iloc[peak]),'trough_close':float(f.close.iloc[trough])}
    open_code=str(table[table.status=='尚未修复'].iloc[0].code) if (table.status=='尚未修复').any() else None
    summary={'start':metadata['start'],'end':metadata['end'],'entities':len(table),'price_observations':metadata['calendar_rows'],
             'trading_day_intervals':metadata['calendar_rows']-1,'max_events_repaired':len(repaired),
             'max_events_unrepaired':int((table.status=='尚未修复').sum()),
             'maximum_drawdown_records':table.to_dict(orient='records'),
             'closed_example_code':closed_code,'unrepaired_example_code':open_code,
             'closed_example_record':closed_example if closed_example is not None else (records.get(closed_code) if closed_code else None),
             'all_events':len(events),'major_events':len(major),'major_repaired_events':len(closed),'major_unrepaired_events':len(opened),
             'major_repaired_median_days':float(closed.recovery_days.median()) if len(closed) else None,
             'major_repaired_mean_days':float(closed.recovery_days.mean()) if len(closed) else None,
             'major_repaired_min_days':int(closed.recovery_days.min()) if len(closed) else None,
             'major_repaired_max_days':int(closed.recovery_days.max()) if len(closed) else None,
             'cross_source_checked_entities':sum(c['cross_source_status']=='passed' for c in metadata['cross_checks'].values()),
             'boundary_peak_entities':int(table.peak_at_window_start.sum())}
    (ROOT/'分析结果.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'验收结果.json').write_text(json.dumps({'status':'passed','rows':len(table),'daily_observations':sum(len(f) for f in frames.values()),
       'checks':{'calendar_aligned':True,'brute_force_drawdown':True,'first_recovery_close':True,'duration_identities':True,'unrepaired_recovery_is_null':True,'known_sequence_edge_cases':True},
       'sources':metadata['cross_checks'],'scope':'前复权市场收盘价；窗口起点重新建立高点，不代表全历史或个人持仓成本'},ensure_ascii=False,indent=2),encoding='utf-8')

    # 主图：同一行同时看幅度和时间；未完成修复用斜纹明确区分。
    fig,axes=plt.subplots(1,2,figsize=(14,10),gridspec_kw={'width_ratios':[1,1.65]},facecolor='white')
    fig.subplots_adjust(left=.16,right=.97,top=.78,bottom=.18,wspace=.13)
    y=np.arange(len(table)); labels=[f'{r.name}  {r.code}' for r in table.itertuples()]
    for ax in axes:style(ax);ax.set_ylim(len(table)-.4,-.8)
    axes[0].barh(y,-table.max_drawdown_pct,color=BLUE,height=.58)
    axes[0].set_yticks(y,labels,fontsize=10);axes[1].set_yticks(y,[])
    max_depth=float(-table.max_drawdown_pct.min());axes[0].set_xlim(0,max_depth*1.35)
    for i,r in table.iterrows():
        axes[0].text(-r.max_drawdown_pct+.6,i,f'{r.max_drawdown_pct:.1f}%',va='center',color=INK,fontsize=10)
        duration=r.recovery_days if r.status=='已修复' else r.observed_after_trough_days
        axes[1].barh(i,r.decline_days,color=BLUE,height=.58)
        axes[1].barh(i,duration,left=r.decline_days,color=GOLD if r.status=='已修复' else '#DCE4E9',edgecolor=GOLD if r.status=='已修复' else '#7E929F',hatch=None if r.status=='已修复' else '///',height=.58,lw=.5)
        text=f'下跌{r.decline_days} + 修复{int(duration)}' if r.status=='已修复' else f'下跌{r.decline_days} + 观察{int(duration)} →'
        axes[1].text(r.decline_days+duration+3,i,text,va='center',fontsize=9,color=INK)
    axes[1].set_xlim(0,float(table.underwater_days.max())*1.65)
    axes[0].set_xlabel('最大回撤幅度 / %');axes[1].set_xlabel('从高点开始的交易日间隔')
    axes[0].set_title('幅度：窗口内跌得最深的一次',loc='left',fontsize=13,color=INK,pad=18)
    axes[1].set_title('时间：下跌 + 修复，或下跌 + 已观察',loc='left',fontsize=13,color=INK,pad=18)
    fig.suptitle('ETF回撤有多深，修复用了多久',x=.06,ha='left',y=.97,fontsize=28,weight='bold',color=INK)
    fig.text(.06,.91,f'16只代表ETF  |  2025-09-30—2026-09-30  |  {len(repaired)}次最大回撤已修复，{summary["max_events_unrepaired"]}次尚未修复',fontsize=12,color=MUTED)
    fig.text(.06,.86,'蓝色：高点→低点   橙色：低点→首次回到高点   斜纹：截至观察日尚未修复，不是预测时长',fontsize=11,color=INK)
    fig.text(.06,.085,'每只ETF只取窗口内最大回撤事件；时间按交易日间隔计算。未修复事件在09-30截止。',fontsize=10,color=MUTED)
    foot(fig);export(fig,'最大回撤与修复总览')
    if closed_code:example_chart(closed_code,frames,records,'已修复案例',closed_example)
    if open_code:example_chart(open_code,frames,records,'尚未修复案例')

    # 概念图的数据来自代数关系，不是模拟市场行情。
    drops=np.array([.1,.2,.3,.4,.5]);rises=drops/(1-drops)*100
    fig,ax=plt.subplots(figsize=(10,5.8),facecolor='white')
    fig.subplots_adjust(left=.12,right=.92,top=.73,bottom=.20)
    style(ax);bars=ax.bar(np.arange(5),rises,color=GOLD,width=.55)
    ax.set_xticks(np.arange(5),[f'跌{d*100:.0f}%' for d in drops]);ax.set_ylim(0,118)
    ax.set_ylabel('从低点回到原高点所需涨幅 / %')
    ax.bar_label(bars,labels=[f'需涨{r:.1f}%' for r in rises],padding=5,color=INK,fontsize=12)
    fig.suptitle('跌幅和回本所需涨幅，并不对称',x=.06,ha='left',y=.96,fontsize=23,weight='bold',color=INK)
    fig.text(.06,.84,'数学关系：所需涨幅 = 跌幅 /（1 − 跌幅）；只说明幅度，不给出时间预测。',fontsize=11,color=MUTED)
    foot(fig,'数据：代数公式直接计算；例如100跌到80，再回100需要从80上涨25%。');export(fig,'跌幅与所需涨幅')

    fig,axes=plt.subplots(1,2,figsize=(12,6.5),facecolor='white')
    fig.subplots_adjust(left=.08,right=.96,top=.74,bottom=.20,wspace=.27)
    for ax in axes:style(ax);ax.grid(axis='y',color=GRID,lw=.7);ax.set_xlabel('该次最大回撤幅度 / %');ax.set_xlim(0,float(-major.depth_pct.min())*1.12)
    axes[0].scatter(-closed.depth_pct,closed.recovery_days,color=GOLD,s=65,alpha=.75,edgecolors='white')
    axes[1].scatter(-opened.depth_pct,opened.observed_after_trough_days,facecolors='none',edgecolors=BLUE,marker='^',s=65,lw=1.3)
    axes[0].set_ylabel('低点→修复实际交易日数');axes[1].set_ylabel('低点→截止已观察交易日数')
    axes[0].set_title(f'已修复事件：{len(closed)}次',loc='left',color=INK,fontsize=14,pad=15)
    axes[1].set_title(f'未修复事件：{len(opened)}次',loc='left',color=INK,fontsize=14,pad=15)
    fig.suptitle('回撤至少5%的事件：修复记录与观察记录分开',x=.06,ha='left',y=.96,fontsize=22,weight='bold',color=INK)
    fig.text(.06,.85,'每点是一只ETF的一次互不重叠回撤事件；两图纵轴含义不同，不能合并计算平均修复时间。',fontsize=10,color=MUTED)
    foot(fig,'来源：同一窗口内16只ETF收盘价；5%为本例事先设定的展示筛选线，ETF之间可能同期共变。');export(fig,'回撤事件与修复时间')
    print(json.dumps({k:v for k,v in summary.items() if k!='maximum_drawdown_records'},ensure_ascii=True))


if __name__=='__main__':
    main()
