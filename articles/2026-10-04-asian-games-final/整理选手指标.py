"""由官方选手奖牌清单与简介生成可离线重建的选手、年龄、性别和纪录指标。"""
from datetime import date
import json
import pandas as pd
from 官方接口 import ROOT, RAW
from 采集选手与纪录 import canonical_athletes
from 映射 import DISC_ZH, ORG_ZH

D=ROOT/'数据'
REFERENCE=date(2026,9,19)
AGE_LABELS=['15岁以下','15—19岁','20—24岁','25—29岁','30—34岁','35—39岁','40岁及以上','未提供']

def main():
    original=json.loads((RAW/'多奖牌运动员.json').read_text(encoding='utf-8'))
    people=canonical_athletes(original)
    profiles=json.loads((D/'获奖选手原始简介.json').read_text(encoding='utf-8'))
    bios={(r['noc'],str(r['reg'])):r for r in profiles}
    assert len(bios)==len(profiles)==len(people)
    roster=json.loads((RAW/'参赛名单.json').read_text(encoding='utf-8'))['participants']
    sexes={}
    for r in roster:
        if r['Type']!='A':continue
        key=(r['Org'],str(r['Reg']))
        if key in sexes:assert sexes[key]==r.get('Gender')
        sexes[key]=r.get('Gender')
    participants=[]; awards=[]
    for p in people:
        noc,reg=p['Org'],str(p['Reg']); bio=bios[(noc,reg)]['raw'] or {}
        birthday=pd.to_datetime(bio.get('BirthDateRaw'),errors='coerce')
        age=None
        if pd.notna(birthday):
            born=birthday.date()
            age=REFERENCE.year-born.year-((REFERENCE.month,REFERENCE.day)<(born.month,born.day))
            assert 5<=age<=100, (reg,age)
        gender=bio.get('Gender') or sexes.get((noc,reg))
        assert gender in ['M','W',None,''], (reg,gender)
        sex={'M':'男','W':'女'}.get(gender,'未提供')
        row=dict(noc=noc,reg=reg,name=p['Name'],noc_zh=ORG_ZH[noc],
                 birth_date=None if pd.isna(birthday) else birthday.date().isoformat(),
                 age=age,sex=sex,profile_url=bios[(noc,reg)]['source_url'])
        medals=p['Medals']
        assert len({(m['Disc'],m['Event'],m['Medal']) for m in medals})==len(medals)
        for kind,col in [('ME_GOLD','gold'),('ME_SILVER','silver'),('ME_BRONZE','bronze')]:
            row[col]=sum(m['Medal']==kind for m in medals)
            assert row[col]==p[kind]
        row['total']=len(medals)
        row['disciplines']='、'.join(DISC_ZH[c] for c in sorted({m['Disc'] for m in medals}))
        participants.append(row)
        for m in medals:
            awards.append(dict(noc=noc,reg=reg,name=p['Name'],discipline=m['Disc'],event_key=m['Event'],
                event_en=m['EventDesc'],medal=m['Medal'],age=age,sex=sex))
    ranking=pd.DataFrame(participants).sort_values(['gold','silver','bronze','noc','reg'],ascending=[False,False,False,True,True])
    previous=None; rank=0; ranks=[]
    for position,r in enumerate(ranking.itertuples(),1):
        counts=(r.gold,r.silver,r.bronze)
        if counts!=previous:rank=position
        ranks.append(rank); previous=counts
    ranking.insert(0,'rank',ranks)
    ranking.to_csv(D/'选手奖牌榜.csv',index=False,encoding='utf-8-sig')
    award=pd.DataFrame(awards)
    assert not award.duplicated(['noc','reg','discipline','event_key','medal']).any()
    official=pd.read_csv(D/'奖牌明细.csv',dtype={'reg':str})
    official['event_key']=official.event.str.rsplit('.',n=1).str[0]
    keys=['noc','discipline','event_key','medal']
    # 同一代表团在一个个人小项可能有两名铜牌选手，个人连接还需注册号。
    singles=official[official.type=='A'].set_index(keys+['reg'])
    teams=official[official.type!='A'].set_index(keys)
    assert singles.index.is_unique and teams.index.is_unique
    matched=[]
    for r in award.itertuples():
        key=(r.noc,r.discipline,r.event_key,r.medal)
        individual=key+(r.reg,)
        result=singles.loc[individual] if individual in singles.index else teams.loc[key]
        matched.append(dict(award_id=result.award_id,type=result.type,
            reg_official=r.reg if individual in singles.index else result.reg,date=result.date))
    joined=pd.concat([award.reset_index(drop=True),pd.DataFrame(matched)],axis=1)
    assert joined.award_id.notna().all()
    single=joined[joined.type=='A']
    assert single.reg.eq(single.reg_official).all()
    joined['age_group']=pd.cut(joined.age,[-1,14,19,24,29,34,39,100],labels=AGE_LABELS[:-1]).astype('object').fillna('未提供')
    joined.to_csv(D/'选手获奖明细.csv',index=False,encoding='utf-8-sig')
    for column,filename,labels in [('age_group','年龄分布.csv',AGE_LABELS),('sex','性别分布.csv',['女','男','未提供'])]:
        counts=joined.groupby(column).size().reindex(labels,fill_value=0)
        gold=joined[joined.medal=='ME_GOLD'].groupby(column).size().reindex(labels,fill_value=0)
        result=pd.DataFrame({'category':labels,'gold':gold.to_numpy(),'medals':counts.to_numpy()})
        result['gold_pct']=result.gold/result.gold.sum()*100
        result['medals_pct']=result.medals/result.medals.sum()*100
        result.to_csv(D/filename,index=False,encoding='utf-8-sig')
    records=[]
    raw=json.loads((D/'分项破纪录原始.json').read_text(encoding='utf-8'))
    for block in raw:
        disc=block['discipline']
        for group in block['raw']['records']:
            for r in group['Records']:
                assert isinstance(r['Equalled'],bool)
                records.append(dict(discipline=disc,sport_zh=DISC_ZH[disc],event_key=group['EvtKey'],
                    event_en=group['EvtDesc'],record_type=group['Type'],record_type_desc=group['TypeDesc'],
                    indicator=r['Indicator'],equalled=r['Equalled'],result=r['Result'],
                    name=r.get('Name'),noc=r.get('Org'),reg=str(r.get('Reg')),
                    date_raw=r['DateTimeRaw'],unit=r.get('Unit'),
                    source_url=f'https://back.results.asiangames2026.org/s/AG2026/en/{disc}/records/broken'))
    record=pd.DataFrame(records)
    # 纪录页中的空白占位没有成绩、选手或日期，不能计作本届破纪录。
    placeholders=record['result'].fillna('').astype(str).str.strip().eq('')
    record[placeholders].to_csv(D/'纪录空白条目.csv',index=False,encoding='utf-8-sig')
    record=record[~placeholders].copy()
    assert record['name'].fillna('').str.strip().ne('').all()
    assert record.date_raw.fillna('').str.strip().ne('').all()
    unique=['discipline','event_key','record_type','indicator','equalled','result','reg','date_raw','unit']
    assert not record.duplicated(unique).any()
    record.to_csv(D/'破纪录明细.csv',index=False,encoding='utf-8-sig')
    summary=record.groupby(['discipline','sport_zh']).agg(events=('event_key','nunique'),entries=('indicator','size'),equalled=('equalled','sum')).reset_index()
    summary['broken']=summary.entries-summary.equalled
    summary=summary.sort_values(['events','broken'],ascending=False)
    summary.to_csv(D/'破纪录分项统计.csv',index=False,encoding='utf-8-sig')
    indicators=dict(athletes=len(ranking),raw_rows=len(original),alias_rows=len(original)-len(ranking),
        medal_person_times=len(joined),gold_person_times=int(joined.medal.eq('ME_GOLD').sum()),
        age_reference=REFERENCE.isoformat(),athletes_age_available=int(ranking.age.notna().sum()),
        medal_age_available=int(joined.age.notna().sum()),gold_age_available=int(joined[joined.medal=='ME_GOLD'].age.notna().sum()),
        athlete_sex_missing=int(ranking.sex.eq('未提供').sum()),min_age=int(ranking.age.min()),max_age=int(ranking.age.max()),
        record_disciplines=len(summary),record_entries=len(record),record_broken=int((~record.equalled).sum()),
        record_equalled=int(record.equalled.sum()),record_events=int(summary.events.sum()),
        record_pages=len(raw),record_blank_placeholders=int(placeholders.sum()),
        all_person_awards_matched=True,individual_award_reg_matched=True)
    (D/'选手与纪录指标.json').write_text(json.dumps(indicators,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(indicators,ensure_ascii=False))

if __name__=='__main__':main()
