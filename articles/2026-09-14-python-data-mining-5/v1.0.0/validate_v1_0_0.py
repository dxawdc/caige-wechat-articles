"""v1.0.0 | 从导出的预测与交易重新计算关键指标，检查内容口径。"""
from common_v1_0_0 import *
from sklearn.metrics import mean_absolute_error,roc_auc_score,confusion_matrix

def main():
    checks={}
    load=lambda name:json.loads((OUT/(name+'_v1.0.0.json')).read_text(encoding='utf8'))
    reg=pd.read_csv(OUT/'regression_test_v1.0.0.csv');r=load('regression')
    checks['regression_mae_recomputed']=bool(np.isclose(mean_absolute_error(reg.spend_next30d,reg.prediction),r['MAE']))
    checks['regression_beats_mean_baseline']=r['MAE']<r['baseline_MAE']
    log=pd.read_csv(OUT/'logistic_test_v1.0.0.csv');m=load('logistic')
    counts=confusion_matrix(log.churn_next14d,log.prediction).ravel()
    checks['confusion_matrix_recomputed']=list(map(int,counts))==[m[x] for x in ['TN','FP','FN','TP']]
    checks['logistic_auc_recomputed']=bool(np.isclose(roc_auc_score(log.churn_next14d,log.probability),m['roc_auc']))
    checks['frozen_threshold_predictions']=bool(((log.probability>=m['threshold']).astype(int)==log.prediction).all())
    tree=pd.read_csv(OUT/'tree_test_v1.0.0.csv')
    checks['same_heldout_users_for_classifiers']=set(tree.user_id)==set(log.user_id)
    k=pd.read_csv(OUT/'cluster_assignments_v1.0.0.csv');profiles=pd.read_csv(OUT/'cluster_profile_v1.0.0.csv')
    checks['clustering_all_users_once']=len(k)==1000 and k.user_id.is_unique and int(profiles.users.sum())==1000
    baskets=pd.read_csv(OUT/'basket_holdout_v1.0.0.csv');a=baskets['面包'].astype(bool);b=baskets['牛奶'].astype(bool);joint=(a&b).sum();ar=load('association')['bread_to_milk_test']
    checks['association_denominators']=bool(ar['n']==len(baskets) and ar['a_count']==a.sum() and ar['b_count']==b.sum() and ar['joint_count']==joint)
    checks['association_metrics_recomputed']=bool(np.isclose(ar['support'],joint/len(baskets)) and np.isclose(ar['confidence'],joint/a.sum()) and np.isclose(ar['lift'],(joint/a.sum())/b.mean()))
    for file,key in [('spend','user_id'),('churn','user_id'),('rfm','user_id'),('baskets','basket_id')]:
        df=pd.read_csv(DATA/(file+'_v1.0.0.csv'));checks[file+'_complete_unique']=bool(df[key].is_unique and not df.isna().any().any())
    checks['nine_analysis_figures']=len(list(OUT.glob('0[1-9]_*_v1.0.0.png')))==9
    result('validation',{'checks':checks,'all_passed':all(checks.values()),'scope':'数据与指标自检；图片另做人工视觉检查'})
    assert all(checks.values()),checks
    print('PASS',len(checks),'data/model checks')

if __name__=='__main__':main()
