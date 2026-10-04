"""建立NOC、地图名称、行政区代码和点定位的明确连接表。"""
import pandas as pd
from 图表工具 import D

WORLD = dict(AFG='Afghanistan', BAN='Bangladesh', BRN='Bahrain', BRU='Brunei',
    BHU='Bhutan', UAE='United Arab Emirates', INA='Indonesia', IND='India',
    IRI='Iran', IRQ='Iraq', JOR='Jordan', JPN='Japan', KAZ='Kazakhstan',
    KGZ='Kyrgyzstan', CAM='Cambodia', KOR='Korea', KUW='Kuwait', LAO='Lao PDR',
    LBN='Lebanon', SRI='Sri Lanka', MYA='Myanmar', MGL='Mongolia', MAS='Malaysia',
    NEP='Nepal', OMA='Oman', PAK='Pakistan', PHI='Philippines', PRK='Dem. Rep. Korea',
    PLE='Palestine', QAT='Qatar', KSA='Saudi Arabia', SGP='Singapore', SYR='Syria',
    THA='Thailand', TJK='Tajikistan', TKM='Turkmenistan', TLS='Timor-Leste',
    UZB='Uzbekistan', VIE='Vietnam', YEM='Yemen')
POINTS = dict(HKG=(114.109497,22.396428), MAC=(113.543873,22.198745),
    SGP=(103.819836,1.352083), BRN=(50.637772,25.930414),
    QAT=(51.183884,25.354826), MDV=(73.22068,3.202778))
world_url = 'https://echarts.apache.org/examples/data/asset/geo/world.json'
province_url = 'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'
point_url = 'https://developers.google.com/public-data/docs/canonical/countries_csv'
records = []
for noc in pd.read_csv(D/'国家地区奖牌榜.csv').noc:
    assert noc in WORLD or noc in ['CHN','TPE','HKG','MAC','MDV','ART'], f'新代表团需补充映射：{noc}'
    adcode = dict(TPE=710000,HKG=810000,MAC=820000).get(noc)
    kind = 'world_polygon' if noc in WORLD else 'china_provincial_union' if noc=='CHN' else 'province_polygon' if adcode else 'point' if noc=='MDV' else 'nonterritorial'
    lon,lat = POINTS.get(noc,(None,None))
    records.append(dict(noc=noc,world_name=WORLD.get(noc,''),adcode=adcode,
        geometry_type=kind,longitude=lon,latitude=lat,
        boundary_source_url=world_url if noc in WORLD else province_url if noc=='CHN' or adcode else '',
        point_source_url=point_url if noc in POINTS else ''))
pd.DataFrame(records).to_csv(D/'代表团地图映射.csv',index=False,encoding='utf-8-sig')
print('46个代表团映射已生成：45个有地域，亚洲难民队单列。')
