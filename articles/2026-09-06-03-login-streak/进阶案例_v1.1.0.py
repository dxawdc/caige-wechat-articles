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

days=['2026-07-30','2026-07-31','2026-08-01','2026-08-01','2026-08-03','2026-08-04']
con=sqlite3.connect(':memory:')
pd.DataFrame({'user_id':['A']*6,'login_day':days}).to_sql('logins',con,index=False)
# BEGIN SQL
sql="""WITH daily AS (
  SELECT DISTINCT user_id, date(login_day) AS day FROM logins
  WHERE date(login_day) <= :asof
), previous AS (
  SELECT *, LAG(day) OVER (
    PARTITION BY user_id ORDER BY day
  ) AS prev_day FROM daily
), flags AS (
  SELECT *, CASE WHEN prev_day IS NULL
    OR julianday(day)-julianday(prev_day)<>1
    THEN 1 ELSE 0 END AS new_segment FROM previous
), grouped AS (
  SELECT *, SUM(new_segment) OVER (
    PARTITION BY user_id ORDER BY day
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS segment_id FROM flags
)
SELECT user_id, segment_id, MIN(day) AS start_day,
       MAX(day) AS end_day, COUNT(*) AS days
FROM grouped GROUP BY user_id,segment_id
ORDER BY user_id,start_day;"""
segments=pd.read_sql_query(sql,con,params={'asof':'2026-08-04'})
# END SQL
assert segments.days.tolist()==[3,2]
assert segments.start_day.tolist()==['2026-07-30','2026-08-03']
old=(ROOT/'连续登录_v1.0.0.sql').read_text(encoding='utf-8')
summary=pd.read_sql_query(old,con,params={'asof':'2026-08-04'})
assert summary.iloc[0].longest_streak==3 and summary.iloc[0].current_streak==2
empty=pd.read_sql_query(sql,con,params={'asof':'2026-07-29'});assert empty.empty
con.execute("INSERT INTO logins VALUES ('A','2026-08-02')")
assert pd.read_sql_query(sql,con,params={'asof':'2026-08-04'}).days.tolist()==[6]
patched=pd.read_sql_query(old,con,params={'asof':'2026-08-04'})
assert patched.iloc[0].longest_streak==6 and patched.iloc[0].current_streak==6
con.execute("DELETE FROM logins WHERE login_day='2026-08-04'")
assert pd.read_sql_query(old,con,params={'asof':'2026-08-04'}).iloc[0].current_streak==0
unique=sorted(set(days));rows=[]
for i,d in enumerate(unique,1):
    anchor=(pd.Timestamp(d)-pd.Timedelta(days=i)).strftime('%m-%d')
    gap='首日' if i==1 else str((pd.Timestamp(d)-pd.Timestamp(unique[i-2])).days)
    rows.append((d[5:],i,anchor,gap,1 if i<=3 else 2))
frame=pd.DataFrame(rows,columns=['登录日','序号','日期减序号','距上次/天','段编号'])
frame.to_csv(ROOT/'数据/连续段推导_v1.1.0.csv',index=False,encoding='utf-8-sig')
segments.to_csv(ROOT/'数据/LAG分段结果_v1.1.0.csv',index=False,encoding='utf-8-sig')
explain('两种方法，看的是同一个断点','用户 A；同日先去重；08-02 未登录，08-03 开始新段',frame)
finish({'segments':[3,2],'both_methods_agree':True,'empty_before_first_day':True},4)
