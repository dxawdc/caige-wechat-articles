"""v2.0.0 | 2026-09-08 | 可离线复核本月范围；--refresh 只读公开元数据。"""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import urlopen,Request
from urllib.error import HTTPError,URLError
import json,argparse,subprocess
R=Path(__file__).resolve().parent
def eligible(d):
    dt=datetime.fromisoformat(d['created_at'].replace('Z','+00:00'))
    return datetime(2026,9,1,tzinfo=timezone.utc)<=dt<datetime(2026,10,1,tzinfo=timezone.utc) and not d['fork'] and not d['archived']
def run(refresh=False,use_gh=False):
    data=json.loads((R/'六个项目快照_v2.0.0.json').read_text(encoding='utf-8'))
    assert len(data)==6 and len({d['full_name'] for d in data})==6
    assert all(eligible(d) for d in data)
    # 明确排除刚更新的旧仓库、Fork 和归档仓库；测试月边界。
    sample={'created_at':'2026-09-01T00:00:00Z','fork':False,'archived':False}
    assert eligible(sample)
    for changes in [{'created_at':'2026-08-31T23:59:59Z'},{'created_at':'2026-10-01T00:00:00Z'},{'fork':True},{'archived':True}]:assert not eligible(sample|changes)
    result={'version':'v2.0.0','month':'2026-09 UTC','offline_passed':True,'selected':6,'boundary_checks':5}
    if refresh:
        checked=[]
        for d in data:
            url='https://api.github.com/repos/'+d['full_name']
            try:
                if use_gh:
                    p=subprocess.run(['gh','api','repos/'+d['full_name']],capture_output=True,encoding='utf-8',timeout=30)
                    if p.returncode:raise RuntimeError('GitHub CLI request failed')
                    v=json.loads(p.stdout)
                else:
                    with urlopen(Request(url,headers={'User-Agent':'caige-new-ai-repos-v2'}),timeout=20) as response:v=json.load(response)
                checked.append({'repo':v['full_name'],'created_at':v['created_at'],'stars':v['stargazers_count'],'eligible':eligible(v),'source':url})
            except (HTTPError,URLError,TimeoutError,RuntimeError,FileNotFoundError,subprocess.TimeoutExpired) as e:checked.append({'repo':d['full_name'],'error':type(e).__name__,'status':getattr(e,'code',None)})
        result['live']=checked
    out=R/'本地运行输出';out.mkdir(exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    (out/f'范围校验_{stamp}_v2.0.0.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true');p.add_argument('--use-gh',action='store_true',help='使用本机已登录的GitHub CLI，不读取或输出令牌');a=p.parse_args();run(a.refresh,a.use_gh)
