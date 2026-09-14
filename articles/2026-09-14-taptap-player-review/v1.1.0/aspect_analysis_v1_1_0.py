"""v1.1.0 | Reproduce contextual annotation counts; optionally audit original sampling.
This script counts supplied Codex annotations. It does NOT classify new text.
"""
from pathlib import Path
from collections import Counter
import argparse, json
import pandas as pd
ROOT=Path(__file__).parent

# BEGIN ASPECT_COUNT
def count_aspects(rows, group, polarity):
    cohort = [r for r in rows if r['group'] == group]
    counts = Counter()
    for row in cohort:
        # 一条评价的同一方面、同一态度最多计一次
        counts.update(set(row[polarity]))
    return pd.DataFrame([
        {'方面': aspect, '条数': n, '样本分母': len(cohort),
         '样本内占比': n / len(cohort)}
        for aspect, n in counts.most_common()
    ])
# END ASPECT_COUNT

def main():
    p=argparse.ArgumentParser();p.add_argument('--private-csv',type=Path);args=p.parse_args()
    out=ROOT/'outputs'
    rows=json.loads((out/'aspect_annotations_v1.1.0.json').read_text(encoding='utf8'))
    expected=json.loads((out/'aspect_summary_v1.1.0.json').read_text(encoding='utf8'))
    assert len(rows)==len({r['audit_id'] for r in rows})==80
    for g in ['高星','低星']:
        rr=[r for r in rows if r['group']==g];assert len(rr)==40
        assert all(r['score'] in ([4,5] if g=='高星' else [1,2]) for r in rr)
        for polarity in ['praise','criticism']:
            got=count_aspects(rows,g,polarity).set_index('方面')['条数'].to_dict()
            want={a:n for a,n in expected['groups'][g][polarity].items() if n}
            assert got==want
            assert all(len(r[polarity])==len(set(r[polarity])) for r in rr)
        assert sum(not(r['praise'] or r['criticism']) for r in rr)==expected['groups'][g]['no_specific_aspect']
    if args.private_csv:
        from analyze_v1_0_0 import THEMES
        d=pd.read_csv(args.private_csv,dtype={'review_id':str})
        mention=json.loads((out/'rating_theme_mentions_v1.1.0.json').read_text(encoding='utf8'))
        for g,mask in [('高星',d.score.ge(4)),('低星',d.score.le(2))]:
            df=d[mask]
            for a,pat in THEMES.items():
                assert len(df)==mention[a][g]['n']
                assert int(df.text.fillna('').str.contains(pat,case=False,regex=True).sum())==mention[a][g]['mentions']
            sample=df.sample(n=40,random_state=20260914)
            local=[r for r in rows if r['group']==g]
            assert sample.score.tolist()==[r['score'] for r in local]
        # Original ID membership is validated privately; public bundle has no IDs/text.
    print(count_aspects(rows,'高星','praise').to_string(index=False))
    print(count_aspects(rows,'低星','criticism').to_string(index=False))
    print('PASS: 80 annotations, polarity counts, cohort denominators'+(', full-corpus mentions' if args.private_csv else ''))

if __name__=='__main__':main()
