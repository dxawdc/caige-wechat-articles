"""采集收官奖牌榜和46个代表团明细，逐一校验后导出整洁CSV。"""
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from datetime import datetime, timezone
import json
import pandas as pd
from 官方接口 import ROOT, RAW, get

def collect_org(org):
    code=org['Key']
    rows=get('/ALL/medals/org/'+code,'奖牌明细_'+code)
    print(code,len(rows),flush=True)
    return rows

def main():
    orgs=get('/ALL/orgs/list','代表团')
    standings=get('/ALL/medals/standings','奖牌榜')
    disciplines=get('/ALL/disc/list','项目')
    with ThreadPoolExecutor(max_workers=3) as pool:
        details=[r for rows in pool.map(collect_org,orgs) for r in rows]
    end=get('/ALL/medals/standings','奖牌榜_采集结束')
    if standings!=end:raise ValueError('采集过程中奖牌榜发生变化，请重新采集')
    count=Counter((r['Org'],r['Medal']) for r in details)
    mismatches=[]
    for s in standings:
        for medal in ['ME_GOLD','ME_SILVER','ME_BRONZE']:
            if s['Count'][medal]['total']!=count[s['Org'],medal]:
                mismatches.append([s['Org'],medal,s['Count'][medal]['total'],count[s['Org'],medal]])
    if mismatches:raise ValueError('奖牌明细与榜单不一致：'+str(mismatches))
    all_orgs={o['Key']:o['Desc'] for o in orgs}
    ranked={s['Org']:s for s in standings}
    table=[]
    for code,name in all_orgs.items():
        s=ranked.get(code,{})
        c=s.get('Count',{})
        table.append({'noc':code,'name_en':name,'official_rank':s.get('Rk',''),
          'gold':c.get('ME_GOLD',{}).get('total',0),'silver':c.get('ME_SILVER',{}).get('total',0),
          'bronze':c.get('ME_BRONZE',{}).get('total',0),'total':c.get('total',{}).get('total',0)})
    pd.DataFrame(table).sort_values(['gold','silver','bronze'],ascending=False).to_csv(ROOT/'数据/国家地区奖牌榜.csv',index=False,encoding='utf-8-sig')
    flat=[]; candidates=[]
    for r in details:
        award_id='|'.join(str(r.get(k,'')) for k in ['Org','Disc','Event','Medal','Reg'])
        flat.append({'award_id':award_id,'noc':r['Org'],'medal':r['Medal'],'discipline':r['Disc'],
            'sport_en':r['DiscDesc'],'event':r['Event'],'event_en':r['EventDesc'],
            'type':r['Type'],'name_en':r['Name'],'reg':r.get('Reg',''),'date':r.get('DateRaw','')[:10],
            'gender':r.get('Gender',''),'members':json.dumps(r.get('Members',[]),ensure_ascii=False)})
        members=r.get('Members') if r['Type']=='T' else [r]
        for m in members or []:
            candidates.append({'award_id':award_id,'noc':r['Org'],'medal':r['Medal'],
                'discipline':r['Disc'],'event_en':r['EventDesc'],'reg':m.get('Reg',''),
                'name_en':m.get('Name',''),'birthdate':m.get('BirthDate',''),
                'membership_status':'requires_event_verification' if r['Type']=='T' else 'individual_award'})
    df=pd.DataFrame(flat)
    if df.award_id.duplicated().any():raise ValueError('存在重复奖牌唯一键')
    df.to_csv(ROOT/'数据/奖牌明细.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(candidates).drop_duplicates(['award_id','reg']).to_csv(ROOT/'数据/官方成员候选.csv',index=False,encoding='utf-8-sig')
    report={'fetched_at':datetime.now(timezone.utc).isoformat(),'orgs':len(orgs),
       'medal_orgs':len(standings),'medals':len(details),'gold':sum(v for (o,m),v in count.items() if m=='ME_GOLD'),
       'medal_counts':dict(Counter(r['Medal'] for r in details)),
       'latest_award_date':max(r.get('DateRaw','')[:10] for r in details),
       'standings_unchanged_during_collection':True,'mismatches':mismatches,'status':'passed'}
    (ROOT/'数据/成绩验收.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
