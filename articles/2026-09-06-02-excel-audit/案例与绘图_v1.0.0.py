"""v1.0.0 | 2026-09-06 | 教学模拟案例：用Python合并Excel，顺手把数据问题查出来。"""
from pathlib import Path
import runpy
globals().update({k:v for k,v in runpy.run_path(str(Path(__file__).with_name("绘图工具_v1.0.0.py"))).items() if not k.startswith("__")})

import re
inbox=ROOT/'输入表';inbox.mkdir(exist_ok=True)
pd.DataFrame([['O01',100],['O02',200],['O03',300]],columns=['order_id','amount']).to_excel(inbox/'订单_2026-08-01.xlsx',index=False)
pd.DataFrame([['O03',300],['O04',400],['O05','待补']],columns=['order_id','amount']).to_excel(inbox/'订单_2026-08-02.xlsx',index=False)
pd.DataFrame([['O04',450],['O06',600]],columns=['order_id','amount']).to_excel(inbox/'订单_2026-08-03.xlsx',index=False)
pd.DataFrame([['O07',700]],columns=['order_id','amt']).to_excel(inbox/'订单_2026-08-04.xlsx',index=False)
parts=[];rejected_files=[]
for path in sorted(inbox.glob('订单_*.xlsx')):
    if path.name.startswith('~$'):continue
    df=pd.read_excel(path,dtype={'order_id':'string'},engine='openpyxl')
    stamp=re.fullmatch(r'订单_(\d{4}-\d{2}-\d{2})\.xlsx',path.name)
    if stamp is None or set(df.columns)!={'order_id','amount'}:
        rejected_files.append(path.name);continue
    # report_day 是文件日期，不冒充订单发生日期。
    df['report_day']=pd.to_datetime(stamp.group(1),format='%Y-%m-%d',errors='raise')
    df['source_file']=path.name;parts.append(df)
raw=pd.concat(parts,ignore_index=True)
raw['amount']=pd.to_numeric(raw['amount'],errors='coerce')
invalid=raw[raw.amount.isna() | raw.order_id.isna()].copy()
valid=raw.drop(index=invalid.index)
# 相同订单 + 相同金额视为重复报送；冲突订单的全部记录先隔离。
unique=valid.drop_duplicates(['order_id','amount'],keep='first')
conflicts=unique[unique.duplicated('order_id',keep=False)]
clean=unique[~unique.order_id.isin(conflicts.order_id)]
for frame,name in [(raw,'合并原始'),(invalid,'无效行'),(conflicts,'冲突订单'),(clean,'可用订单')]:csv(frame,name)
assert len(raw)==8 and len(invalid)==1 and len(valid)-len(unique)==1
assert len(conflicts)==2 and clean.order_id.is_unique and clean.amount.sum()==1200
assert len(raw)==len(invalid)+(len(valid)-len(unique))+len(conflicts)+len(clean)
assert len(rejected_files)==1
table('这些订单，需要分开处理','3 份通过表头检查的文件，共 8 行；金额单位：元',pd.DataFrame([['O03','300 / 300','重复报送'],['O04','400 / 450','金额冲突'],['O05','待补','无效金额'],['O01/O02/O06','100/200/600','正常保留']],columns=['订单','原始金额','处理判断']),'01_问题定位')
bar('每一行，都有明确去向','8 = 1 无效 + 1 重复 + 2 冲突 + 4 可用；另拒收 1 个文件',['无效行','重复报送','冲突待核','可用记录'],[1,1,2,4],'02_行数对账','记录数（行）')
result({'passed':True,'accepted_files':3,'rejected_files':rejected_files,'input_rows':8,'invalid_rows':1,'duplicate_rows':1,'conflict_rows':2,'clean_rows':4,'clean_amount':1200,'checks':7})
