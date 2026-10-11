"""同口径比较持有与价格均线择时；预先固定网格，分段检验。"""
from pathlib import Path
from datetime import date
import json,csv,math
import numpy as np
BASE=Path(__file__).resolve().parent;OUT=BASE/'结果';OUT.mkdir(exist_ok=True)
DATA=json.loads((BASE/'数据/总回报行情.json').read_text(encoding='utf-8'))
START='2021-12-31';END='2026-09-30';CUT='2023-12-29'
WINDOWS=[100,120,140,160,180,182,200,220,250];BANDS=[.03,.04,.05,.06,.07,.08,.09,.10,.12]

def run(code,window=182,band=.07,start=START,end=END,hold=False,fee=.0003,cash=0.,delay=1):
    rows=DATA[code]['rows'];dates=[r['date'] for r in rows];close=np.array([r['close'] for r in rows]);op=np.array([r['open'] for r in rows])
    sums=np.r_[0.,np.cumsum(close)];ma=np.full(len(close),np.nan);ma[window-1:]=(sums[window:]-sums[:-window])/window
    indices=[i for i,day in enumerate(dates) if start<=day<=end];assert len(indices)>50
    first,last=indices[0],indices[-1];assert first>=window and dates[first]==start
    nav=[1.];positions=[0];turns=[];pos=0;buy=None;completed=[]
    for i in indices[1:]:
        dt=(date.fromisoformat(dates[i])-date.fromisoformat(dates[i-1])).days
        # 先按旧仓位计入隔夜价格变化/现金计息，再于当日开盘按前一日收盘信号成交。
        at_open=nav[-1]*(pos*op[i]/close[i-1]+(1-pos)*(1+cash)**(dt/365.25))
        sig=i-delay;target=pos
        if hold:target=1
        elif pos==0 and close[sig]<ma[sig]:target=1
        elif pos==1 and close[sig]>ma[sig]*(1+band):target=0
        if target!=pos:
            at_open*=1-fee
            turns.append({'signal_date':dates[sig],'trade_date':dates[i],'side':'买入' if target else '卖出','adjusted_open':op[i],'ma':float(ma[sig]),'signal_close':close[sig]})
            if target:buy=(dates[i],op[i])
            elif buy:
                completed.append({'entry':buy[0],'exit':dates[i],'return':op[i]/buy[1]*(1-fee)**2-1,'calendar_days':(date.fromisoformat(dates[i])-date.fromisoformat(buy[0])).days});buy=None
        pos=target;nav.append(at_open*(pos*close[i]/op[i]+1-pos));positions.append(pos)
    ds=[dates[i] for i in indices];nav=np.array(nav);positions=np.array(positions);dd=nav/np.maximum.accumulate(nav)-1
    days=(date.fromisoformat(ds[-1])-date.fromisoformat(ds[0])).days;ret=nav[-1]-1;cagr=nav[-1]**(365.25/days)-1
    daily=np.diff(nav)/nav[:-1];vol=float(daily.std(ddof=1)*np.sqrt(252));calmar=cagr/abs(dd.min()) if dd.min()<0 else None
    cash_streak=0;streak=0
    for p in positions[1:]:streak=streak+1 if p==0 else 0;cash_streak=max(cash_streak,streak)
    annual={}
    for year in sorted({s[:4] for s in ds[1:]}):
        idx=[k for k,s in enumerate(ds) if s.startswith(year)];a=max(0,idx[0]-1);b=idx[-1];annual[year]=float(nav[b]/nav[a]-1)
    summary={'code':code,'window':window,'band':band,'start':ds[0],'first_execution':ds[1],'end':ds[-1],'terminal':float(nav[-1]),'return':float(ret),'cagr':float(cagr),'max_drawdown':float(dd.min()),'volatility':vol,'calmar':calmar,'exposure':float(positions[1:].mean()),'trades':len(turns),'round_trips':len(completed),'win_rate':float(np.mean([t['return']>0 for t in completed])) if completed else None,'max_cash_streak':cash_streak,'annual':annual,'fee':fee,'cash_rate':cash,'delay':delay}
    return {'summary':summary,'dates':ds,'nav':nav.tolist(),'drawdown':dd.tolist(),'positions':positions.tolist(),'transactions':turns,'closed_trades':completed}

def main():
    results={};grids={};selection={};sensitivity={}
    for c in DATA:
        results[c]={'hold':run(c,hold=True),'timing':run(c),'cash2':run(c,cash=.02)}
        grids[c]=[]
        for w in WINDOWS:
            for b in BANDS:
                full=run(c,w,b);train=run(c,w,b,end=CUT);test=run(c,w,b,start=CUT)
                grids[c].append({'window':w,'band':b,'full':full['summary'],'train':train['summary'],'test':test['summary']})
        best=max(grids[c],key=lambda r:r['train']['cagr']);test_hold=run(c,start=CUT,hold=True);default=run(c,start=CUT)
        selection[c]={'chosen_by_2022_2023':{'window':best['window'],'band':best['band']},'train':best['train'],'test':best['test'],'test_hold':test_hold['summary'],'test_default':default['summary'],'test_winner_path':run(c,best['window'],best['band'],start=CUT)}
        sensitivity[c]={'fee':[run(c,fee=v)['summary'] for v in [0.,.0003,.001,.003]],'delay':[run(c,delay=v)['summary'] for v in [1,2,3]]}
    # 空仓时的价格变化仅作为“机会与保护”的事后分解，不构造可交易的最佳日策略。
    attribution={}
    for c,r in results.items():
        rows={x['date']:x for x in DATA[c]['rows']};t=r['timing'];dates=t['dates'];p=t['positions'];held=0.;flat=0.
        for i in range(1,len(dates)):
            prev=rows[dates[i-1]]['close'];o=rows[dates[i]]['open'];cl=rows[dates[i]]['close']
            held+=p[i-1]*math.log(o/prev)+p[i]*math.log(cl/o)
            flat+=(1-p[i-1])*math.log(o/prev)+(1-p[i])*math.log(cl/o)
        attribution[c]={'held_log_return':held,'flat_log_return':flat,'price_total_log_return':held+flat,'interpretation':'对数收益分解，空仓期间ETF价格变化，非策略收益；含基准日收盘到首日开盘'}
    payload={'start':START,'end':END,'train_end':CUT,'windows':WINDOWS,'bands':BANDS,'funds':{c:m['name'] for c,m in DATA.items()},'results':results,'grid':grids,'selection':selection,'sensitivity':sensitivity,'attribution':attribution,'method':{'price':'拆分校正场内OHLC，加现金分红除息日开盘理论再投；仅用已发生分红向前构建总回报价格','execution':'前一交易日收盘信号，下一交易日开盘成交','fee_per_side':.0003,'cash_default':0,'initial_position':0,'cash_sensitivity':.02,'valuation_filter':False,'terminal_liquidation':False,'grid_size_per_fund':len(WINDOWS)*len(BANDS),'holdout':'按时间划分的历史留出检验；2026年回看历史，不是真实发布后样本外'}}
    (OUT/'研究结果.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/'参数网格.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['代码','MA交易日','卖出乖离','区间','年化收益','最大回撤','持仓比例','调仓次数'])
        for c,grid in grids.items():
            for r in grid:
                for part in ['full','train','test']:
                    s=r[part];w.writerow([c,r['window'],r['band'],part,s['cagr'],s['max_drawdown'],s['exposure'],s['trades']])
    with (OUT/'基准策略交易记录.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['代码','信号日期','执行日期','方向','总回报序列开盘','信号收盘','信号MA182'])
        for c,r in results.items():
            for t in r['timing']['transactions']:w.writerow([c,t['signal_date'],t['trade_date'],t['side'],t['adjusted_open'],t['signal_close'],t['ma']])
    print(json.dumps({'base':{c:{k:v['summary'] for k,v in r.items()} for c,r in results.items()},'selected':{c:{k:v for k,v in s.items() if k!='test_winner_path'} for c,s in selection.items()}},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
