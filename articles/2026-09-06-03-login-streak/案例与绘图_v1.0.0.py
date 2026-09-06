"""v1.0.0 | 2026-09-06 | 教学模拟案例：SQL算连续登录：去重、断档和跨月怎么处理。"""
from pathlib import Path
import runpy
globals().update({k:v for k,v in runpy.run_path(str(Path(__file__).with_name("绘图工具_v1.0.0.py"))).items() if not k.startswith("__")})

import sqlite3
con=sqlite3.connect(':memory:')
days={'A':['2026-07-30','2026-07-31','2026-08-01','2026-08-01','2026-08-03','2026-08-04'],'B':['2026-07-31','2026-08-01','2026-08-02','2026-08-03','2026-08-04'],'C':['2026-07-30','2026-08-01','2026-08-03'],'D':['2026-08-04']}
logs=pd.DataFrame([(u,d) for u,dates in days.items() for d in dates],columns=['user_id','login_day'])
logs.to_sql('logins',con,index=False);csv(logs,'登录日志')
sql="""WITH daily AS (
  SELECT DISTINCT user_id, date(login_day) AS day
  FROM logins WHERE login_day <= :asof
), numbered AS (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY user_id ORDER BY day
  ) AS rn FROM daily
), islands AS (
  SELECT user_id, date(day, '-'||rn||' days') AS grp,
         MIN(day) AS start_day, MAX(day) AS end_day,
         COUNT(*) AS days
  FROM numbered GROUP BY user_id,grp
)
SELECT user_id, MAX(days) AS longest_streak,
       MAX(CASE WHEN end_day=:asof THEN days ELSE 0 END) AS current_streak
FROM islands GROUP BY user_id ORDER BY user_id;"""
(ROOT/'连续登录_v1.0.0.sql').write_text(sql,encoding='utf-8')
out=pd.read_sql_query(sql,con,params={'asof':'2026-08-04'});csv(out,'连续登录结果')
expected={'A':(3,2),'B':(5,5),'C':(1,0),'D':(1,1)}
for row in out.itertuples():assert (row.longest_streak,row.current_streak)==expected[row.user_id]
assert len(logs)==15 and len(logs.drop_duplicates())==14
timeline=pd.date_range('2026-07-30','2026-08-04');matrix=np.array([[int(d.strftime('%Y-%m-%d') in dates) for d in timeline] for dates in days.values()])
fig,ax=figure('跨月不断档，漏一天才断档','已按用户与自然日去重；深色=有登录，浅色=无登录')
from matplotlib.colors import ListedColormap
ax.imshow(matrix,cmap=ListedColormap([GRAY,BLUE]),vmin=0,vmax=1,aspect='auto')
ax.set_xticks(range(6),[d.strftime('%m-%d') for d in timeline]);ax.set_yticks(range(4),list(days))
for (r,c),v in np.ndenumerate(matrix):ax.text(c,r,'有' if v else '—',ha='center',va='center',color='white' if v else INK)
save(fig,'01_登录日历')
table('最长连续，不是当前连续','当前连续要求最后一天正好是 2026-08-04；单位：天',out.rename(columns={'user_id':'用户','longest_streak':'最长连续','current_streak':'当前连续'}),'02_连续结果')
result({'passed':True,'raw_rows':15,'unique_user_days':14,'streaks':expected,'checks':6})
