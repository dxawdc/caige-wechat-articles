"""采集沪深融资汇总与沪深300日线，原始响应落盘，正常 TLS 验证。"""
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
import json
import time
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '数据'
DATA.mkdir(exist_ok=True)


def fetch(url, params=None, referer=None):
    if params:
        url += '?' + urllib.parse.urlencode(params)
    headers = {'User-Agent': 'Mozilla/5.0'}
    if referer:
        headers['Referer'] = referer
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
                return json.load(response)
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def margin(code):
    params = {'reportName': 'RPTA_WEB_RZRQ_LSSH', 'columns': 'ALL', 'source': 'WEB',
              'sortColumns': 'DIM_DATE', 'sortTypes': '-1', 'pageSize': 500, 'pageNumber': 1,
              'filter': '(SCDM=' + code + ")(DIM_DATE<='2026-09-30')"}
    result = fetch('https://datacenter-web.eastmoney.com/api/data/v1/get', params)
    assert result.get('success') and len(result['result']['data']) >= 350
    return result


def write(name, value):
    (DATA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    jobs = [('沪市融资汇总.json', lambda: margin('007')),
            ('深市融资汇总.json', lambda: margin('001')),
            ('沪深300日线.json', lambda: fetch('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get', {'param': 'sh000300,day,,,500,qfq'}, 'https://gu.qq.com/'))]
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda item: (item[0], item[1]()), jobs))
    for name, value in results:
        write(name, value)
    # 沪市偿还额采用交易所历史汇总；深市做最新共同日期抽样核对。
    checks = {}
    latest = min(datetime.fromisoformat(value['result']['data'][0]['DIM_DATE']).date() for name, value in results if '融资汇总' in name)
    official_jobs = [('上交所融资汇总.json', 'https://query.sse.com.cn/marketdata/tradedata/queryMargin.do',
                      {'isPagination': 'true', 'beginDate': '20250901', 'endDate': '20260930', 'tabType': '', 'stockCode': '', 'pageHelp.pageSize': 1000, 'pageHelp.pageNo': 1}, 'https://www.sse.com.cn/'),
                     ('深交所汇总抽样.json', 'https://www.szse.cn/api/report/ShowReport/data',
                      {'SHOWTYPE': 'JSON', 'CATALOGID': '1837_xxpl', 'txtDate': latest.isoformat(), 'tab1PAGENO': 1}, 'https://www.szse.cn/disclosure/margin/margin/index.html'),
                     ('深交所9月30日汇总.json', 'https://www.szse.cn/api/report/ShowReport/data',
                      {'SHOWTYPE': 'JSON', 'CATALOGID': '1837_xxpl', 'txtDate': '2026-09-30', 'tab1PAGENO': 1}, 'https://www.szse.cn/disclosure/margin/margin/index.html')]
    def official(item):
        name, url, params, referer = item
        try:
            value = fetch(url, params, referer)
            write(name, value)
            return name, {'status': 'fetched'}
        except Exception as error:
            return name, {'status': 'unavailable', 'type': type(error).__name__}
    with ThreadPoolExecutor(max_workers=2) as pool:
        checks = dict(pool.map(official, official_jobs))
    metadata = {'collected_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),
                'margin_source': 'https://data.eastmoney.com/rzrq/',
                'margin_report': 'RPTA_WEB_RZRQ_LSSH', 'margin_unit': '人民币元',
                'sh_repayment_source': '上交所融资融券汇总；沪市偿还额使用rzche字段',
                'information_cutoff': '2026-09-30',
                'scope': '沪市与深市融资融券标的汇总，含股票和符合条件的基金；不含京市',
                'index_source': '腾讯证券日线接口', 'index': '沪深300价格指数，代码000300',
                'official_fetch': checks}
    write('采集元数据.json', metadata)
    print(json.dumps({'status': 'collected', 'official': checks}, ensure_ascii=True))


if __name__ == '__main__':
    main()
