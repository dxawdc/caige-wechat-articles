"""v1.0.0 | 2026-09-08 | 标准库只读公开元数据，不覆盖文章统计快照。"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import json,datetime,time
R=Path(__file__).resolve().parent
def refresh():
    original=json.loads((R/'项目数据_v1.0.0.json').read_text(encoding='utf-8'));rows=[]
    for d in original:
        name=d['full_name'];url='https://api.github.com/repos/'+name
        try:
            with urlopen(Request(url,headers={'User-Agent':'caige-public-repo-guide-v1','Accept':'application/vnd.github+json'}),timeout=20) as response:data=json.load(response)
            rows.append({'repo':name,'stars':data['stargazers_count'],'created_at':data['created_at'],'pushed_at':data['pushed_at'],'archived':data['archived'],'license':(data.get('license') or {}).get('spdx_id'),'source':url})
        except (HTTPError,URLError,TimeoutError) as e:
            rows.append({'repo':name,'error':type(e).__name__,'status':getattr(e,'code',None)})
        time.sleep(.25)
    out=R/'本地运行输出';out.mkdir(exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc)
    target=out/('GitHub刷新_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')+'_v1.0.0.json')
    target.write_text(json.dumps({'version':'v1.0.0','checked_at':stamp.isoformat(),'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    print('完成：',target.name,'成功',sum('error' not in d for d in rows),'/',len(rows))
if __name__=='__main__':refresh()
