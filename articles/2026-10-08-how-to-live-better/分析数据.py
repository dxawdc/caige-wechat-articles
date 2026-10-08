"""解析《高性价比人生指南》book/ 目录，输出条目表与汇总统计。

用法：python 分析数据.py <HowToLiveBetter 仓库目录>
性价比档的算法与仓库 index.html 一致：
  成本分 = 钱(0/少/多→0/1/2) + 时间(少/中/多→0/1/2) + 毅力(否/些/是→0/1/2)
  收益大：成本分0→极高，≤2→高，其余一般；收益中：成本分0→高，其余一般；收益小→一般
"""
from pathlib import Path
import json, re, sys
from collections import Counter
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '数据'
REPO = Path(sys.argv[1])

W = {'money': {'0': 0, '少': 1, '多': 2}, 'time': {'少': 0, '中': 1, '多': 2}, 'will': {'否': 0, '些': 1, '是': 2}}
KEY = {'钱': 'money', '时间': 'time', '毅力': 'will', '收益': 'level', '口径': 'lens'}
LENS = {'死亡率': '换寿命', '金钱': '换钱', '时间': '换时间精力', '自由': '换人身自由'}

rows = []
for f in sorted((REPO / 'book').glob('*.md')):
    sec_no, sec_title, e = None, None, None
    for line in f.read_text(encoding='utf-8').splitlines():
        if m := re.match(r'^# (\d+)\. (.+)$', line):
            sec_no, sec_title = int(m[1]), m[2].strip()
        elif m := re.match(r'^### (\d+)\. (.+)$', line):
            e = {'节': sec_no, '节名': sec_title, '条': int(m[1]), '标题': m[2].strip(),
                 'money': '', 'time': '', 'will': '', 'level': '', 'lens': '', '证据': '', '来源': '', '备注': '', '说人话': ''}
            rows.append(e)
        elif e and (m := re.match(r'^<!--\s*成本标签:\s*(.*?)\s*-->', line)):
            for kv in m[1].split():
                k, v = kv.split('=')
                e[KEY[k]] = v
        elif e and (m := re.match(r'^- 证据等级：\s*([ABC])', line)):
            e['证据'] = m[1]
        elif e and (m := re.match(r'^- 来源：(.*)$', line)):
            e['来源'] = m[1]
        elif e and (m := re.match(r'^- 备注：(.*)$', line)):
            e['备注'] = m[1]
        elif e and (m := re.match(r'^- 说人话：(.*)$', line)):
            e['说人话'] = m[1]

df = pd.DataFrame(rows)
df['成本分'] = [W['money'].get(a, 0) + W['time'].get(b, 0) + W['will'].get(c, 0) for a, b, c in zip(df.money, df.time, df.will)]
def tier(r):
    if r.level == '大':
        return '极高' if r.成本分 == 0 else ('高' if r.成本分 <= 2 else '一般')
    if r.level == '中':
        return '高' if r.成本分 == 0 else '一般'
    return '一般'
df['性价比'] = df.apply(tier, axis=1)
df['口径名'] = df.lens.map(LENS)
df['争议'] = df.备注.str.startswith('争议')
df['链接数'] = df.来源.str.count(r'https?://')
df['DOI'] = df.来源.str.count(r'doi\.org/')
df['PubMed'] = df.来源.str.count(r'pubmed|ncbi\.nlm')
df['政府站点'] = df.来源.str.count(r'https?://[^\s<>)]*\.gov(\.cn)?\b')

dom = Counter(u.lower() for s in df.来源 for u in re.findall(r'https?://([^/\s<>)]+)', s))
pd.DataFrame(dom.most_common(), columns=['域名', '次数']).to_csv(OUT / '来源域名.csv', index=False, encoding='utf-8-sig')

keep = ['节', '节名', '条', '标题', 'money', 'time', 'will', 'level', 'lens', '口径名', '成本分', '性价比', '证据', '争议', '链接数', 'DOI', 'PubMed', '政府站点', '说人话']
df[keep].rename(columns={'money': '钱', 'time': '时间', 'will': '毅力', 'level': '收益量级', 'lens': '口径'}).to_csv(OUT / '条目.csv', index=False, encoding='utf-8-sig')

sec = df.groupby(['节', '节名']).agg(条目=('条', 'size'), A=('证据', lambda s: (s == 'A').sum()), B=('证据', lambda s: (s == 'B').sum()),
                                   C=('证据', lambda s: (s == 'C').sum()), 极高=('性价比', lambda s: (s == '极高').sum()),
                                   高=('性价比', lambda s: (s == '高').sum()), 一般=('性价比', lambda s: (s == '一般').sum()),
                                   争议=('争议', 'sum'), 链接=('链接数', 'sum')).reset_index()
sec.to_csv(OUT / '章节统计.csv', index=False, encoding='utf-8-sig')

stats = {
    '条目': len(df), '章节': int(df.节.nunique()),
    '证据': dict(Counter(df.证据)), '性价比': dict(Counter(df.性价比)), '口径': dict(Counter(df.口径名)),
    '收益量级': dict(Counter(df.level)), '钱': dict(Counter(df.money)), '时间': dict(Counter(df.time)), '毅力': dict(Counter(df.will)),
    '零成本条目': int((df.成本分 == 0).sum()), '争议': int(df.争议.sum()),
    '来源链接': int(df.链接数.sum()), 'DOI链接': int(df.DOI.sum()), 'PubMed链接': int(df.PubMed.sum()), '政府站点链接': int(df.政府站点.sum()),
    '口径×性价比': {k: dict(Counter(g.性价比)) for k, g in df.groupby('口径名')},
    '口径×证据': {k: dict(Counter(g.证据)) for k, g in df.groupby('口径名')},
}
(OUT / '统计.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2, default=int), encoding='utf-8')
print(json.dumps(stats, ensure_ascii=False, indent=1, default=int))
