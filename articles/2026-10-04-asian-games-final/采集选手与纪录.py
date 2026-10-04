"""采集官方获奖运动员榜、生日与性别，以及各分项的破纪录清单。"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import pandas as pd
from 官方接口 import ROOT, RAW, get

D=ROOT/'数据'
CACHE=D/'选手简介缓存'
CACHE.mkdir(exist_ok=True)

def read_or_get(path,name,refresh=False):
    file=RAW/(name+'.json')
    return json.loads(file.read_text(encoding='utf-8')) if file.exists() and not refresh else get(path,name)

def canonical_athletes(rows):
    """官方短注册号为同一选手重复行时，以正式注册号及获奖项目集合归并。"""
    real={(r['Org'],str(r['Reg'])):r for r in rows if str(r['Reg']).isdigit()}
    aliases=[]
    for row in rows:
        if str(row['Reg']).isdigit():continue
        targets=[r for r in real.values() if r['Org']==row['Org'] and r['Name']==row['Name']
                 and r['Medals'][0]['Disc']==row['Medals'][0]['Disc']]
        assert len(targets)==1, row['Reg']
        target=targets[0]
        keys=lambda r:{(m['Disc'],m['Event'],m['Medal']) for m in r['Medals']}
        assert keys(row)<=keys(target), '别名行必须是正式行的已获奖项目子集'
        aliases.append(dict(noc=row['Org'],alias_reg=row['Reg'],reg=target['Reg'],name=row['Name']))
    pd.DataFrame(aliases).to_csv(D/'选手注册号映射.csv',index=False,encoding='utf-8-sig')
    return list(real.values())

def collect_profiles(athletes,refresh=False,workers=6):
    combined=D/'获奖选手原始简介.json'
    previous=json.loads(combined.read_text(encoding='utf-8')) if combined.exists() else []
    available={(r['noc'],r['reg']):r for r in previous} if not refresh else {}
    def one(row):
        reg=str(row['Reg']);noc=row['Org'];disc=row['Medals'][0]['Disc']
        key=(noc,reg)
        if key in available:return available[key]
        file=CACHE/f'{disc}_{reg}.json'
        if file.exists() and not refresh:return json.loads(file.read_text(encoding='utf-8'))
        # 复用此前已经采集的同一简介；简介原始字段完整保存。
        old=RAW/f'运动员简介_{disc}_{reg}.json'
        bio=json.loads(old.read_text(encoding='utf-8')) if old.exists() and not refresh else get(f'/{disc}/entries/bio-info/{reg}')
        valid=lambda r:isinstance(r,dict) and str(r.get('Reg'))==reg and r.get('Org')==noc and r.get('Type')=='A'
        source=f'https://back.results.asiangames2026.org/s/AG2026/en/{disc}/entries/bio-info/{reg}'
        if not valid(bio):
            alternative=get(f'/{disc}/entries/bio/{reg}')
            if isinstance(alternative,dict) and valid(alternative.get('participant')):
                bio=alternative['participant'];source=f'https://back.results.asiangames2026.org/s/AG2026/en/{disc}/entries/bio/{reg}'
            else:bio=None
        record=dict(noc=noc,reg=reg,discipline=disc,
            source_url=source,profile_status='available' if bio else 'not_available',
            fetched_at=datetime.now(timezone.utc).isoformat(),raw=bio)
        file.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        return record
    records=[]; failures=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(one,r):r for r in athletes}
        for job in as_completed(jobs):
            try:records.append(job.result())
            except Exception as error:
                r=jobs[job];failures.append(dict(noc=r['Org'],reg=r['Reg'],error=type(error).__name__))
            if (len(records)+len(failures))%100==0:
                print(json.dumps(dict(profiles=len(records),total=len(athletes),failures=len(failures)),ensure_ascii=False),flush=True)
    assert not failures, failures[:10]
    records.sort(key=lambda r:(r['noc'],r['reg']))
    content=json.dumps(records,ensure_ascii=False,indent=2).encode('utf-8')
    combined.write_bytes(content)
    (D/'获奖选手原始简介.来源.json').write_text(json.dumps(dict(rows=len(records),
        sha256=hashlib.sha256(content).hexdigest(),sources='每条记录保留官方简介URL和读取时间'),ensure_ascii=False,indent=2),encoding='utf-8')
    return records

def collect_records(refresh=False):
    disciplines=json.loads((RAW/'项目.json').read_text(encoding='utf-8'))
    chosen=[r for r in disciplines if r.get('HasRecords')]
    def one(r):
        code=r['Key']
        result=read_or_get(f'/{code}/records/broken','破纪录_'+code,refresh)
        assert isinstance(result,dict) and 'records' in result, code
        # v2清单是另一版页面接口；传统清单空时检查v2，使用同一分项唯一清单。
        if not result['records']:
            alternative=read_or_get(f'/{code}/records-v2/broken','破纪录V2_'+code,refresh)
            if isinstance(alternative,dict) and alternative.get('records'):result=alternative
        return dict(discipline=code,raw=result)
    with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(one,chosen))
    (D/'分项破纪录原始.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(record_disciplines_checked=len(records),nonempty=sum(bool(r['raw']['records']) for r in records)),ensure_ascii=False),flush=True)

def main(refresh=False,workers=6):
    athletes=read_or_get('/ALL/medals/multi-medallists','多奖牌运动员',refresh)
    assert isinstance(athletes,list) and athletes
    assert len({(r['Org'],str(r['Reg'])) for r in athletes})==len(athletes)
    assert all(r['Medals'] and len(r['Medals'])==r['total'] for r in athletes)
    print(json.dumps(dict(athletes=len(athletes),gold_max=max(r['ME_GOLD'] for r in athletes),top=[(r['Name'],r['ME_GOLD']) for r in athletes[:12]]),ensure_ascii=False),flush=True)
    collect_records(refresh)
    collect_profiles(canonical_athletes(athletes),refresh,workers)
    print('获奖运动员简介及分项纪录采集完成。',flush=True)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');parser.add_argument('--workers',type=int,default=6)
    args=parser.parse_args();main(args.refresh,args.workers)
