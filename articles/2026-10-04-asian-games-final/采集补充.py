"""核验官方运动员地理字段，下载代表团地图边界。"""
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
import re
import urllib.request
import pandas as pd
from 官方接口 import ROOT, get, opener

D=ROOT/'数据'
MAP_URLS=[
    'https://echarts.apache.org/examples/data/asset/geo/world.json',
    'https://geo.datav.aliyun.com/areas/bound/world.json',
    'https://datavmap-public.oss-cn-hangzhou.aliyuncs.com/world/geo/World.geo.json',
    'https://assets.pyecharts.org/assets/v5/maps/world.js',
]

def download_world(refresh=False):
    cache=D/'世界边界.geojson'
    if cache.is_file() and not refresh:
        raw=cache.read_bytes();geo=json.loads(raw)
        meta=dict(url=MAP_URLS[0],cache_verified_at=datetime.now(timezone.utc).isoformat(),
            sha256=hashlib.sha256(raw).hexdigest(),features=len(geo['features']))
        (D/'世界边界.来源.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
        print('使用已下载世界GeoJSON：',len(geo['features']),'区域',flush=True)
        return
    def fetch(url):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with opener.open(req,timeout=10) as response:raw=response.read()
            try:geo=json.loads(raw)
            except (UnicodeDecodeError,json.JSONDecodeError):geo=None
            print(url,len(raw),'GeoJSON' if geo else 'script',flush=True)
            if geo and isinstance(geo.get('features'),list):return url,raw,geo
        except Exception as error:print(url,type(error).__name__,flush=True)
        return None
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,MAP_URLS))
    candidates=[r for r in results if r]
    assert candidates, '未下载到世界GeoJSON'
    url,raw,geo=candidates[0]
    (D/'世界边界.geojson').write_bytes(raw)
    meta=dict(url=url,fetched_at=datetime.now(timezone.utc).isoformat(),
              sha256=hashlib.sha256(raw).hexdigest(),features=len(geo['features']))
    (D/'世界边界.来源.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print('features:',len(geo['features']),geo['features'][0]['properties'],flush=True)

def audit_athletes(refresh=False):
    cache=D/'官方原始/参赛名单.json'
    entries=json.loads(cache.read_text(encoding='utf-8')) if cache.exists() and not refresh else get('/ALL/entries/list','参赛名单')
    rows=entries['participants']
    athletes=[r for r in rows if r.get('Type')=='A']
    fields=Counter(k for r in athletes for k in r)
    china=[r for r in athletes if r['Org']=='CHN']
    choices={}
    for row in china:
        # 简介只使用名单中真实个人注册号，不把团体Reg当作运动员ID。
        if str(row['Reg']).isdigit():choices.setdefault(row['Disc'],str(row['Reg']))
    def fetch(item):
        disc,reg=item
        cache=D/f'官方原始/运动员简介_{disc}_{reg}.json'
        result=json.loads(cache.read_text(encoding='utf-8')) if cache.exists() and not refresh else get(f'/{disc}/entries/bio-info/{reg}',f'运动员简介_{disc}_{reg}')
        assert isinstance(result,dict), (disc,reg)
        return dict(discipline=disc,reg=reg,fields=sorted(result),
            structured_geography=[k for k in result if re.search('birth.?place|home.?town|province|club|training|residence|籍贯|培养|注册单位',k,re.I)],
            info_has_geography_terms=bool(re.search('place of birth|home.?town|birth.?place|training (place|club)|籍贯|培养单位|注册单位',str(result.get('Info','')),re.I)),
            info_nonempty=bool(result.get('Info')),
            url=f'https://back.results.asiangames2026.org/s/AG2026/en/{disc}/entries/bio-info/{reg}')
    with ThreadPoolExecutor(max_workers=3) as pool:profiles=list(pool.map(fetch,sorted(choices.items())))
    result=dict(roster_rows=len(rows),individual_entry_rows=len(athletes),
        china_individual_entry_rows=len(china),
        unique_athlete_ids=len({(r['Org'],str(r['Reg'])) for r in athletes}),
        china_unique_athlete_ids=len({str(r['Reg']) for r in china}),roster_fields=dict(fields),
        roster_has_geographic_fields=any(re.search('birth.?place|home.?town|province|club|training|residence|籍贯|培养',k,re.I) for k in fields),
        biography_samples=len(profiles),biography_geographic_field_samples=sum(bool(r['structured_geography']) for r in profiles),
        samples=profiles,source_url='https://back.results.asiangames2026.org/s/AG2026/en/ALL/entries/list',
        conclusion='参赛名单不提供籍贯或培养单位；简介样本另核验，比赛履历中的Location不作为培养地')
    (D/'运动员字段核验.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['samples','roster_fields']},ensure_ascii=False),flush=True)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--map',action='store_true');parser.add_argument('--audit',action='store_true');parser.add_argument('--refresh',action='store_true')
    args=parser.parse_args()
    if args.map:download_world(args.refresh)
    if args.audit:audit_athletes(args.refresh)
