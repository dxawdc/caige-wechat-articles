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

# BEGIN MAIN
cohorts=pd.DataFrame({
    'signup':['2026-08-01','2026-08-02','2026-08-05','2026-08-08'],
    'new_users':[100,200,80,120],
    'retained_d7':[35,60,None,None],
})
cutoff=pd.Timestamp('2026-08-09')
cohorts['mature']=pd.to_datetime(cohorts.signup)+pd.Timedelta(days=7)<=cutoff
eligible=cohorts.loc[cohorts.mature]
assert eligible.retained_d7.notna().all()
denominator=int(eligible.new_users.sum())
numerator=int(eligible.retained_d7.sum())
rate=numerator/denominator if denominator else None
coverage=denominator/cohorts.new_users.sum()
# END MAIN
# BEGIN TEST
def safe_rate(new_users,retained,mature):
    if not mature or new_users==0:return None
    if retained is None:raise ValueError('成熟窗口缺少数据，需排查')
    if not 0<=retained<=new_users:raise ValueError('人数越界')
    return retained/new_users
assert safe_rate(100,0,True)==0
assert safe_rate(100,None,False) is None
assert safe_rate(0,0,True) is None
# END TEST
assert denominator==300 and numerator==95
assert math.isclose(rate,95/300) and math.isclose(coverage,.6)
earlier=cohorts.loc[pd.to_datetime(cohorts.signup)+pd.Timedelta(days=7)<=pd.Timestamp('2026-08-08')]
assert earlier.new_users.sum()==100 and earlier.retained_d7.sum()==35
for args in [(100,None,True),(100,101,True)]:
    try:safe_rate(*args);raise AssertionError('应拒绝异常')
    except ValueError:pass
cohorts.to_csv(ROOT/'数据/成熟批次审计_v1.1.0.csv',index=False,encoding='utf-8-sig')
explain('同一个 95 人，为什么有三个答案','D7；成熟批次新增 100+200 人；全部批次新增 500 人',pd.DataFrame([
 ['全量分母','95 / 500','19.00%','混入未成熟'],
 ['批次简单平均','(35%+30%) / 2','32.50%','人数权重丢失'],
 ['成熟批次汇总','95 / 300','31.67%','本例正确口径'],
 ['观察覆盖率','300 / 500','60.00%','不是留存率'],
],columns=['算法','计算','结果','解释']))
finish({'numerator':95,'denominator':300,'coverage':.6,'rate':rate},8)
