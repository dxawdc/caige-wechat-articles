"""从 USGS 地震目录（FDSN Event API）采集本文用到的地震数据，保存为 CSV。

USGS 单次查询最多返回 20000 条，因此按时间分段下载后合并。
"""
from pathlib import Path
import io
import time

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '数据'
API = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
CUTOFF = '2026-10-16'          # 数据截止日（UTC，不含当天）
COLS = ['time', 'latitude', 'longitude', 'depth', 'mag', 'magType', 'place', 'type', 'id']


def query(start, end, **params):
    """按年分段请求，返回合并后的 DataFrame。"""
    frames = []
    edges = pd.date_range(start, end, freq='YS').strftime('%Y-%m-%d').tolist()
    edges = sorted(set([start] + edges + [end]))
    for a, b in zip(edges[:-1], edges[1:]):
        for retry in range(3):
            try:
                r = requests.get(API, params={'format': 'csv', 'starttime': a, 'endtime': b,
                                              'eventtype': 'earthquake', 'orderby': 'time-asc', **params},
                                 timeout=120)
                r.raise_for_status()
                break
            except requests.RequestException:
                time.sleep(5)
        else:
            raise RuntimeError(f'下载失败：{a}~{b}')
        if r.text.strip():
            frames.append(pd.read_csv(io.StringIO(r.text)))
        print(f'\r{a} ~ {b}', end='')
    print()
    df = pd.concat(frames, ignore_index=True)[COLS].drop_duplicates('id')
    return df.sort_values('time').reset_index(drop=True)


TASKS = {
    # 全球6级以上：看几十年来大地震是否变多
    '全球6级以上_1950起.csv': dict(start='1950-01-01', minmagnitude=6),
    # 全球5级以上近10年：分布地图、震级规律、月份分布
    '全球5级以上_2016起.csv': dict(start='2016-01-01', minmagnitude=5),
    # 全球4.5级以上最近30天：最近一个月的全球地图
    '全球4.5级以上_最近30天.csv': dict(start='2026-09-16', minmagnitude=4.5),
    # 中国及周边4.5级以上：各省分布与历年变化
    '中国周边4.5级以上_1976起.csv': dict(start='1976-01-01', minmagnitude=4.5,
                                     minlatitude=3, maxlatitude=54, minlongitude=73, maxlongitude=136),
    # 堪察加8.8级地震（2025-07-29 UTC）前后：余震衰减
    '堪察加序列_2025.csv': dict(start='2025-07-01', minmagnitude=4.5,
                              latitude=52.5, longitude=160.3, maxradiuskm=500),
}

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for name, p in TASKS.items():
        p = dict(p)
        start = p.pop('start')
        df = query(start, CUTOFF, **p)
        df.to_csv(OUT / name, index=False, encoding='utf-8')
        print(name, len(df))
