"""一个已核验团体冠军示例：同一地区同一获奖事件只计一次贡献。"""
import pandas as pd
from 图表工具 import D

medals = pd.read_csv(D / '奖牌明细.csv')
mask = ((medals.noc=='CHN') & (medals.discipline=='SHO') &
        (medals.medal=='ME_GOLD') &
        medals.event_en.str.contains('50m Rifle 3 Positions Men Team', regex=False) &
        (medals.gender=='M'))
selected = medals.loc[mask]
assert len(selected)==1
award_id = selected.iloc[0].award_id
# 来源：江苏省体育局2026-09-25该团体冠军报道，非出生地推断。
source = 'https://jsstyj.jiangsu.gov.cn/art/2026/9/25/art_40686_11835298.html'
athletes = pd.DataFrame([
    [award_id, '盛李豪', '江苏', source],
    [award_id, '刘宇坤', '陕西', source],
    [award_id, '张常鸿', '山东', source],
], columns=['award_id','athlete','registered_region','source_url'])
athletes.to_csv(D/'实获奖名单示例.csv',index=False,encoding='utf-8-sig')
contributions = athletes.drop_duplicates(['award_id','registered_region'])
print(contributions.groupby('registered_region').size())
assert contributions.award_id.nunique()==1
assert len(contributions)==3
