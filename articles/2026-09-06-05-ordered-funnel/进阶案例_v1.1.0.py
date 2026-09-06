"""v1.1.0 | 2026-09-06 | 教学模拟数据，运行断言并生成解释图。"""
from pathlib import Path
import json,runpy,math,sqlite3
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parent
g=runpy.run_path(str(ROOT/'绘图工具_v1.0.0.py'))
plt=g['plt'];figure=g['figure']
def explain(title,note,frame):
    fig,ax=figure(title,note);ax.axis('off')
    widths=[.23,.12,.65] if list(frame.columns)==['路径结果','人数','事件证据'] else None
    t=ax.table(cellText=frame.astype(str).values,colLabels=frame.columns,colWidths=widths,cellLoc='center',bbox=[-.06,-.04,1.1,1.10])
    t.auto_set_font_size(False);t.set_fontsize(11)
    for (r,c),cell in t.get_celld().items():
        cell.set_edgecolor('white');cell.set_linewidth(2)
        cell.set_facecolor('#e9f1fa' if r==0 else ('#f4f6f9' if r%2 else 'white'))
        if r==0:cell.set_text_props(weight='bold')
    fig.savefig(ROOT/'图片/03_进阶解释_v1.1.0.png',dpi=200);plt.close(fig)
def finish(values,checks):
    (ROOT/'结果/进阶验收_v1.1.0.json').write_text(json.dumps({'version':'v1.1.0','simulated':True,'passed':True,'checks':checks,**values},ensure_ascii=False,indent=2),encoding='utf-8')

source=pd.read_csv(ROOT/'数据/活动事件_v1.0.0.csv',parse_dates=['event_time'])
# BEGIN MAIN
first=source[source.event.eq('enter')].groupby('user_id').event_time.min()
audit=[]
for user,t0 in first.items():
    events=source[source.user_id.eq(user)]
    deadline=t0+pd.Timedelta(hours=24)
    clicks=events.loc[events.event.eq('click') & events.event_time.gt(t0)
        & events.event_time.le(deadline),'event_time']
    if clicks.empty:
        audit.append((user,'无有效点击'));continue
    t1=clicks.min()
    claims=events.loc[events.event.eq('claim') & events.event_time.gt(t1),'event_time']
    if (claims<=deadline).any():reason='完成转化'
    elif not claims.empty:reason='领取超时'
    else:reason='有效点击后无领取'
    audit.append((user,reason))
audit=pd.DataFrame(audit,columns=['user_id','reason'])
counts=audit.reason.value_counts()
# END MAIN
# BEGIN BOUNDARY
def converted(click_hour,claim_hour,window=24):
    return 0<click_hour<claim_hour<=window
assert converted(1,24)
assert not converted(1,24.001)
assert not converted(1,1)
assert not converted(-1,2)
# END BOUNDARY
assert counts.to_dict()=={'完成转化':40,'无有效点击':30,'有效点击后无领取':20,'领取超时':10}
assert len(audit)==100 and audit.user_id.nunique()==100
outsiders=set(source.loc[source.event.eq('claim'),'user_id'])-set(first.index)
assert len(outsiders)==20
assert converted(1,25,48) and not converted(1,25,24)
audit.to_csv(ROOT/'数据/用户路径审计_v1.1.0.csv',index=False,encoding='utf-8-sig')
explain('把 100 名进入用户分到四个去向','互斥归类；另外 20 名只有领取的用户不进入这 100 人分母',pd.DataFrame([
 ['完成转化',40,'enter < click < claim ≤ 24h'],
 ['领取超时',10,'有效点击后，24h 以外领取'],
 ['点击后无领取',20,'找到有效点击，未找到后续领取'],
 ['无有效点击',30,'其中 10 人只有进入前的旧点击'],
],columns=['路径结果','人数','事件证据']))
finish({'cohort':100,'converted':40,'late':10,'no_claim':20,'no_click':30,'outside_cohort_claimers':20},8)
