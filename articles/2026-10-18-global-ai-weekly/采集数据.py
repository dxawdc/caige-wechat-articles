"""采集芯片股日线收盘价（Yahoo Finance），计算本周（10月12日—16日）累计涨跌幅。

周涨跌幅 = 10月16日收盘 / 上周最后一个交易日收盘 - 1。
韩国10月9日（韩文日）、日本10月12日（体育日）休市，基准日按各市场实际交易日取。
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import urllib.request

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '数据'
OUT.mkdir(exist_ok=True)

STOCKS = [  # 代码, 中文名, 市场
    ('000660.KS', 'SK海力士', '韩国'), ('005930.KS', '三星电子', '韩国'),
    ('6857.T', '爱德万测试', '日本'), ('9984.T', '软银集团', '日本'),
    ('AMD', 'AMD', '美国'), ('AVGO', '博通', '美国'), ('TSM', '台积电ADR', '美国'),
    ('ASML.AS', '阿斯麦', '荷兰'), ('NVDA', '英伟达', '美国'),
    ('SOXX', '半导体ETF（SOXX）', '美国'),
]
START, END = '2026-09-15', '2026-10-18'
WEEK_START, WEEK_END = '2026-10-12', '2026-10-16'


def fetch(code):
    p1 = int(datetime.fromisoformat(START).replace(tzinfo=timezone.utc).timestamp())
    p2 = int(datetime.fromisoformat(END).replace(tzinfo=timezone.utc).timestamp())
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}?period1={p1}&period2={p2}&interval=1d'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    d = json.load(urllib.request.urlopen(req, timeout=30))['chart']['result'][0]
    off = d['meta']['gmtoffset']
    days = [datetime.fromtimestamp(t + off, timezone.utc).strftime('%Y-%m-%d') for t in d['timestamp']]
    return pd.Series(d['indicators']['quote'][0]['close'], index=days, name=code).dropna()


rows, closes = [], {}
for code, name, mkt in STOCKS:
    s = fetch(code)
    closes[code] = s
    base_day = s[s.index < WEEK_START].index[-1]
    end_day = s[s.index <= WEEK_END].index[-1]
    week = s[(s.index >= WEEK_START) & (s.index <= WEEK_END)]
    daily = s.pct_change() * 100
    # 截至周五的连续下跌天数
    streak = 0
    for v in daily[daily.index <= WEEK_END][::-1]:
        if v < 0:
            streak += 1
        else:
            break
    rows.append({
        '代码': code, '名称': name, '市场': mkt,
        '基准日': base_day, '基准收盘': s[base_day], '周五收盘': s[end_day],
        '周涨跌幅%': round((s[end_day] / s[base_day] - 1) * 100, 2),
        '10月15日涨跌幅%': round(daily.get('2026-10-15', float('nan')), 2),
        '本周交易日': len(week),
        '截至周五连跌天数': streak,
        '距10月高点%': round((s[end_day] / s[s.index >= '2026-10-01'].max() - 1) * 100, 2),
    })

res = pd.DataFrame(rows).sort_values('周涨跌幅%')
res.to_csv(OUT / '芯片股本周涨跌幅.csv', index=False, encoding='utf-8-sig')
pd.DataFrame(closes).sort_index().to_csv(OUT / '芯片股日线收盘价.csv', encoding='utf-8-sig')
print(res.to_string(index=False))
