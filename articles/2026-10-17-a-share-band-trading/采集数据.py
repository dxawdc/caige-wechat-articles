"""采集A股主要指数日线开盘价与收盘价（腾讯行情），落盘为 数据/指数日线.json。"""
from pathlib import Path
import json
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '数据'
DATA.mkdir(exist_ok=True)
CUTOFF = '2026-10-16'
INDICES = {'sh000001': '上证指数', 'sh000016': '上证50', 'sh000300': '沪深300', 'sh000905': '中证500',
           'sh000852': '中证1000', 'sz399006': '创业板指', 'sh000688': '科创50'}


def get(code, year):
    q = urllib.parse.urlencode({'param': f'{code},day,{year}-01-01,{year}-12-31,400,'})
    req = urllib.request.Request('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?' + q,
                                 headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://gu.qq.com/'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)['data'][code]
            return d.get('day') or d.get('qfqday') or []
        except (OSError, ValueError, KeyError):
            if attempt == 3:
                raise
            time.sleep(1 + attempt)


def main():
    out = {}
    for code, name in INDICES.items():
        rows = {}
        for year in range(2012, 2027):
            for bar in get(code, year):
                # 字段：日期、开盘、收盘、最高、最低、成交量
                if bar[0] <= CUTOFF:
                    rows[bar[0]] = [float(bar[1]), float(bar[2])]
        days = sorted(rows)
        assert days and days[-1] == CUTOFF, (name, days[-1:])
        out[name] = {'code': code, 'rows': [[d] + rows[d] for d in days]}
        print(f'{name:6s} {code} {days[0]} ~ {days[-1]} {len(days)}条', flush=True)
    payload = {'source': '腾讯行情', 'cutoff': CUTOFF, 'fields': ['date', 'open', 'close'], 'series': out}
    (DATA / '指数日线.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
