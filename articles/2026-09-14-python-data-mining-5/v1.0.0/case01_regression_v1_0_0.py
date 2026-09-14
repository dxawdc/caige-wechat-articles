"""v1.0.0 | 多元线性回归：预测下一30天消费金额，测试集只做最终评价。"""
from common_v1_0_0 import *
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error,root_mean_squared_error,r2_score

def main():
    # ARTICLE_START
    df=pd.read_csv(DATA/'spend_v1.0.0.csv')
    features=['spend_30d','orders_30d','active_days_30d']
    train,test=train_test_split(df,test_size=.25,random_state=42)
    model=LinearRegression().fit(train[features],train['spend_next30d'])
    pred=model.predict(test[features])
    baseline=DummyRegressor(strategy='mean').fit(train[features],train['spend_next30d'])
    base_pred=baseline.predict(test[features])
    metrics={
        'MAE':mean_absolute_error(test['spend_next30d'],pred),
        'RMSE':root_mean_squared_error(test['spend_next30d'],pred),
        'R2':r2_score(test['spend_next30d'],pred),
        'baseline_MAE':mean_absolute_error(test['spend_next30d'],base_pred)
    }
    print(metrics)
    # ARTICLE_END
    assert set(train.user_id).isdisjoint(test.user_id)
    csv(test.assign(prediction=pred,residual=test.spend_next30d-pred),'regression_test')
    csv(pd.DataFrame({'feature':features,'coefficient':model.coef_}),'regression_coefficients')
    metrics.update(train_n=len(train),test_n=len(test),intercept=float(model.intercept_),coefficients=dict(zip(features,map(float,model.coef_))))
    result('regression',metrics)
    fig,ax=plt.subplots(figsize=(7,5.5));ax.scatter(test.spend_next30d,pred,s=20,alpha=.6,color=GREEN)
    lim=[min(test.spend_next30d.min(),pred.min())-30,max(test.spend_next30d.max(),pred.max())+30]
    ax.plot(lim,lim,'--',color=GRAY,label='理想预测：预测值=真实值');ax.set(xlim=lim,ylim=lim,xlabel='真实的未来30天消费（元）',ylabel='模型预测消费（元）',title='线性回归：250名测试用户的预测')
    ax.legend(fontsize=10);fig.tight_layout(rect=[0,.04,1,1]);savefig(fig,'01_regression_prediction')
    fig,ax=plt.subplots(figsize=(7,4.8));ax.scatter(pred,test.spend_next30d-pred,s=20,alpha=.6,color=BLUE);ax.axhline(0,color=GRAY,ls='--')
    ax.set(xlabel='预测消费（元）',ylabel='残差：真实值−预测值（元）',title='残差检查：是否还有系统性偏差？');fig.tight_layout(rect=[0,.04,1,1]);savefig(fig,'02_regression_residual')

if __name__=='__main__':main()
