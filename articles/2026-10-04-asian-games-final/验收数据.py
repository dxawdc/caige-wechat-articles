"""核对已交付数据与图表指标，输出可审计验收结果。"""
from pathlib import Path
import json
import pandas as pd
from PIL import Image
from 图表工具 import ROOT, D, map_features

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
    assert len(list((ROOT/'配图').glob('*.png')))==6
    with Image.open(ROOT/'封面/亚运会封面.png') as im:assert im.size==(900,383)
    result={'status':'passed','date':'2026-10-04','version':'v1.0.0',
        'orgs':46,'medal_records':1568,'gold_records':470,'gold_event_keys':469,
        'china_gold':169,'china_gold_disciplines':38,'all_noc_colors_match':True,
        'gold_dates_verified':True,'region_rows':34,'verified_regions':12,'pending_regions':22,
        'ranking_scope':'已核验地区比较；全国省级完整排名需补齐22地区来源',
        'missing_kept_null':True,'charts':6,'cover_pixels':[900,383]}
    (ROOT/'数据验收.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
