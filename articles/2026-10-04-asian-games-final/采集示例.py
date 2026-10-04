"""先用两个公开接口取得代表团奖牌榜；解压与重试在官方接口.py。"""
import pandas as pd
from 官方接口 import get, ROOT
from 映射 import ORG_ZH

orgs = get('/ALL/orgs/list', '代表团')
standings = get('/ALL/medals/standings', '奖牌榜')
by_noc = {row['Org']: row for row in standings}
rows = []
for org in orgs:
    code = org['Key']
    record = by_noc.get(code, {})
    count = record.get('Count', {})
    rows.append({
        'noc': code, 'name_zh': ORG_ZH[code],
        'official_rank': record.get('Rk'),
        'gold': count.get('ME_GOLD', {}).get('total', 0),
        'silver': count.get('ME_SILVER', {}).get('total', 0),
        'bronze': count.get('ME_BRONZE', {}).get('total', 0),
    })
df = pd.DataFrame(rows)
df['total'] = df[['gold','silver','bronze']].sum(axis=1)
df = df.sort_values(['gold','silver','bronze'], ascending=False)
print(df.head(10).to_string(index=False))
# 演示单独保存，不覆盖完整采集脚本所需的标准榜单字段。
df.to_csv(ROOT/'数据/奖牌榜采集示例.csv', index=False, encoding='utf-8-sig')
