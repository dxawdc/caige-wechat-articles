"""v1.0.0 | Convert private public-page snapshots into minimal analytical rows."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
import pandas as pd

LAUNCH = pd.Timestamp('2026-09-10 07:00:00', tz='Asia/Shanghai')

def prepare(raw, output):
    rows, seen, duplicates = [], set(), 0
    for path in sorted(raw.glob('page_*_v1.0.0.json')):
        obj = json.loads(path.read_text(encoding='utf8'))
        for item in obj['data'].get('list', []):
            moment = item.get('moment', {})
            review = moment.get('review')
            if not review:
                continue
            if review['id'] in seen:
                duplicates += 1
                continue  # freeze first encountered version during this crawl
            seen.add(review['id'])
            user = moment.get('author', {}).get('user', {})
            contents = review.get('contents', {})
            text = contents.get('raw_text')
            if not text:
                text = html.unescape(re.sub('<[^>]+>', ' ', contents.get('text', '')))
            text = re.sub(r'\s+', ' ', text).strip()
            created = moment.get('created_time')
            edited = moment.get('edited_time') or created
            rows.append({
                'review_id': str(review['id']),
                'user_key': hashlib.sha256(str(user.get('id')).encode()).hexdigest()[:16],
                'created_time': created, 'edited_time': edited,
                'version_time': max(created, edited),
                'is_edited': bool(moment.get('edited')),
                'score': review.get('score'),
                'stage': review.get('stage'),
                'stage_label': review.get('stage_label') or '未展示状态',
                'played_seconds': review.get('played_spent'),
                'total_played_seconds': review.get('total_played_spent'),
                'hidden_spent': review.get('hidden_spent', False),
                'has_badge': bool(user.get('badges')),
                'account_level': user.get('level'),
                'ups': moment.get('stat', {}).get('ups', 0),
                'text': text, 'text_length': len(text),
                'source_page': path.name,
            })
    df = pd.DataFrame(rows)
    for key in ('created_time', 'edited_time', 'version_time'):
        df[key] = pd.to_datetime(df[key], unit='s', utc=True).dt.tz_convert('Asia/Shanghai')
    df['version_day'] = df.version_time.dt.strftime('%Y-%m-%d')
    df['cross_launch_edit'] = (df.created_time < LAUNCH) & (df.version_time >= LAUNCH)
    df['rating_group'] = df.score.map({1:'低星（1–2）',2:'低星（1–2）',3:'中星（3）',4:'高星（4–5）',5:'高星（4–5）'}).fillna('未评分')
    df['positive'] = df.score.ge(4) & df.score.le(5)
    df['negative'] = df.score.ge(1) & df.score.le(2)
    df['played_hours'] = df.played_seconds / 3600
    df['play_group'] = pd.cut(df.played_hours, [-0.001,1,5,20,float('inf')], right=False,
                              labels=['不足1小时','1–5小时','5–20小时','20小时及以上']).astype('string').fillna('未展示评价时长')
    df['period'] = '更早版本'
    df.loc[(df.version_time >= LAUNCH-pd.Timedelta(days=7)) & (df.version_time < LAUNCH),'period']='首发前7天'
    df.loc[(df.version_time >= LAUNCH) & (df.version_time < LAUNCH+pd.Timedelta(days=1)),'period']='首发首24小时'
    df.loc[(df.version_time >= LAUNCH+pd.Timedelta(days=1)) & (df.version_time < LAUNCH+pd.Timedelta(days=4)),'period']='首发第2–4天'
    df.loc[df.version_time >= LAUNCH+pd.Timedelta(days=4),'period']='第5天未完整'
    output.mkdir(parents=True, exist_ok=True)
    df.to_csv(output/'reviews_private_v1.0.0.csv', index=False, encoding='utf-8-sig')
    state=json.loads((raw/'checkpoint_v1.0.0.json').read_text(encoding='utf8'))
    summary={'n':len(df),'unique_users':df.user_key.nunique(),'duplicate_rows':duplicates,
             'pages':state['pages'],'crawl_completed':state['completed'],
             'started_at':state['started_at'],'finished_at':state['updated_at'],
             'api_totals':sorted(set(state['totals_reported'])),
             'stages':df.stage_label.value_counts().to_dict(),
             'scores':df.score.value_counts().sort_index().to_dict(),
             'periods':df.period.value_counts().to_dict(),
             'created_min':str(df.created_time.min()),'version_min':str(df.version_time.min()),
             'version_max':str(df.version_time.max()),'cross_launch_edits':int(df.cross_launch_edit.sum()),
             'edited':int(df.is_edited.sum()),'played_hours_available':int(df.played_hours.notna().sum()),
             'account_level_available':int(df.account_level.notna().sum()),
             'text_duplicates':int(df.text.duplicated().sum()),'empty_text':int(df.text.eq('').sum())}
    (output/'collection_summary_v1.0.0.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return df

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();prepare(a.raw,a.output)
