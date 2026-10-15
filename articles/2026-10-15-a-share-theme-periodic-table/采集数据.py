"""从中证指数官网采集25个主题指数日收盘（2016年至今），落盘为 数据/主题指数日线.json。

选取有2016年以来完整历史的中证主题指数，覆盖科技、高端制造、新能源与电力、资源、金融、消费医药6个大类。
"""
from pathlib import Path
from datetime import date
import json
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '数据'
DATA.mkdir(exist_ok=True)
API = 'https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode={code}&startDate=20160101&endDate={end}'
# 展示名: (中证代码, 对应东财主题)
THEMES = {
    '人工智能': ('931071', 'AI 算力'), '5G通信': ('931079', 'CPO'), '半导体': ('H30184', '半导体'),
    '云计算': ('930851', '云计算/数据中心'), '卫星产业': ('931594', '商业航天/卫星'), '机器人': ('H30590', '机器人'),
    '智能汽车': ('930721', '自动驾驶'), '核电': ('930642', '核电'), '电网设备': ('931994', '电网'),
    '军工': ('399967', '军工'), '新能源': ('399808', '新能源'), '光伏': ('931151', '光伏'),
    '电池': ('931719', '锂电池'), '油气': ('H30198', '石油/天然气'), '有色金属': ('930708', '铜/有色'),
    '黄金采掘': ('930619', '黄金'), '银行': ('399986', '银行金融'), '证券': ('399975', '银行金融'),
    '生物科技': ('930743', '生物医疗'), '主要消费': ('000932', '消费'), '稀土': ('930598', '稀土永磁'),
    '创新药': ('931152', '创新药'), '消费电子': ('931494', '消费电子'), '医疗器械': ('H30217', '医疗器械'),
    '白酒': ('399997', '消费'),
}


def fetch(code):
    url = API.format(code=code, end=date.today().strftime('%Y%m%d'))
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
    for name, (code, em) in THEMES.items():
        rows = fetch(code)
        assert all(r['indexCode'] == code for r in rows)
        closes = {}
        for r in rows:
            # 接口会在起始日补一行（2016-01-01为休市日），剔除
            if r.get('close') not in (None, '') and r['tradeDate'] != '20160101':
                closes[f"{r['tradeDate'][:4]}-{r['tradeDate'][4:6]}-{r['tradeDate'][6:]}"] = float(r['close'])
        days = sorted(closes)
        out[name] = {'code': code, 'full_name': rows[0]['indexNameCnAll'], 'eastmoney_theme': em,
                     'rows': [[d, closes[d]] for d in days]}
        print(f"{name:5s} {code} {rows[0]['indexNameCnAll']:14s} {days[0]} ~ {days[-1]} {len(days)}条", flush=True)
        time.sleep(0.8)
    # 年度周期表以2016年最后一个交易日为基准，所有指数必须覆盖
    late = [n for n, v in out.items() if v['rows'][0][0] > '2016-12-30']
    assert not late, late
    ends = {v['rows'][-1][0] for v in out.values()}
    assert len(ends) == 1, ends
    payload = {'source': '中证指数有限公司官网 csindex.com.cn', 'cutoff': ends.pop(), 'series': out}
    (DATA / '主题指数日线.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    print('截止', payload['cutoff'])


if __name__ == '__main__':
    main()
