"""v1.0.0 | 2026-09-06 | 教学模拟案例：游戏活动漏斗：人数都对，转化率却错了。"""
from pathlib import Path
import runpy
globals().update({k:v for k,v in runpy.run_path(str(Path(__file__).with_name("绘图工具_v1.0.0.py"))).items() if not k.startswith("__")})

events=[]
start=pd.Timestamp('2026-08-01 10:00:00')
def add(user,event,hours):events.append((user,event,start+pd.Timedelta(hours=hours)))
# 100人进入。70人之后点击；其中40人在24小时内依序领取，10人超时。
for i in range(100):
    u=f'U{i:03}';add(u,'enter',0)
    if i<70:add(u,'click',1)
    if i<40:add(u,'claim',2)
    elif i<50:add(u,'claim',25)
    elif 70<=i<80:add(u,'click',-2);add(u,'claim',-1)
# 20人只有领取埋点，没有进入与点击。
for i in range(100,120):add(f'U{i:03}','claim',3)
events.extend(events[:10]) # 模拟重复上报
df=pd.DataFrame(events,columns=['user_id','event','event_time']);csv(df,'活动事件')
first=df[df.event.eq('enter')].groupby('user_id').event_time.min()
counts=[len(first),0,0];members=[]
for user,t0 in first.items():
    user_events=df[df.user_id.eq(user)]
    end=t0+pd.Timedelta(hours=24)
    clicks=user_events.loc[user_events.event.eq('click') & user_events.event_time.gt(t0) & user_events.event_time.le(end),'event_time']
    if clicks.empty:continue
    t1=clicks.min();counts[1]+=1
    claims=user_events.loc[user_events.event.eq('claim') & user_events.event_time.gt(t1) & user_events.event_time.le(end),'event_time']
    if not claims.empty:counts[2]+=1;members.append(user)
naive=[df.loc[df.event.eq(e),'user_id'].nunique() for e in ['enter','click','claim']]
assert counts==[100,70,40] and naive==[100,80,80]
assert len(set(members))==40 and not set(members)&{f'U{i:03}' for i in range(40,120)}
assert counts[0]>=counts[1]>=counts[2]
bar('独立统计事件，不能直接当漏斗','错误做法：各事件独立去重，未约束用户路径与时间窗',['进入活动','点击参与','领取奖励'],naive,'01_独立计数','去重用户数（人）',ORANGE)
bar('同一批人，按顺序走完才算转化','首次进入后 24 小时；严格 enter < click < claim',['进入活动','有效点击','有效领取'],counts,'02_有序漏斗','去重用户数（人）',BLUE)
result({'passed':True,'naive':naive,'ordered':counts,'total_conversion_pct':40,'click_to_claim_pct':round(40/70*100,2),'window_hours':24,'checks':4})
