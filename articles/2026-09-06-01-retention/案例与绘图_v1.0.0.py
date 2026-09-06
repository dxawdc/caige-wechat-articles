"""v1.0.0 | 2026-09-06 | 教学模拟案例：SQL算留存：别把还没到第7天的用户算成流失。"""
from pathlib import Path
import runpy
globals().update({k:v for k,v in runpy.run_path(str(Path(__file__).with_name("绘图工具_v1.0.0.py"))).items() if not k.startswith("__")})

import sqlite3
from datetime import date,timedelta
con=sqlite3.connect(':memory:')
users=[];logs=[]
spec=[('2026-08-01',100,[60,45,35]),('2026-08-02',200,[100,80,60]),('2026-08-05',80,[48,36,0]),('2026-08-08',120,[72,0,0])]
for d,n,counts in spec:
    for i in range(n):
        uid=f'{d}-{i:03d}'; users.append((uid,d));logs.append((uid,d+' 08:00:00'))
        for lag,count in zip([1,3,7],counts):
            day=(date.fromisoformat(d)+timedelta(days=lag)).isoformat()
            if i<count and day<='2026-08-09':logs.extend([(uid,day+' 09:00:00'),(uid,day+' 18:00:00')])
u=pd.DataFrame(users,columns=['user_id','signup_date']);l=pd.DataFrame(logs,columns=['user_id','login_time'])
u.to_sql('users',con,index=False);l.to_sql('logins',con,index=False);csv(u,'注册用户');csv(l,'登录日志')
# 本例注册日期与登录时间已按 Asia/Shanghai 转为本地日期。
sql="""WITH daily AS (
  SELECT DISTINCT user_id, date(login_time) AS login_day
  FROM logins WHERE date(login_time) <= :asof
), targets(day_n) AS (VALUES (1),(3),(7))
SELECT u.signup_date, t.day_n,
       COUNT(DISTINCT u.user_id) AS new_users,
       CASE WHEN date(u.signup_date, '+'||t.day_n||' days') <= :asof
            THEN COUNT(DISTINCT d.user_id) END AS retained,
       CASE WHEN date(u.signup_date, '+'||t.day_n||' days') <= :asof
            THEN 1.0*COUNT(DISTINCT d.user_id)
                 /COUNT(DISTINCT u.user_id) END AS rate
FROM users u CROSS JOIN targets t
LEFT JOIN daily d ON d.user_id=u.user_id
 AND d.login_day=date(u.signup_date, '+'||t.day_n||' days')
WHERE u.signup_date <= :asof
GROUP BY u.signup_date,t.day_n
ORDER BY u.signup_date,t.day_n;"""
(ROOT/'留存查询_v1.0.0.sql').write_text(sql,encoding='utf-8')
out=pd.read_sql_query(sql,con,params={'asof':'2026-08-09'});csv(out,'留存结果')
d7=out[out.day_n.eq(7)];mature=d7[d7.rate.notna()]
good=mature.retained.sum()/mature.new_users.sum();wrong=mature.retained.sum()/d7.new_users.sum()
assert len(u)==500 and int(mature.retained.sum())==95 and int(mature.new_users.sum())==300
assert np.isclose(good,95/300) and np.isclose(wrong,.19)
assert d7.rate.isna().sum()==2 and out.rate.dropna().between(0,1).all()
matrix=out.pivot(index='signup_date',columns='day_n',values='rate').to_numpy()
fig,ax=figure('灰色格子，是还没等到那一天','截至 2026-08-09 当日结束；D0 为注册当天；单位：%')
cmap=plt.get_cmap('Blues').copy();cmap.set_bad(GRAY)
ax.imshow(np.ma.masked_invalid(matrix),vmin=0,vmax=1,cmap=cmap,aspect='auto')
ax.set_xticks(range(3),['D1','D3','D7']);ax.set_yticks(range(4),[f'{d[5:]}\n新增 {n}' for d,n,_ in spec])
for (r,c),v in np.ndenumerate(matrix):ax.text(c,r,'未到期' if np.isnan(v) else f'{v:.0%}',ha='center',va='center',color=INK,weight='bold')
save(fig,'01_留存矩阵')
bar('同一批 95 人，换个分母就差很多','D7：仅 08-01、08-02 批次已成熟；后两批不能填零', ['错误：全体500人','正确：成熟300人'],[wrong*100,good*100],'02_分母对比','D7 留存率（%）',[ORANGE,BLUE])
result({'passed':True,'new_users':500,'mature_users':300,'retained_d7':95,'correct_d7_pct':round(good*100,2),'wrong_d7_pct':19,'missing_d7_cohorts':2,'checks':7})
