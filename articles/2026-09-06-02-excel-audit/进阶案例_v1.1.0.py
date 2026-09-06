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

from decimal import Decimal,InvalidOperation
import re
# BEGIN MAIN
def amount_to_cent(value):
    text=str(value).strip()
    if not re.fullmatch(r'-?[0-9]+(?:\.[0-9]{1,2})?',text):
        raise ValueError('金额格式不符合约定')
    amount=Decimal(text)
    if not amount.is_finite():raise ValueError('金额不是有限数')
    return int(amount*100)

values=['100','0.10','-20.00','1,200','待补','12.345','NaN']
audit=[]
for value in values:
    try:audit.append((value,amount_to_cent(value),'接受'))
    except ValueError:audit.append((value,None,'隔离'))
# END MAIN
# BEGIN ROUTE
def classify_order(group):
    # 每个元素为同一订单的一次报送，保留原始行 ID。
    parsed=[]
    for row in group:
        try:parsed.append(amount_to_cent(row['amount']))
        except ValueError:return '整单待核：含无效金额'
    if len(set(parsed))>1:return '整单待核：金额冲突'
    return '可用；其余相同记录计重复报送'
assert classify_order([{'amount':'400'},{'amount':'待补'}]).startswith('整单待核')
assert classify_order([{'amount':'400'},{'amount':'450'}]).endswith('金额冲突')
assert classify_order([{'amount':'300'},{'amount':'300.00'}]).startswith('可用')
# END ROUTE
assert [a[1] for a in audit]==[10000,10,-2000,None,None,None,None]
assert amount_to_cent('0.10')+amount_to_cent('0.20')==30
assert classify_order([{'amount':'300'},{'amount':'300'},{'amount':'301'}]).endswith('金额冲突')
frame=pd.DataFrame(audit,columns=['输入原值','金额（分）','处置'])
frame.to_csv(ROOT/'数据/金额格式审计_v1.1.0.csv',index=False,encoding='utf-8-sig')
display=frame.copy();display['金额（分）']=display['金额（分）'].apply(lambda x:'—' if pd.isna(x) else str(int(x)))
explain('金额先定义规则，再转换','仅接受普通十进制、最多两位小数；负数是否业务有效另判',display)
finish({'valid_formats':3,'quarantined_formats':4,'sum_cent':30,'invalid_sibling_quarantines_order':True},5)
