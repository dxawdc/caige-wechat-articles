# -*- coding: utf-8 -*-
"""采集16只ETF前复权日线，输出绘图脚本所需的原始K线。
python 采集ETF行情.py          完整采集成功后更新数据/etf_K线.json
python 采集ETF行情.py --check  只采集核验，与现有快照比较；保留当前绘图数据
"""
import argparse
import json
import math
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
ETFS = {
    "sh510300": "沪深300ETF", "sh510500": "中证500ETF",
    "sz159915": "创业板ETF", "sh588000": "科创50ETF",
    "sh510050": "上证50ETF", "sz159845": "中证1000ETF",
    "sh512880": "证券ETF", "sh512480": "半导体ETF",
    "sh512010": "医药ETF", "sz159928": "消费ETF",
    "sz159516": "半导体设备ETF", "sh515790": "光伏ETF",
    "sh512170": "医疗ETF", "sh512690": "酒ETF",
    "sz159819": "人工智能ETF", "sh516160": "新能源ETF",
}


def fetch_kline(symbol):
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param={symbol},day,,,120,qfq"
    )
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://gu.qq.com/",
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    # 统一请求qfq；实测部分ETF返回day，记录实际字段，不凭请求参数推断。
    content = payload.get("data", {}).get(symbol, {})
    field = "qfqday" if content.get("qfqday") else "day"
    candles = content.get(field)
    if not candles:
        raise ValueError(f"{symbol}缺少日线")
    series = [{
        "date": r[0], "open": float(r[1]), "close": float(r[2]),
        "high": float(r[3]), "low": float(r[4]), "vol": float(r[5]),
    } for r in candles]
    series.sort(key=lambda r: r["date"])
    if len(series) < 21 or len({r["date"] for r in series}) != len(series):
        raise ValueError(f"{symbol}历史不足或日期重复")
    for r in series:
        if any(not math.isfinite(r[k]) for k in ("open", "close", "high", "low", "vol")):
            raise ValueError(f"{symbol}存在无效值")
        if min(r[k] for k in ("open", "close", "high", "low")) <= 0 or r["vol"] < 0:
            raise ValueError(f"{symbol}价格或成交量无效")
    return series, field


def collect():
    result = {}
    for symbol, name in ETFS.items():
        for attempt in range(3):
            try:
                series, field = fetch_kline(symbol)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)
        result[symbol[2:]] = {"name": name, "series": series,
                              "requested_adjustment": "qfq", "returned_field": field}
        print(f"{symbol} {name}: {len(series)}条，最新{series[-1]['date']}，字段{field}")
        time.sleep(.2)
    baseline = [r["date"] for r in result["510300"]["series"][-21:]]
    if any([r["date"] for r in f["series"][-21:]] != baseline for f in result.values()):
        raise ValueError("ETF交易日期未对齐，请检查停牌或缺失记录")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = collect()
    target = BASE / "数据" / "etf_K线.json"
    if args.check:
        old = json.loads(target.read_text(encoding="utf-8"))
        matches = {c: old.get(c, {}).get("series") == f["series"] for c, f in data.items()}
        report = {"status": "passed", "provider": "腾讯证券日线（请求qfq）", "entities": len(data),
                  "as_of": data["510300"]["series"][-1]["date"], "snapshot_price_volume_matches": matches,
                  "all_snapshot_series_match": all(matches.values()),
                  "rows": {c: len(f["series"]) for c, f in data.items()},
                  "returned_fields": {c: f["returned_field"] for c, f in data.items()}}
        (BASE / "验收_数据采集.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("采集核验通过；当前行情快照保持原样。")
        return
    target.parent.mkdir(exist_ok=True)
    staging = target.with_suffix(".tmp")
    staging.write_text(json.dumps(data, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8")
    staging.replace(target)
    print(f"已保存 {len(data)} 只ETF到 {target.name}")


if __name__ == "__main__":
    main()
