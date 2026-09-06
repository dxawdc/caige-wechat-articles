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
orders=pd.DataFrame({'order_id':['O1','O2','O3'],
 'user_id':['U1','U1','U2'],'amount':[100,200,300]})
dimension=pd.DataFrame({'user_id':['U1','U1','U2','U2'],
 'channel':['A','A','B','B']})
left_n=orders.groupby('user_id').size().rename('left_rows')
right_n=dimension.groupby('user_id').size().rename('right_rows')
diagnosis=left_n.to_frame().join(right_n).fillna(0)
diagnosis['predicted_left_join_rows']=(
    diagnosis.left_rows*diagnosis.right_rows.clip(lower=1)
)
assert diagnosis.predicted_left_join_rows.sum()==6
# END MAIN
# BEGIN HISTORY
history=pd.DataFrame({'user_id':['U1','U1'],
    'valid_from':pd.to_datetime(['2026-08-01','2026-08-05']),
    'channel':['A','B']})
dated_orders=pd.DataFrame({'order_id':['P1','P2'],'user_id':['U1','U1'],
    'paid_at':pd.to_datetime(['2026-08-03','2026-08-06']),
    'amount':[100,200]})
assert not history.duplicated(['user_id','valid_from']).any()
asof=pd.merge_asof(
    dated_orders.sort_values('paid_at'),history.sort_values('valid_from'),
    left_on='paid_at',right_on='valid_from',by='user_id',direction='backward',
)
assert asof.channel.tolist()==['A','B']
assert len(asof)==2 and asof.amount.sum()==300
# END HISTORY
bad=orders.merge(dimension,on='user_id',how='left')
assert len(bad)==6 and bad.amount.sum()==1200
fixed=orders.merge(dimension.drop_duplicates(),on='user_id',how='left',validate='many_to_one')
assert len(fixed)==3 and fixed.amount.sum()==600
conflict=dimension.copy();conflict.loc[1,'channel']='C'
try:
    orders.merge(conflict.drop_duplicates(),on='user_id',validate='many_to_one')
    raise AssertionError('冲突渠道不应通过多对一')
except pd.errors.MergeError:pass
missing=dated_orders.copy();missing['paid_at']=pd.to_datetime(['2026-07-30','2026-08-06'])
unmatched=pd.merge_asof(missing.sort_values('paid_at'),history.sort_values('valid_from'),left_on='paid_at',right_on='valid_from',by='user_id',direction='backward')
assert pd.isna(unmatched.iloc[0].channel)
diagnosis.to_csv(ROOT/'数据/扩行诊断_v1.1.0.csv',encoding='utf-8-sig')
asof.to_csv(ROOT/'数据/历史渠道匹配_v1.1.0.csv',index=False,encoding='utf-8-sig')
explain('补渠道，要用哪个时间的渠道','独立时间维表示例：U1 在 08-05 从 A 变为 B',pd.DataFrame([
 ['P1','08-03','A','B'],['P2','08-06','B','B'],
],columns=['订单','支付日期','按历史生效日','若只取最新渠道']))
finish({'predicted_rows':6,'bad_amount':1200,'fixed_amount':600,'historical_channels':['A','B']},6)
