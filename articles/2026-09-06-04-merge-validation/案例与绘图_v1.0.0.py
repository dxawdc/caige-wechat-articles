"""v1.0.0 | 2026-09-06 | 教学模拟案例：pandas合并后金额翻倍，问题出在哪里。"""
from pathlib import Path
import runpy
globals().update({k:v for k,v in runpy.run_path(str(Path(__file__).with_name("绘图工具_v1.0.0.py"))).items() if not k.startswith("__")})

orders=pd.DataFrame({'order_id':['O1','O2','O3'],'user_id':['U1','U1','U2'],'amount':[100,200,300]})
dimension=pd.DataFrame({'user_id':['U1','U1','U2','U2'],'channel':['搜索','搜索','推荐','推荐']})
bad=orders.merge(dimension,on='user_id',how='left')
blocked=False
try:orders.merge(dimension,on='user_id',how='left',validate='many_to_one')
except pd.errors.MergeError:blocked=True
# 本例重复行的全部属性一致，才可以删完全重复行。
dim=dimension.drop_duplicates()
good=orders.merge(dim,on='user_id',how='left',validate='many_to_one',indicator=True)
assert blocked and len(bad)==6 and bad.amount.sum()==1200
assert len(good)==len(orders)==3 and good.order_id.is_unique
assert good.amount.sum()==orders.amount.sum()==600 and good['_merge'].eq('both').all()
unknown=pd.DataFrame({'order_id':['O4'],'user_id':['U9'],'amount':[50]})
assert unknown.merge(dim,on='user_id',how='left',validate='many_to_one',indicator=True)['_merge'].eq('left_only').all()
for df,name in [(orders,'订单'),(dimension,'重复用户维表'),(bad,'错误合并'),(good,'正确合并')]:csv(df,name)
table('3 笔订单，为什么变成了 6 行','U1、U2 在右表各出现 2 次；一次匹配生成一行',pd.DataFrame([['O1','U1','100 × 2'],['O2','U1','200 × 2'],['O3','U2','300 × 2']],columns=['订单','关联用户','合并后的金额']),'01_匹配关系')
bar('没有新增订单，金额却翻倍','右表重复键扩大了左表记录；合并前后必须对账',['合并前','错误合并','修复后'],[600,1200,600],'02_金额核对','订单金额（元）',[BLUE,ORANGE,BLUE])
result({'passed':True,'before_rows':3,'bad_rows':6,'after_rows':3,'before_amount':600,'bad_amount':1200,'after_amount':600,'validation_blocks_duplicate_keys':blocked,'checks':6})
