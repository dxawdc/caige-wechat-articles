"""v1.0.0 | Apriori与关联规则：训练篮子发现，独立留出篮子复核。"""
from common_v1_0_0 import *
from sklearn.model_selection import train_test_split
from mlxtend.frequent_patterns import apriori,association_rules

def rule_metrics(frame,A,B):
    a=frame[list(A)].all(axis=1);b=frame[list(B)].all(axis=1)
    joint=int((a&b).sum());na=int(a.sum());nb=int(b.sum());n=len(frame)
    confidence=joint/na if na else 0
    return {'n':n,'a_count':na,'b_count':nb,'joint_count':joint,'support':joint/n,'confidence':confidence,'lift':confidence/(nb/n) if nb else 0}

def main():
    # ARTICLE_START
    df=pd.read_csv(DATA/'baskets_v1.0.0.csv')
    baskets=df.drop(columns='basket_id').astype(bool)
    train,test=train_test_split(baskets,test_size=.3,random_state=42)
    itemsets=apriori(train,min_support=.04,use_colnames=True,max_len=2)
    rules=association_rules(itemsets,metric='confidence',min_threshold=.4)
    rules=rules[rules.lift>=1.2].sort_values('lift',ascending=False)
    # 先冻结训练集发现的规则，再在留出篮子中计算同一组规则
    rows=[]
    for _,r in rules.iterrows():
        A,B=r.antecedents,r.consequents
        score=rule_metrics(test,A,B)
        rows.append({'rule':'+'.join(sorted(A))+' → '+'+'.join(sorted(B)),
                     'train_lift':float(r.lift),**score})
    comparison=pd.DataFrame(rows)
    print(comparison[['rule','joint_count','confidence','lift']])
    # ARTICLE_END
    assert set(train.index).isdisjoint(test.index)
    selected=rule_metrics(test,{'面包'},{'牛奶'})
    assert ((rules.antecedents==frozenset({'面包'}))&(rules.consequents==frozenset({'牛奶'}))).any()
    result('association',{'train_n':len(train),'test_n':len(test),'rules_found':len(rules),'bread_to_milk_test':selected,'top_rules':comparison.head(6).to_dict('records')})
    csv(comparison,'association_holdout');csv(df.loc[test.index].sort_index(),'basket_holdout')
    fig,ax=plt.subplots(figsize=(7,5.2));show=comparison.head(6).iloc[::-1];pos=np.arange(len(show));ax.barh(pos-.16,show.train_lift,height=.3,color=GRAY,label='发现集');ax.barh(pos+.16,show.lift,height=.3,color=GREEN,label='独立留出集');ax.set(yticks=pos,yticklabels=show.rule,xlabel='提升度 Lift',title='关联规则：训练中发现，留出数据复核');ax.axvline(1,color=ORANGE,ls='--',label='Lift=1参考线');ax.legend(fontsize=10);fig.tight_layout(rect=[0,.04,1,1]);savefig(fig,'09_association_lift')

if __name__=='__main__':main()
