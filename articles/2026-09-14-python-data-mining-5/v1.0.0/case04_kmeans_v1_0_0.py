"""v1.0.0 | RFM分群：log1p变换、标准化，轮廓系数辅助选K。"""
from common_v1_0_0 import *
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score,adjusted_rand_score

def main():
    # ARTICLE_START
    df=pd.read_csv(DATA/'rfm_v1.0.0.csv')
    features=['recency_days','frequency_90d','monetary_90d']
    scaler=StandardScaler()
    X=scaler.fit_transform(np.log1p(df[features]))
    scores={}
    for k in range(2,7):
        km=KMeans(n_clusters=k,n_init=20,random_state=42).fit(X)
        scores[k]=silhouette_score(X,km.labels_)
    best_k=max(scores,key=scores.get)
    model=KMeans(n_clusters=best_k,n_init=20,random_state=42).fit(X)
    df['cluster']=model.labels_
    profile=df.groupby('cluster')[features].median()
    profile['users']=df.groupby('cluster').size()
    print('候选范围内的最佳K：',best_k)
    print(profile)
    # ARTICLE_END
    assert profile.users.sum()==len(df) and df.user_id.is_unique
    stability=[adjusted_rand_score(model.labels_,KMeans(n_clusters=best_k,n_init=20,random_state=s).fit_predict(X)) for s in [7,13,29]]
    result('kmeans',{'best_k':best_k,'silhouette':float(scores[best_k]),'scores':{str(k):float(v) for k,v in scores.items()},'seed_stability_ARI':stability,'profile':profile.reset_index().to_dict('records')})
    csv(df,'cluster_assignments');csv(profile.reset_index(),'cluster_profile');csv(pd.DataFrame({'k':list(scores),'silhouette':list(scores.values())}),'cluster_k_search')
    fig,ax=plt.subplots(figsize=(7,4.5));ax.plot(list(scores),list(scores.values()),'o-',color=GREEN);ax.scatter([best_k],[scores[best_k]],s=110,facecolor='white',edgecolor=ORANGE,linewidth=2,zorder=3);ax.set(xticks=list(scores),xlabel='候选簇数K',ylabel='轮廓系数（越高通常越分离）',title='K-Means：先比较候选K，再解释人群');fig.tight_layout(rect=[0,.04,1,1]);savefig(fig,'07_cluster_k')
    fig,ax=plt.subplots(figsize=(7,5.8));colors=[GREEN,BLUE,ORANGE,'#886caa','#ba6485','#547875'];markers=['o','s','^','D','v','P']
    for c in sorted(df.cluster.unique()):
        part=df[df.cluster==c];ax.scatter(part.recency_days,part.monetary_90d,s=18,alpha=.5,color=colors[c],marker=markers[c],label=f'群{c}（{len(part)}人）')
    ax.set(xlabel='距最近一次购买（天）',ylabel='近90天累计消费（元）',title='用户分群：展示R与M的二维投影');ax.legend(fontsize=10);fig.tight_layout(rect=[0,.04,1,1]);savefig(fig,'08_cluster_projection')

if __name__=='__main__':main()
