"""v1.0.0 | 决策树：交叉验证控制深度，最终测试集与逻辑回归保持相同。"""
from common_v1_0_0 import *
from case02_logistic_v1_0_0 import split,FEATURES
from sklearn.tree import DecisionTreeClassifier,plot_tree,export_text
from sklearn.model_selection import GridSearchCV,StratifiedKFold
from sklearn.metrics import roc_auc_score,average_precision_score,precision_score,recall_score

def main():
    # ARTICLE_START
    train,val,test=split()
    dev=pd.concat([train,val])  # 合并为开发集，在内部进行5折交叉验证
    cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
    search=GridSearchCV(
        DecisionTreeClassifier(min_samples_leaf=30,random_state=42),
        {'max_depth':[1,2,3,4,5,8,None]},
        scoring='roc_auc',cv=cv,return_train_score=True,n_jobs=1
    )
    search.fit(dev[FEATURES],dev.churn_next14d)
    model=search.best_estimator_  # 默认已在全部开发集上重新拟合
    probability=model.predict_proba(test[FEATURES])[:,1]
    print('最佳深度：',search.best_params_)
    print('测试集ROC-AUC：',roc_auc_score(test.churn_next14d,probability))
    # ARTICLE_END
    assert set(dev.user_id).isdisjoint(test.user_id)
    results=pd.DataFrame(search.cv_results_);csv(results[['param_max_depth','mean_train_score','mean_test_score','std_test_score']],'tree_cv')
    csv(test.assign(probability=probability,prediction=(probability>=.5).astype(int)),'tree_test')
    metrics={'chosen_max_depth':search.best_params_['max_depth'],'actual_depth':model.get_depth(),'leaves':model.get_n_leaves(),'cv_auc':float(search.best_score_),'test_auc':roc_auc_score(test.churn_next14d,probability),'test_ap':average_precision_score(test.churn_next14d,probability),'test_precision_at_05':precision_score(test.churn_next14d,probability>=.5,zero_division=0),'test_recall_at_05':recall_score(test.churn_next14d,probability>=.5),'development_n':len(dev),'test_n':len(test)}
    result('tree',metrics)
    (OUT/'tree_rules_v1.0.0.txt').write_text(export_text(model,feature_names=FEATURES,max_depth=30),encoding='utf8')
    fig,ax=plt.subplots(figsize=(7,4.8));x=np.arange(len(results));ax.plot(x,results.mean_train_score,'o-',color=GRAY,label='训练折AUC');ax.errorbar(x,results.mean_test_score,yerr=results.std_test_score,fmt='s-',color=GREEN,capsize=4,label='验证折均值 ± 1个标准差');ax.set(xticks=x,xticklabels=['1','2','3','4','5','8','不限'],xlabel='最大树深度（叶节点至少30人）',ylabel='ROC-AUC',title='树越复杂，验证成绩不一定更好');ax.legend(fontsize=10);fig.tight_layout(rect=[0,.04,1,1]);savefig(fig,'05_tree_complexity')
    fig,ax=plt.subplots(figsize=(11,6.5));plot_tree(model,max_depth=2,feature_names=['距上次访问天数','近30天访问次数','近30天工单数','注册天数'],class_names=['不流失','流失'],filled=True,rounded=True,fontsize=10,ax=ax,impurity=False)
    ax.set_title('决策树规则：展示前两层分裂，更深节点以省略号表示',fontsize=17);fig.tight_layout(rect=[0,.06,1,.95]);fig.savefig(OUT/'tree_overview_v1.0.0.svg',bbox_inches='tight');plt.close(fig)
    # 手机正文用一条真实高风险路径，避免整棵宽树缩小后文字不可读。
    tr=model.tree_;paths=[]
    def walk(node,steps):
        if tr.children_left[node]==tr.children_right[node]:
            value=tr.value[node][0];paths.append((float(value[1]/value.sum()),node,steps));return
        walk(tr.children_left[node],steps+[(node,'≤')]);walk(tr.children_right[node],steps+[(node,'>')])
    walk(0,[]);risk,leaf,steps=max(paths,key=lambda row:row[0]);names=['距上次访问天数','近30天访问次数','近30天工单数','注册天数']
    fig,ax=plt.subplots(figsize=(7,8));ax.axis('off');ax.set_title('决策树：沿一条实际高风险路径往下读',pad=20)
    levels=len(steps)+1;ys=np.linspace(.86,.15,levels)
    for idx,(node,relation) in enumerate(steps):
        label=f'{names[tr.feature[node]]} {relation} {tr.threshold[node]:.1f}\n判断前覆盖 {tr.n_node_samples[node]} 名开发集用户'
        ax.text(.5,ys[idx],label,transform=ax.transAxes,ha='center',va='center',fontsize=15,bbox={'boxstyle':'round,pad=.7','facecolor':'#edf6f1','edgecolor':GREEN})
        ax.annotate('',xy=(.5,ys[idx+1]+.07),xytext=(.5,ys[idx]-.06),xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':GRAY,'lw':1.5})
    ax.text(.5,ys[-1],f'落入此叶节点：{tr.n_node_samples[leaf]} 人\n其中流失类别占比 {risk:.1%}\n这是节点样本比例，不是挽回成功率',transform=ax.transAxes,ha='center',va='center',fontsize=15,bbox={'boxstyle':'round,pad=.7','facecolor':'#f9f0e3','edgecolor':ORANGE})
    fig.tight_layout(rect=[0,.04,1,1]);savefig(fig,'06_tree_rules')

if __name__=='__main__':main()
