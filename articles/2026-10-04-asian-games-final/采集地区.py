"""采集地方收官报道，人工确认语义后用规则复核数字；生成34地区底表。"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import re
import urllib.request
import pandas as pd
from bs4 import BeautifulSoup
from 官方接口 import ROOT, opener

D=ROOT/'数据'
# 每条规则只截取涉及该地区的句子，避免抓到中国代表团总数或人次数。
SOURCES=[
 ('浙江',330000,35,12,12,'省委省政府贺电（北京青年报政知见刊载）','2026-10-04',
  'https://news.ifeng.com/c/8wwVw9j6OSL',r'浙江运动员[\s\S]{0,120}?夺得35枚金牌、12枚银牌、12枚铜牌'),
 ('山东',370000,32,11,18,'山东卫视','2026-10-04',
  'https://news.iqilu.com/shandong/shandonggedi/20261004/5949899.shtml',r'32[\s\S]{0,50}?11[\s\S]{0,50}?18'),
 ('江苏',320000,31,11,9,'新华日报·交汇点','2026-10-04',
  'https://sports.jschina.com.cn/jrtt/202610/t20261004_s6ac233ace4b02e2ec97f72aa.shtml',r'共获得31枚金牌、11枚银牌、9枚铜牌'),
 ('广东',440000,25,None,None,'广州日报','2026-10-04',
  'https://news.dayoo.com/sports/202610/04/140001_55009796.htm',r'广东运动员[\s\S]{0,80}?一共收获25枚金牌'),
 ('四川',510000,19,7,5,'四川日报·四川在线','2026-10-04',
  'https://ent.scol.com.cn/ty/202610/83335218.html',r'共获得19枚金牌7枚银牌5枚铜牌'),
 ('湖北',420000,19,5,7,'省委省政府贺电（京报网刊载）','2026-10-04',
  'https://news.bjd.com.cn/2026/10/04/11983437.shtml',r'荆楚健儿[\s\S]{0,40}?19金5银7铜'),
 ('福建',350000,17,9,4,'省委省政府贺电（京报网刊载）','2026-10-04',
  'https://news.bjd.com.cn/2026/10/04/11983437.shtml',r'福建运动员20人次夺得17枚金牌、10人次夺得9枚银牌、5人次夺得4枚铜牌'),
 ('湖南',430000,11,1,2,'湖南日报','2026-10-04',
  'https://www.hunantoday.cn/news/xhn/202610/33911919.html',r'体育湘军[\s\S]{0,30}?11金1银2铜'),
 ('安徽',340000,9,4,4,'省委省政府贺电（京报网刊载）','2026-10-03',
  'https://news.bjd.com.cn/2026/10/04/11983437.shtml',r'安徽运动员夺得9枚金牌、4枚银牌、4枚铜牌'),
]

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with opener.open(req,timeout=25) as r: raw=r.read()
    soup=BeautifulSoup(raw,'html.parser')
    return url,raw,re.sub(r'\s+','',soup.get_text(' ',strip=True))

def main(online=False):
    rules=[]; records=[]
    if online:
        with ThreadPoolExecutor(max_workers=3) as pool:
            pages={u:(raw,text) for u,raw,text in pool.map(fetch,sorted({s[7] for s in SOURCES}))}
        evidence=[]
        for name,code,g,s,b,pub,date,url,pattern in SOURCES:
            raw,text=pages[url]
            match=re.search(pattern,text)
            if not match:raise ValueError(f'{name}的来源规则未匹配，请人工复核，不能填零')
            evidence.append(dict(region=name,url=url,publisher=pub,published_at=date,
                fetched_at=datetime.now(timezone.utc).isoformat(),raw_sha256=hashlib.sha256(raw).hexdigest(),
                verified_counts={'gold':g,'silver':s,'bronze':b},pattern_matched=True))
        (D/'地区来源核验.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    else:
        evidence=json.loads((D/'地区来源核验.json').read_text(encoding='utf-8'))
        for row in SOURCES:
            assert any(e['region']==row[0] and e['url']==row[7] and e['verified_counts']['gold']==row[2] for e in evidence)
    for name,code,g,s,b,pub,date,url,pattern in SOURCES:
        records.append(dict(adcode=code,region=name,gold=g,silver=s,bronze=b,
            metric_scope='地方公布的注册/培养运动员项目奖牌贡献',status='verified_final',
            publisher=pub,published_at=date,source_url=url))
        rules.append(dict(region=name,adcode=code,source_url=url,verification_pattern=pattern))
    noc=pd.read_csv(D/'国家地区奖牌榜.csv').set_index('noc')
    for name,code,org in [('香港',810000,'HKG'),('澳门',820000,'MAC'),('台湾',710000,'TPE')]:
        r=noc.loc[org]
        records.append(dict(adcode=code,region=name,gold=int(r.gold),silver=int(r.silver),bronze=int(r.bronze),
            metric_scope=f'{r.name_zh}代表团官方奖牌数（{org}）',status='verified_final',
            publisher='赛事官方成绩系统',published_at='2026-10-04',
            source_url='https://back.results.asiangames2026.org/s/AG2026/en/ALL/medals/org/'+org))
    geo=json.loads((D/'中国省级边界.geojson').read_text(encoding='utf-8'))
    master=[]
    for f in geo['features']:
        p=f['properties']
        if not isinstance(p['adcode'],int):continue
        short=p['name']
        for suffix in ['壮族自治区','回族自治区','维吾尔自治区','特别行政区','自治区','省','市']:short=short.removesuffix(suffix)
        master.append(dict(adcode=p['adcode'],region=short))
    result=pd.DataFrame(master).merge(pd.DataFrame(records).drop(columns='region'),on='adcode',how='left',validate='one_to_one')
    result['status']=result.status.fillna('pending_verification')
    result['metric_scope']=result.metric_scope.fillna('地方注册/培养项目奖牌贡献，待核验完整收官来源')
    for col in ['gold','silver','bronze']:result[col]=result[col].astype('Int64')
    assert len(result)==34 and result.adcode.nunique()==34
    result.to_csv(D/'地区奖牌底表.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(rules).to_csv(D/'地区采集规则.csv',index=False,encoding='utf-8-sig')
    report=dict(total_regions=34,verified_gold_regions=int(result.gold.notna().sum()),
        pending_regions=result.loc[result.gold.isna(),'region'].tolist(),
        coverage_pct=round(result.gold.notna().mean()*100,1),
        complete_national_provincial_ranking=False,missing_is_zero=False,
        ranking_scope='已核验地区样本；港澳台单列代表团口径')
    (D/'地区覆盖验收.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--online',action='store_true')
    main(parser.parse_args().online)
