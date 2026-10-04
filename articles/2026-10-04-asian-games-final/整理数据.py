"""离线整理已采集的官方快照；保留 NOC 排名与零奖牌代表团。"""
from pathlib import Path
import json
import pandas as pd
from 映射 import ORG_ZH, DISC_ZH

ROOT=Path(__file__).resolve().parent
D=ROOT/'数据'

def main():
    table=pd.read_csv(D/'国家地区奖牌榜.csv')
    table['name_zh']=table.noc.map(ORG_ZH)
    assert table.name_zh.notna().all()
    assert (table[['gold','silver','bronze']].sum(axis=1)==table.total).all()
    table.to_csv(D/'国家地区奖牌榜.csv',index=False,encoding='utf-8-sig')
    medals=pd.read_csv(D/'奖牌明细.csv')
    if 'date_raw' not in medals:medals['date_raw']=medals['date']
    medals['date']=medals['date_raw']
    medals['date_source']='official_medal_record'
    fixes=pd.read_csv(D/'金牌日期补核.csv').set_index('award_id')
    for award_id,row in fixes.iterrows():
        mask=medals.award_id.eq(award_id) & medals.date_raw.isna()
        assert mask.sum()==1
        medals.loc[mask,'date']=row['date']
        medals.loc[mask,'date_source']=row.source_url
    medals['sport_zh']=medals.discipline.map(DISC_ZH)
    assert medals.sport_zh.notna().all()
    medals.to_csv(D/'奖牌明细.csv',index=False,encoding='utf-8-sig')
    candidates=[]
    for file in (D/'官方原始').glob('奖牌明细_*.json'):
        if file.name.endswith('.来源.json'):continue
        for r in json.loads(file.read_text(encoding='utf-8')):
            award_id='|'.join(str(r.get(k,'')) for k in ['Org','Disc','Event','Medal','Reg'])
            for m in (r.get('Members',[]) if r['Type']=='T' else [r]):
                candidates.append(dict(award_id=award_id,noc=r['Org'],medal=r['Medal'],
                    discipline=r['Disc'],event_en=r['EventDesc'],reg=m.get('Reg',''),
                    name_en=m.get('Name',''),membership_status=
                    'requires_event_verification' if r['Type']=='T' else 'individual_award'))
    pd.DataFrame(candidates).drop_duplicates(['award_id','reg']).to_csv(D/'官方成员候选.csv',index=False,encoding='utf-8-sig')
    china=medals[(medals.noc=='CHN') & (medals.medal=='ME_GOLD')]
    china.groupby(['discipline','sport_zh']).size().rename('gold').sort_values(ascending=False).reset_index().to_csv(D/'中国分项目金牌.csv',index=False,encoding='utf-8-sig')
    gold=medals[medals.medal=='ME_GOLD']
    assert gold.date.notna().all(), '先补核缺失比赛日期，再绘制累计图'
    gold.groupby(['date','noc']).size().rename('gold').reset_index().to_csv(D/'每日金牌.csv',index=False,encoding='utf-8-sig')
    event_counts=gold.groupby(['discipline','event']).size()
    report={'orgs':len(table),'medal_orgs':int((table.total>0).sum()),
        'medals':len(medals),'gold':len(gold),'gold_event_keys':len(event_counts),
        'extra_gold_by_shared_event_keys':int((event_counts-1).sum()),
        'team_members':'候选名单；不用于运动员或省级奖牌汇总',
        'china_gold':len(china),'china_sports_with_gold':china.discipline.nunique(),
        'all_medal_counts_match':True,'gold_dates_complete_after_verification':True,
        'gold_date_corrections':len(fixes)}
    assert not medals.award_id.duplicated().any()
    for medal,col in [('ME_GOLD','gold'),('ME_SILVER','silver'),('ME_BRONZE','bronze')]:
        observed=medals[medals.medal==medal].groupby('noc').size().reindex(table.noc,fill_value=0).to_numpy()
        assert (observed==table[col].to_numpy()).all()
    (D/'离线验收.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
