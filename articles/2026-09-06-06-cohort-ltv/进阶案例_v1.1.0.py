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
new_users=100
gross=70000       # 7 日成功支付流水，分
refund=5000       # 本例假设截至观察日已发生的退款，分
net=gross-refund
share=net*30//100 # 独立假设：净流水的 30% 分成
variable=6500    # 独立假设：可变服务成本，分
contribution=net-share-variable
gross_ltv=gross/new_users/100
net_ltv=net/new_users/100
contribution_ltv=contribution/new_users/100
assert (gross_ltv,net_ltv,contribution_ltv)==(7,6.5,3.9)
acquisition=50000
margin_after_acquisition=contribution-acquisition
assert margin_after_acquisition==-11000
# END MAIN
# BEGIN COHORT
groups=pd.DataFrame({'new_users':[100,300],'revenue_cent':[70000,150000]})
groups['ltv']=groups.revenue_cent/groups.new_users/100
pooled_ltv=groups.revenue_cent.sum()/groups.new_users.sum()/100
assert pooled_ltv==5.5
assert groups.ltv.mean()==6
# END COHORT
assert gross/acquisition==1.4 and margin_after_acquisition/100==-110
rows=[['成功支付',gross/100,gross_ltv],['扣已发生退款',net/100,net_ltv],
      ['再扣分成与可变成本',contribution/100,contribution_ltv]]
frame=pd.DataFrame(rows,columns=['计算口径','批次金额/元','人均/元'])
frame.to_csv(ROOT/'数据/价值口径对照_v1.1.0.csv',index=False,encoding='utf-8-sig')
explain('同一批 100 人，三种价值口径','独立情景：流水 700，退款 50，分成 195，可变成本 65 元',frame)
finish({'gross_ltv':7,'net_ltv':6.5,'contribution_ltv':3.9,'after_acquisition_yuan':-110,'pooled_ltv':5.5},6)
