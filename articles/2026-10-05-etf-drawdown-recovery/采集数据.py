"""采集16只ETF近一年前复权收盘价；第二来源可用时逐日核对，记录实际范围。"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from lxml import html
import json
import time
import math
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '数据'
START, END = '2025-09-30', '2026-09-30'
ETFS = {'sh510300':'沪深300ETF', 'sh510500':'中证500ETF', 'sz159915':'创业板ETF',
        'sh588000':'科创50ETF', 'sh510050':'上证50ETF', 'sz159845':'中证1000ETF',
        'sh512880':'证券ETF', 'sh512480':'半导体ETF', 'sh512010':'医药ETF',
        'sz159928':'消费ETF', 'sz159516':'半导体设备ETF', 'sh515790':'光伏ETF',
        'sh512170':'医疗ETF', 'sh512690':'酒ETF', 'sz159819':'人工智能ETF', 'sh516160':'新能源ETF'}


def fetch_json(url, params):
    url += '?' + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0', 'Referer':'https://gu.qq.com/'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def collect_one(item):
    symbol, name = item
    raw = DATA / '原始'
    raw.mkdir(parents=True, exist_ok=True)
    tx_path, em_path = raw / f'{symbol[2:]}_腾讯.json', raw / f'{symbol[2:]}_东方财富.json'
    tx = json.loads(tx_path.read_text(encoding='utf-8')) if tx_path.exists() else fetch_json(
        'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get', {'param':f'{symbol},day,{START},{END},500,qfq'})
    tx_path.write_text(json.dumps(tx,ensure_ascii=False,indent=1),encoding='utf-8')
    block = tx['data'][symbol]
    field = 'qfqday' if block.get('qfqday') else 'day'
    rows = block.get(field)
    if not rows:
        raise ValueError(f'{symbol}缺少日线')
    series = [{'date':r[0], 'close':float(r[2])} for r in rows if START <= r[0] <= END]
    try:
        em = json.loads(em_path.read_text(encoding='utf-8')) if em_path.exists() else fetch_json(
            'https://push2his.eastmoney.com/api/qt/stock/kline/get',
            {'secid':('1.' if symbol.startswith('sh') else '0.') + symbol[2:],
             'klt':101, 'fqt':1, 'beg':START.replace('-',''), 'end':END.replace('-',''),
             'fields1':'f1,f2,f3,f4,f5,f6', 'fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'})
        other = {r.split(',')[0]:float(r.split(',')[2]) for r in em['data']['klines']}
        em_path.write_text(json.dumps(em,ensure_ascii=False,indent=1),encoding='utf-8')
    except (OSError, KeyError, TypeError) as error:
        if field != 'qfqday':
            # 无分红和拆分时，未复权与复权价格相同；保存完整历史分红拆分表核对。
            evidence = raw / f'{symbol[2:]}_分红拆分.txt'
            if evidence.exists():
                body = evidence.read_text(encoding='utf-8')
            else:
                request = urllib.request.Request(f'https://fundf10.eastmoney.com/fhsp_{symbol[2:]}.html',headers={'User-Agent':'Mozilla/5.0'})
                with urllib.request.urlopen(request,timeout=20) as response:
                    body = response.read().decode('utf-8')
                evidence.write_text(body,encoding='utf-8')
            text = html.fromstring(body).text_content()
            if '暂无分红信息' not in text or '暂无拆分信息' not in text:
                raise ValueError(f'{symbol}day字段存在分红或拆分，需另取可靠复权价格') from error
        em, other = None, None
    assert len(series) >= 230 and len({r['date'] for r in series}) == len(series)
    assert all(math.isfinite(r['close']) and r['close'] > 0 for r in series)
    assert series[0]['date'] == START and series[-1]['date'] == END
    error = None
    if other is not None:
        assert set(other) == {r['date'] for r in series}, '跨来源日期不一致'
        error = max(abs(r['close'] - other[r['date']]) for r in series)
        assert error <= .00101, '前复权收盘价跨来源差异超过0.001元'
    return symbol[2:], {'name':name, 'symbol':symbol, 'requested_adjustment':'qfq', 'returned_field':field,
                       'series':series}, tx, em, {'rows':len(series), 'maximum_close_difference_yuan':error, 'returned_field':field,
                       'cross_source_status':'passed' if other is not None else 'unavailable',
                       'adjustment_basis':'qfqday' if field=='qfqday' else ('cross_source_qfq_verified' if other is not None else 'no_dividend_or_split_history_verified')}


def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(collect_one, ETFS.items()))
    DATA.mkdir(exist_ok=True)
    raw = DATA / '原始'
    raw.mkdir(exist_ok=True)
    snapshot, checks = {}, {}
    for code, item, tx, em, check in results:
        snapshot[code] = item
        checks[code] = check
        for provider, value in [('腾讯',tx),('东方财富',em)]:
            if value is not None:
                (raw / f'{code}_{provider}.json').write_text(json.dumps(value,ensure_ascii=False,indent=1),encoding='utf-8')
    calendar = [r['date'] for r in next(iter(snapshot.values()))['series']]
    assert all([r['date'] for r in item['series']] == calendar for item in snapshot.values())
    (DATA / 'ETF行情.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=1),encoding='utf-8')
    metadata = {'collection_client_date':'2026-10-05', 'start':START, 'end':END, 'entities':len(snapshot),
                'price_basis':'请求前复权的ETF市场收盘价；qfqday直接采用，day需跨源核对或验证无分红拆分；第二来源不可用如实记录',
                'sources':['https://gu.qq.com/','https://quote.eastmoney.com/center/gridlist.html#fund_etf'],
                'cross_checks':checks, 'calendar_rows':len(calendar)}
    (DATA / '采集元数据.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(metadata,ensure_ascii=True))


if __name__ == '__main__':
    main()
