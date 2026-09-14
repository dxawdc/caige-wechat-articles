"""v1.0.0 | 逻辑回归：验证集定阈值，测试集只报告冻结阈值的结果。"""
from common_v1_0_0 import *
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix,precision_score,recall_score,roc_auc_score,average_precision_score,precision_recall_curve

FEATURES=['days_since_visit','sessions_30d','tickets_30d','tenure_days']
def split():
    df=pd.read_csv(DATA/'churn_v1.0.0.csv')
    dev,test=train_test_split(df,test_size=.2,stratify=df.churn_next14d,random_state=42)
    train,val=train_test_split(dev,test_size=.25,stratify=dev.churn_next14d,random_state=43)
    assert set(train.user_id).isdisjoint(val.user_id) and set(dev.user_id).isdisjoint(test.user_id)
    return train,val,test

def main():
    # ARTICLE_START
    train,val,test=split()  # 60%训练、20%验证、20%测试
    model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000))
    model.fit(train[FEATURES],train.churn_next14d)
    val_p=model.predict_proba(val[FEATURES])[:,1]
    thresholds=np.arange(.05,.96,.01)
    costs=[]
    for t in thresholds:
        tn,fp,fn,tp=confusion_matrix(val.churn_next14d,val_p>=t).ravel()
        costs.append(fp+4*fn)  # 教学假设：漏报成本为误报的4倍
    threshold=float(thresholds[np.argmin(costs)])
    test_p=model.predict_proba(test[FEATURES])[:,1]
    test_pred=test_p>=threshold
    print('验证集选定阈值：',round(threshold,2))
    print('测试集混淆矩阵：',confusion_matrix(test.churn_next14d,test_pred))
    # ARTICLE_END
    cm=confusion_matrix(test.churn_next14d,test_pred);tn,fp,fn,tp=map(int,cm.ravel())
    metrics={'threshold':threshold,'test_n':len(test),'train_n':len(train),'validation_n':len(val),'test_prevalence':float(test.churn_next14d.mean()),'precision':precision_score(test.churn_next14d,test_pred),'recall':recall_score(test.churn_next14d,test_pred),'roc_auc':roc_auc_score(test.churn_next14d,test_p),'average_precision':average_precision_score(test.churn_next14d,test_p),'TN':tn,'FP':fp,'FN':fn,'TP':tp,'test_cost_units':fp+4*fn,'all_negative_cost_units':4*int(test.churn_next14d.sum()),'validation_min_cost_units':int(min(costs))}
    result('logistic',metrics);csv(test.assign(probability=test_p,prediction=test_pred.astype(int)),'logistic_test');csv(pd.DataFrame({'threshold':thresholds,'validation_cost':costs}),'threshold_search')
    fig,ax=plt.subplots(figsize=(7,4.8));ax.plot(thresholds,costs,color=GREEN);ax.axvline(threshold,color=ORANGE,ls='--',label=f'冻结阈值 {threshold:.2f}');ax.set(xlabel='判为流失的概率阈值',ylabel='误报数 + 4 × 漏报数（成本单位）',title='阈值只在验证集上选择');ax.legend();fig.tight_layout(rect=[0,.04,1,1]);savefig(fig,'03_logistic_threshold')
    fig,axes=plt.subplots(2,1,figsize=(7,9),gridspec_kw={'height_ratios':[1,1.1]});ax=axes[0]
    precision,recall,_=precision_recall_curve(test.churn_next14d,test_p);ax.plot(recall,precision,color=GREEN,label=f'AP={metrics["average_precision"]:.3f}');ax.axhline(metrics['test_prevalence'],color=GRAY,ls='--',label='正例比例参考线');ax.scatter([metrics['recall']],[metrics['precision']],color=ORANGE,zorder=4,label=f'阈值={threshold:.2f}');ax.set(xlim=(0,1),ylim=(0,1.05),xlabel='召回率',ylabel='精确率',title='逻辑回归：600名测试用户');ax.legend(fontsize=10)
    ax=axes[1];ax.imshow(cm,cmap='Blues');ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['预测不流失','预测流失'],yticklabels=['实际不流失','实际流失'],title='冻结阈值后的混淆矩阵')
    for (i,j),v in np.ndenumerate(cm):ax.text(j,i,str(v),ha='center',va='center',fontsize=19,color='white' if v>cm.max()/2 else INK)
    fig.tight_layout(rect=[0,.035,1,1],h_pad=2);savefig(fig,'04_logistic_evaluation')

if __name__=='__main__':main()
