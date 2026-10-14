"""采集A股指数（腾讯行情）与美韩指数（Yahoo Finance）日收盘，统一落盘为 数据/指数日线.json。"""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
import time
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '数据'
DATA.mkdir(exist_ok=True)
CUTOFF = '2026-10-14'
# 腾讯行情：2017年以来长序列（含2016年末基准）+ 2026年对比用指数
CN_LONG = {'sh000001': '上证指数', 'sh000300': '沪深300'}
CN_2026 = {'sh000016': '上证50', 'sz399303': '国证2000', 'sh000852': '中证1000', 'sh000905': '中证500',
           'sz399001': '深证成指', 'sz399006': '创业板指', 'sh000688': '科创50'}
# Yahoo：按交易所本地日期取收盘；美股在北京时间晚上仍是盘中，需单独截止
OVERSEAS = {'^KS11': ('KOSPI', 'Asia/Seoul', '2026-10-14'),
            '^GSPC': ('标普500', 'America/New_York', '2026-10-13'),
            '^IXIC': ('纳斯达克', 'America/New_York', '2026-10-13')}


def get_json(url, headers):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', **headers})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def tencent(code, y0, y1):
    rows = {}
    # 单次最多返回约一年，按年分段
    for year in range(y0, y1 + 1):
        q = urllib.parse.urlencode({'param': f'{code},day,{year}-01-01,{year}-12-31,400,'})
        r = get_json('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?' + q, {'Referer': 'https://gu.qq.com/'})
        for bar in r['data'][code].get('day') or r['data'][code].get('qfqday') or []:
            rows[bar[0]] = float(bar[2])
    return [[d, rows[d]] for d in sorted(rows) if d <= CUTOFF]


def yahoo(symbol, tz, cutoff):
    q = urllib.parse.urlencode({'period1': int(datetime(2016, 12, 1, tzinfo=timezone.utc).timestamp()),
                                'period2': int(datetime(2026, 10, 16, tzinfo=timezone.utc).timestamp()),
                                'interval': '1d'})
    r = get_json(f'https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?{q}', {})
    r = r['chart']['result'][0]
    assert r['meta']['exchangeTimezoneName'] == tz
    zone = ZoneInfo(tz)
    rows = {}
    for t, c in zip(r['timestamp'], r['indicators']['quote'][0]['close']):
        d = datetime.fromtimestamp(t, zone).date().isoformat()
        if c is not None and d <= cutoff:
            rows[d] = float(c)
    return [[d, rows[d]] for d in sorted(rows)]


def main():
    out = {}
    for code, name in CN_LONG.items():
        out[name] = {'source': '腾讯行情', 'code': code, 'cutoff': CUTOFF, 'rows': tencent(code, 2016, 2026)}
    for code, name in CN_2026.items():
        out[name] = {'source': '腾讯行情', 'code': code, 'cutoff': CUTOFF, 'rows': tencent(code, 2025, 2026)}
    for symbol, (name, tz, cutoff) in OVERSEAS.items():
        out[name] = {'source': 'Yahoo Finance', 'code': symbol, 'cutoff': cutoff, 'rows': yahoo(symbol, tz, cutoff)}
    for name, v in out.items():
        assert v['rows'][-1][0] == v['cutoff'], (name, v['rows'][-1])
        print(f"{name:8s} {len(v['rows']):5d} 条  {v['rows'][0][0]} ~ {v['rows'][-1][0]}  {v['rows'][-1][1]:.2f}")
    (DATA / '指数日线.json').write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
