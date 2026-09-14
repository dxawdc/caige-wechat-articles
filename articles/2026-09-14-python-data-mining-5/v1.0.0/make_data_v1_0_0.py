"""v1.0.0 | 独立模拟四份数据，固定种子；不代表任何真实经营结果。"""
from common_v1_0_0 import np,pd,DATA,result

def main():
    rng=np.random.default_rng(20260914)
    n=1000
    orders=1+rng.poisson(3,n)  # 当前样本限定为前30天至少购买一次的用户
    spend=rng.gamma(3,160,n)
    active=rng.integers(1,31,n)
    revenue=80+.65*spend+32*orders+7*active+rng.normal(0,85,n)
    # 极端负金额截到0，与线性理想假设有轻微差异；生成式不交给模型。
    reg=pd.DataFrame({'user_id':np.arange(n),'spend_30d':spend.round(2),'orders_30d':orders,'active_days_30d':active,'spend_next30d':np.maximum(revenue,0).round(2)})
    reg.to_csv(DATA/'spend_v1.0.0.csv',index=False,encoding='utf-8-sig')

    n=3000
    recency=rng.integers(0,30,n)
    sessions=1+rng.poisson(7,n)  # 近30天至少访问一次的在险用户
    tickets=rng.poisson(.6,n)
    tenure=rng.integers(15,730,n)
    recency=np.minimum(recency,tenure-1)
    logit=-2.8+.15*recency-.12*sessions+.65*tickets-.001*tenure+1.2*((recency>18)&(sessions<6))
    probability=1/(1+np.exp(-logit))
    churn=rng.binomial(1,probability)
    df=pd.DataFrame({'user_id':np.arange(n),'days_since_visit':recency,'sessions_30d':sessions,'tickets_30d':tickets,'tenure_days':tenure,'churn_next14d':churn})
    df.to_csv(DATA/'churn_v1.0.0.csv',index=False,encoding='utf-8-sig')

    # 在log(1+R/F/M)空间生成四类行为，仅用于构建可解释的教学样本。
    centers=np.array([[1.7,2.8,7.3],[3.9,.7,4.6],[1.7,1.3,5.4],[3.3,2.8,7.1]])
    latent=np.repeat(np.arange(4),250);rng.shuffle(latent)
    logrfm=centers[latent]+rng.normal(0,[.25,.22,.3],(1000,3))
    values=np.expm1(logrfm)
    rfm=pd.DataFrame({'user_id':np.arange(1000),'recency_days':np.clip(np.rint(values[:,0]),0,89).astype(int),'frequency_90d':np.maximum(1,np.rint(values[:,1])).astype(int),'monetary_90d':values[:,2].round(2)})
    rfm.to_csv(DATA/'rfm_v1.0.0.csv',index=False,encoding='utf-8-sig')

    n=2400
    bread=rng.random(n)<.36;coffee=rng.random(n)<.25
    milk=rng.random(n)<np.clip(.16+.46*bread+.2*coffee,0,1)
    butter=rng.random(n)<(.07+.34*bread)
    diapers=rng.random(n)<.13
    beer=rng.random(n)<(.18+.24*diapers)
    eggs=rng.random(n)<.3;tissue=rng.random(n)<.65
    baskets=pd.DataFrame({'面包':bread,'咖啡':coffee,'牛奶':milk,'黄油':butter,'纸尿裤':diapers,'啤酒':beer,'鸡蛋':eggs,'纸巾':tissue})
    baskets.insert(0,'basket_id',np.arange(n))
    # 保留全集交易口径；全0行是只购买了范围外商品的订单，不丢弃。
    baskets.to_csv(DATA/'baskets_v1.0.0.csv',index=False,encoding='utf-8-sig')
    result('data_summary',{'seed':20260914,'spend_rows':len(reg),'churn_rows':len(df),'churn_rate':float(churn.mean()),'rfm_rows':len(rfm),'basket_rows':len(baskets),'all_zero_scope_baskets':int((~baskets.drop(columns='basket_id').any(axis=1)).sum())})

if __name__=='__main__':main()
