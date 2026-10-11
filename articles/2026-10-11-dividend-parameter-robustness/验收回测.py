"""独立现金/份额账本复算，验证无前视、分红时点、费用与持有基准。"""
from pathlib import Path
import json,math
import numpy as np
import 回测研究 as bt
BASE=Path(__file__).resolve().parent
r=json.loads((BASE/'结果/研究结果.json').read_text(encoding='utf-8'));checks=[]
for c,m in bt.DATA.items():
    rows=m['rows'];lookup={x['date']:i for i,x in enumerate(rows)};path=r['results'][c]['timing'];trades={t['trade_date']:t for t in path['transactions']}
    # 按原始市场价格维护实际份额；分红在除息日开盘理论再投。
    cash=1.;shares=0.;eq=[1.]
    for day in path['dates'][1:]:
        row=rows[lookup[day]];o=row['market_open'];cl=row['market_close'];shares*=1+row['dividend']/o
        if day in trades:
            t=trades[day];assert t['signal_date']<day and lookup[day]-lookup[t['signal_date']]==1
            if t['side']=='买入':shares=cash*(1-.0003)/o;cash=0.
            else:cash=shares*o*(1-.0003);shares=0.
        eq.append(cash+shares*cl)
    assert np.allclose(eq,path['nav'],rtol=1e-11,atol=1e-11)
    # 使用直接求均值的独立信号判断，核对每日仓位及两侧阈值。
    state=0
    for day,expected in zip(path['dates'][1:],path['positions'][1:]):
        i=lookup[day];cl=rows[i-1]['close'];mean=sum(x['close'] for x in rows[i-200:i])/200
        if state==0 and cl<mean*.95:state=1
        elif state==1 and cl>mean*1.05:state=0
        assert state==expected,(c,day,'symmetric band signal mismatch')
    # 修改未来行情，不得改变此前交易与净值。
    original=bt.DATA[c]['rows'];cut='2024-06-28';future=[dict(x) for x in original]
    for x in future:
        if x['date']>cut:
            for k in ['open','close','high','low']:x[k]*=3
    bt.DATA[c]['rows']=future;changed=bt.run(c);bt.DATA[c]['rows']=original
    prefix=sum(x<=cut for x in path['dates']);assert np.allclose(changed['nav'][:prefix],path['nav'][:prefix],rtol=0,atol=1e-11)
    assert [t for t in changed['transactions'] if t['trade_date']<=cut]==[t for t in path['transactions'] if t['trade_date']<=cut]
    h=r['results'][c]['hold'];first=rows[lookup[h['dates'][1]]];last=rows[lookup[h['dates'][-1]]]
    assert math.isclose(h['nav'][-1],last['close']/first['open']*(1-.0003),rel_tol=1e-12)
    dd=np.array(eq)/np.maximum.accumulate(eq)-1;assert abs(dd.min()-path['summary']['max_drawdown'])<1e-12
    chosen=max(r['grid'][c],key=lambda x:x['train']['cagr']);assert chosen['window']==r['selection'][c]['chosen_by_2022_2023']['window'] and chosen['band']==r['selection'][c]['chosen_by_2022_2023']['band']
    checks.append({'code':c,'ledger_rows':len(eq),'cash_share_ledger_max_error':float(np.max(np.abs(np.array(eq)-path['nav']))),'symmetric_daily_signal':'passed','future_price_perturbation':'passed','baseline_formula':'passed','training_only_selection':'passed'})
report={'status':'passed','tests':checks,'qualifications':['MA价格条件实验，未包含历史PE/股息率筛选','历史留出检验，不是2026年发布后的真实样本外','除息日开盘理论再投，与真实到账及整数份额有差异']}
(BASE/'结果/验收回测.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
