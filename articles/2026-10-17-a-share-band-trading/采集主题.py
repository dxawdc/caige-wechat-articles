"""从中证指数官网采集25个主题指数日收盘（2014-12至今，含250日均线预热期），落盘为 数据/主题指数日线.json。"""
from pathlib import Path
import json
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '数据'
DATA.mkdir(exist_ok=True)
CUTOFF = '20261016'
API = 'https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode={code}&startDate=20141201&endDate={end}'
THEMES = {
    '人工智能': '931071', '5G通信': '931079', '半导体': 'H30184', '云计算': '930851', '消费电子': '931494',
    '机器人': 'H30590', '智能汽车': '930721', '军工': '399967', '卫星产业': '931594',
    '新能源': '399808', '光伏': '931151', '电池': '931719', '核电': '930642', '电网设备': '931994',
    '油气': 'H30198', '有色金属': '930708', '黄金采掘': '930619', '稀土': '930598',
    '银行': '399986', '证券': '399975',
    '主要消费': '000932', '白酒': '399997', '生物科技': '930743', '创新药': '931152', '医疗器械': 'H30217',
}


def fetch(code):
    url = API.format(code=code, end=CUTOFF)
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.csindex.com.cn/'})
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.load(r)
            assert d['code'] == '200' and d['data']
            return d['data']
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 + 2 * attempt)


def main():
    out = {}
    for name, code in THEMES.items():
        rows = fetch(code)
        assert all(r['indexCode'] == code for r in rows)
        # 接口会在起始日补一行（2014-12-01 为交易日，此处按日期去重即可）
        closes = {f"{r['tradeDate'][:4]}-{r['tradeDate'][4:6]}-{r['tradeDate'][6:]}": float(r['close'])
                  for r in rows if r.get('close') not in (None, '')}
        days = sorted(closes)
        out[name] = {'code': code, 'full_name': rows[0]['indexNameCnAll'], 'rows': [[d, closes[d]] for d in days]}
        print(f'{name:5s} {code} {days[0]} ~ {days[-1]} {len(days)}条', flush=True)
        time.sleep(0.8)
    ends = {v['rows'][-1][0] for v in out.values()}
    assert len(ends) == 1, ends
    payload = {'source': '中证指数有限公司官网 csindex.com.cn', 'cutoff': ends.pop(), 'series': out}
    (DATA / '主题指数日线.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    print('截止', payload['cutoff'])


if __name__ == '__main__':
    main()
