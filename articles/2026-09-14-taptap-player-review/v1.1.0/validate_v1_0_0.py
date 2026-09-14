"""v1.0.0 | Validate aggregate denominators and optionally recompute from private rows."""
from pathlib import Path
import argparse,json,math,re
import pandas as pd
from analyze_v1_0_0 import THEMES, LAUNCH, wilson

ROOT=Path(__file__).parent;OUT=ROOT/'outputs'
def validate(private_csv=None):
    a=json.loads((OUT/'analysis_v1.0.0.json').read_text(encoding='utf8'))
    c=json.loads((OUT/'collection_summary_v1.0.0.json').read_text(encoding='utf8'))
    n=c['n'];checks={}
    checks['rating_counts_sum']=sum(a['rating_counts'].values())==n
    checks['rating_groups_sum']=sum(a['overall'][x] for x in ['high','middle','low'])==n
    checks['stage_counts_sum']=sum(x['n'] for x in a['stages'].values())==n
    checks['hour_counts_sum']=sum(x['n'] for x in a['hours'].values())==n
    checks['hour_missing_preserved']=a['hours']['未展示评价时长']['n']==n-c['played_hours_available']
    checks['daily_counts_sum']=sum(x['n'] for x in a['daily'].values())==n
    checks['no_fake_account_levels']=c['account_level_available']==0
    checks['pager_reached_end']=c['crawl_completed'] is True
    checks['theme_rates']=all(math.isclose(m['mentions']/n,m['mention_rate']) for m in a['themes'].values())
    checks['phase_theme_denominators']=all(v['n']==a['periods'][p]['n'] and math.isclose(v['mentions']/v['n'],v['rate']) for m in a['theme_periods'].values() for p,v in m.items())
    checks['nmf_document_counts']=sum(t['n'] for t in a['nmf']['topics'])==a['nmf']['documents']
    checks['nmf_phase_counts']=sum(sum(x.values()) for x in a['nmf']['period_counts'].values())==a['nmf']['documents']
    checks['wilson_limits']=all(0<=wilson(k,10)[0]<=k/10<=wilson(k,10)[1]<=1+1e-12 for k in [1,5,9])
    # Synthetic wording regression cases, not reposted user comments.
    examples=[('福利与任务','两位英雄联动产生额外伤害',False),
              ('福利与任务','联动活动的奖励可以领取',True),
              ('性能与适配','希望平衡优化，增加更多阵容',False),
              ('性能与适配','建议优化站位，避免技能浪费',False),
              ('性能与适配','换一套阵容就不会直接卡死',False),
              ('性能与适配','手机发热，画面卡顿',True),
              ('性能与适配','优化很好，运行流畅',True)]
    checks['theme_ambiguity_regressions']=all(bool(re.search(THEMES[k],text,re.I))==expected for k,text,expected in examples)
    checks['nine_chart_files']=len(list(OUT.glob('0[1-9]_*_v1.0.0.png')))==9
    if private_csv:
        d=pd.read_csv(private_csv,dtype={'review_id':str});d['text']=d.text.fillna('')
        d['version_time']=pd.to_datetime(d.version_time,utc=True).dt.tz_convert('Asia/Shanghai')
        checks['private_id_dedup']=len(d)==n==d.review_id.nunique()
        checks['private_star_range']=d.score.between(1,5).all().item()
        checks['private_rating_recomputed']=all(int(d.score.eq(int(s)).sum())==count for s,count in a['rating_counts'].items())
        checks['private_theme_recomputed']=all(int(d.text.str.contains(p,regex=True,case=False).sum())==a['themes'][k]['mentions'] for k,p in THEMES.items())
        windows=[]
        for key,start,end in [('首发前96小时',LAUNCH-pd.Timedelta(days=4),LAUNCH),('首发后96小时',LAUNCH,LAUNCH+pd.Timedelta(days=4))]:
            g=d[d.version_time.ge(start)&d.version_time.lt(end)];m=a['matched'][key]
            windows.append(set(g.review_id));assert len(g)==m['n'] and int(g.score.between(4,5).sum())==m['high'] and int(g.score.between(1,2).sum())==m['low']
        checks['private_matched_windows_recomputed']=not (windows[0]&windows[1])
    report={'checks':checks,'all_passed':all(checks.values()),'private_recomputed':bool(private_csv)}
    (OUT/'validation_v1.0.0.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    assert report['all_passed'],[k for k,v in checks.items() if not v]
    print(f'PASS {len(checks)} checks; private recomputation={bool(private_csv)}')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-csv',type=Path);a=p.parse_args();validate(a.private_csv)
