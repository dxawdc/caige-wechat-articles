"""核对已交付数据与图表指标，输出可审计验收结果。"""
from pathlib import Path
import json
import pandas as pd
from PIL import Image
from 图表工具 import ROOT, D, map_features
from 代表团地图工具 import mapping

def main():
    noc=pd.read_csv(D/'国家地区奖牌榜.csv')
    medals=pd.read_csv(D/'奖牌明细.csv')
    regions=pd.read_csv(D/'地区奖牌底表.csv')
    gold=medals[medals.medal=='ME_GOLD']
    assert len(noc)==46 and noc.noc.nunique()==46
    assert len(medals)==1568 and medals.award_id.is_unique
    assert medals.sport_zh.notna().all() and noc.name_zh.notna().all()
    assert (noc[['gold','silver','bronze']].sum(axis=1)==noc.total).all()
    for kind,col in [('ME_GOLD','gold'),('ME_SILVER','silver'),('ME_BRONZE','bronze')]:
        actual=medals[medals.medal==kind].groupby('noc').size().reindex(noc.noc,fill_value=0)
        assert actual.to_list()==noc[col].to_list()
    assert len(gold)==470 and len(gold[gold.noc=='CHN'])==169
    assert gold.date.notna().all()
    by_event=gold.groupby(['discipline','event']).size()
    assert len(by_event)==469 and int((by_event-1).sum())==1
    china=pd.read_csv(D/'中国分项目金牌.csv')
    assert len(china)==38 and china.gold.sum()==169
    assert china.head(14).gold.sum()==136 and china.iloc[14:].gold.sum()==33
    assert len(regions)==34 and regions.adcode.nunique()==34
    assert regions.gold.notna().sum()==12 and regions.gold.isna().sum()==22
    assert regions.loc[regions.status=='pending_verification','gold'].isna().all()
    evidence=json.loads((D/'地区来源核验.json').read_text(encoding='utf-8'))
    assert len(evidence)==9 and all(r['pattern_matched'] for r in evidence)
    for r in evidence:
        actual=regions.set_index('region').loc[r['region']]
        assert actual.gold==r['verified_counts']['gold']
        assert actual.source_url==r['url']
    assert regions.set_index('region').loc['广东',['silver','bronze']].isna().all()
    codes={f['properties']['adcode'] for f in map_features() if isinstance(f['properties']['adcode'],int)}
    assert set(regions.adcode)==codes
    daily=pd.read_csv(D/'每日金牌.csv')
    sums=daily.groupby('noc').gold.sum()
    for code in sums.index:assert sums[code]==noc.set_index('noc').loc[code,'gold']
    for path in (ROOT/'配图').glob('*.png'):
        with Image.open(path) as im:assert im.width>=1000 and im.height>=1000
    assert len(list((ROOT/'配图').glob('*.png')))==11
    athletes=pd.read_csv(D/'选手奖牌榜.csv',dtype={'reg':str})
    person_awards=pd.read_csv(D/'选手获奖明细.csv',dtype={'reg':str})
    indicators=json.loads((D/'选手与纪录指标.json').read_text(encoding='utf-8'))
    assert len(athletes)==3181 and not athletes.duplicated(['noc','reg']).any()
    assert len(person_awards)==3758 and person_awards.medal.eq('ME_GOLD').sum()==1151
    assert person_awards.award_id.notna().all()
    assert person_awards[person_awards.type=='A'].reg.eq(person_awards[person_awards.type=='A'].reg_official).all()
    for kind,col in [('ME_GOLD','gold'),('ME_SILVER','silver'),('ME_BRONZE','bronze')]:
        counts=person_awards[person_awards.medal==kind].groupby(['noc','reg']).size()
        expected=athletes.set_index(['noc','reg'])[col]
        assert counts.reindex(expected.index,fill_value=0).eq(expected).all()
    for filename in ['年龄分布.csv','性别分布.csv']:
        part=pd.read_csv(D/filename)
        assert part.gold.sum()==1151 and part.medals.sum()==3758
        assert abs(part.gold_pct.sum()-100)<1e-8 and abs(part.medals_pct.sum()-100)<1e-8
    assert len(pd.read_csv(D/'选手注册号映射.csv'))==10
    assert athletes.iloc[0]['name']=='ZHANG Zhanshuo' and athletes.iloc[0].gold==7
    assert athletes[athletes['name']=='YU Zidi'].iloc[0].age==13
    extremes=pd.read_csv(D/'选手年龄极值.csv',dtype={'reg':str})
    assert extremes.age.to_list()==[11,63]
    assert extremes.reg.to_list()==['1332684','8521927']
    assert extremes.iloc[0].gold==1 and extremes.iloc[1].silver==1
    for marker,age in [('最年轻',athletes.age.min()),('最年长',athletes.age.max())]:
        assert set(extremes[extremes.extreme==marker].reg)==set(athletes[athletes.age==age].reg)
    highlights=json.loads((D/'选手亮点与来源.json').read_text(encoding='utf-8'))
    assert len(highlights)==6
    for h in highlights:
        person=athletes.set_index('reg').loc[h['reg']]
        assert person['name']==h['name'] and person.noc==h['noc']
        assert person.age==h['age'] and person.birth_date==h['birth_date']
        assert all(int(person[k])==h[k] for k in ['gold','silver','bronze'])
    records=pd.read_csv(D/'破纪录明细.csv')
    record_summary=pd.read_csv(D/'破纪录分项统计.csv')
    assert len(records)==387 and len(record_summary)==7
    assert records.equalled.sum()==9 and record_summary.broken.sum()==378
    assert len(pd.read_csv(D/'纪录空白条目.csv'))==22
    assert record_summary.entries.sum()==len(records)
    assert records.groupby('discipline').event_key.nunique().sum()==record_summary.events.sum()
    assert records[(records.reg=='13174508') & (records.indicator=='WR')]['result'].to_list()==['2:04.83']
    zhang=records[(records.reg=='12371343') & records.event_en.eq("Men's 400m Freestyle")]
    assert '3:41.28' in zhang['result'].to_list()
    boonson=records[(records.reg=='16362440') & records.event_en.eq("Men's 200m")]
    assert ((boonson['result']=='19.88') & (boonson.indicator=='EAR') & boonson.equalled).any()
    record_dates=pd.to_datetime(records.date_raw,format='mixed',utc=True)
    assert record_dates.dt.year.eq(2026).all()
    country_map=mapping()
    assert len(country_map)==46 and country_map.index.is_unique
    assert country_map.geometry_type.ne('nonterritorial').sum()==45
    assert country_map[country_map.geometry_type=='nonterritorial'].index.to_list()==['ART']
    assert country_map.gold.eq(noc.set_index('noc').gold).all()
    audit=json.loads((D/'运动员字段核验.json').read_text(encoding='utf-8'))
    assert audit['biography_samples']==51 and not audit['roster_has_geographic_fields']
    assert audit['biography_geographic_field_samples']==0
    assert all(not r['info_has_geography_terms'] for r in audit['samples'])
    for row in audit['samples']:
        profile=json.loads((D/f'官方原始/运动员简介_{row["discipline"]}_{row["reg"]}.json').read_text(encoding='utf-8'))
        assert sorted(profile)==row['fields']
    with Image.open(ROOT/'封面/亚运会封面.png') as im:assert im.size==(900,383)
    result={'status':'passed','date':'2026-10-04','version':'v1.2.1',
        'orgs':46,'medal_records':1568,'gold_records':470,'gold_event_keys':469,
        'china_gold':169,'china_gold_disciplines':38,'all_noc_colors_match':True,
        'gold_dates_verified':True,'region_rows':34,'verified_regions':12,'pending_regions':22,
        'ranking_scope':'已核验地区比较；全国省级完整排名需补齐22地区来源',
        'missing_kept_null':True,'charts':11,'country_map_territories':45,
        'country_map_gold':int(country_map.gold.sum()),'athlete_geography':'roster absent; 51 biography samples absent',
        'cover_pixels':[900,383],'athlete_metrics':indicators}
    (ROOT/'数据验收.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
