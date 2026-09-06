"""v1.0.0 | 2026-09-06 | 教学模拟案例：游戏LTV怎么算：先把分母和观察天数对齐。"""
from pathlib import Path
import runpy
globals().update({k:v for k,v in runpy.run_path(str(Path(__file__).with_name("绘图工具_v1.0.0.py"))).items() if not k.startswith("__")})

from datetime import date,timedelta
users=pd.DataFrame([(f'A{i:03}','A','2026-08-01') for i in range(100)]+[(f'B{i:03}','B','2026-08-07') for i in range(100)],columns=['user_id','cohort','signup_date'])
daily_a=[200,100,100,80,70,60,90,150,40,35,30,25,20,20]
daily_b=[300,150,120,100,90,80,70,65]
records=[]
for cohort,values,signup in [('A',daily_a,'2026-08-01'),('B',daily_b,'2026-08-07')]:
    for age,value in enumerate(values):
        for payer in range(20):records.append((f'{cohort}{payer:03}',(date.fromisoformat(signup)+timedelta(days=age)).isoformat(),int(round(value*100/20))))
payments=pd.DataFrame(records,columns=['user_id','pay_date','amount_cent'])
detail=payments.merge(users,on='user_id',how='left',validate='many_to_one')
detail['age']=(pd.to_datetime(detail.pay_date)-pd.to_datetime(detail.signup_date)).dt.days
rows=[];cutoff=pd.Timestamp('2026-08-14')
for cohort,group in users.groupby('cohort'):
    signup=pd.Timestamp(group.signup_date.iloc[0]);n=len(group)
    for day_n in [1,7,14]:
        mature=signup+pd.Timedelta(days=day_n-1)<=cutoff
        earned=detail.loc[detail.cohort.eq(cohort)&detail.age.between(0,day_n-1),'amount_cent'].sum()/100
        rows.append((cohort,day_n,n,earned if mature else None,earned/n if mature else None))
out=pd.DataFrame(rows,columns=['cohort','day_n','new_users','revenue','ltv'])
for df,name in [(users,'注册用户'),(payments,'支付订单'),(out,'LTV结果')]:csv(df,name)
a=out[out.cohort.eq('A')].set_index('day_n');b=out[out.cohort.eq('B')].set_index('day_n')
assert a.loc[1,'ltv']==2 and a.loc[7,'ltv']==7 and a.loc[14,'ltv']==10.2
assert b.loc[7,'ltv']==9.1 and pd.isna(b.loc[14,'ltv'])
assert sum(daily_a)==1020 and detail.user_id.nunique()==40
fig,ax=figure('在相同日龄上比较累计价值','截至 2026-08-14；每批新增 100 人；未观测日龄不连线')
ax.plot(range(1,15),np.cumsum(daily_a)/100,marker='o',markersize=4,color=BLUE,label='A 批次：08-01 新增')
ax.plot(range(1,9),np.cumsum(daily_b)/100,marker='s',markersize=4,color=ORANGE,linestyle='--',label='B 批次：08-07 新增')
ax.set_xlabel('累计天数（第1天=注册当天）');ax.set_ylabel('累计LTV（元/新增用户）');ax.set_ylim(0,12);ax.grid(alpha=.15);ax.legend(fontsize=10,loc='upper left');save(fig,'01_日龄对齐')
table('7 日 LTV 可以比，14 日还不能比','分母固定为该批 100 名新增用户；不是付费用户数',pd.DataFrame([['A / 08-01','2.00','7.00','10.20'],['B / 08-07','3.00','9.10','未到期']],columns=['新增批次','1日LTV','7日LTV','14日LTV']),'02_LTV对照')
result({'passed':True,'A_7d_revenue':700,'A_7d_ltv':7,'A_14d_ltv':10.2,'A_payers':20,'A_7d_arppu':35,'B_7d_ltv':9.1,'B_14d_ltv':None,'checks':7})
