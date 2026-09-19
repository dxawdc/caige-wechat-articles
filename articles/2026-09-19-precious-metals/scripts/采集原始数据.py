# -*- coding: utf-8 -*-
"""采集贵金属价格原始数据（只读公开数据源）。

数据源：
1. 新浪国际期货日线（伦敦金现 XAU / 伦敦银现 XAG，2006 年至今）
2. 新浪国内期货日线（沪金主连 AU0 / 沪银主连 AG0）
3. 上海黄金交易所官方日行情（Au99.99 / Ag99.99，2016-12 至今）
4. 金投网品牌金价历史（集金号接口，周大福等 6 品牌，近两年日频）
5. tmini 品牌金价快照（当日，用于交叉校验）

输出：data/raw/*.json + 采集日志.txt
"""
from __future__ import annotations

import json
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "数据采集" / "采集日志.txt"

CST = timezone(timedelta(hours=8))
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Referer": "https://finance.sina.com.cn",
    "Accept": "*/*",
}
# 集金号接口校验来源页，缺失或错误会返回 HTTP 666
JIJINHAO_HEADERS = {**UA, "Referer": "https://quote.cngold.org/gjs/swhj_zdf.html"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# 品牌 -> (品牌页, {品种代码: 品种名})
BRANDS = {
    "周大福": ("https://quote.cngold.org/gjs/swhj_zdf.html",
             {"JO_42660": "黄金价格", "JO_56040": "饰品金价(内地)", "JO_56037": "金条金价(内地)"}),
    "周六福": ("https://quote.cngold.org/gjs/swhj_zlf.html",
             {"JO_42653": "黄金价格", "JO_42656": "金条价格"}),
    "老凤祥": ("https://quote.cngold.org/gjs/swhj_lfx.html",
             {"JO_42657": "黄金价格", "JO_42659": "足金价格", "JO_351184": "金条价格"}),
    "周生生": ("https://quote.cngold.org/gjs/swhj_zss.html",
             {"JO_42625": "黄金价格", "JO_56048": "饰品金价(内地)"}),
    "老庙黄金": ("https://quote.cngold.org/gjs/swhj_lm.html",
              {"JO_42634": "黄金价格", "JO_42636": "足金价格"}),
    "菜百": ("https://quote.cngold.org/gjs/swhj_cb.html",
            {"JO_42638": "黄金价格", "JO_42643": "足金价格"}),
}

HISTORY_START = datetime(2024, 9, 1, tzinfo=CST)   # 近两年起点（留余量）
SINA_GLOBAL = ("https://stock2.finance.sina.com.cn/futures/api/jsonp.php/"
               "var%20_=/GlobalFuturesService.getGlobalFuturesDailyKLine?symbol=")
SINA_INNER = ("https://stock2.finance.sina.com.cn/futures/api/jsonp.php/"
              "var%20_=/InnerFuturesNewService.getDailyKLine?symbol=")
SGE = "https://www.sge.com.cn/graph/Dailyhq?instid="
JIJINHAO = "https://api.jijinhao.com/quoteCenter/historys/query.htm?"

log_lines: list[str] = []


def log(message: str) -> None:
    stamp = datetime.now(CST).strftime("%H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    log_lines.append(line)


def fetch(url: str, attempts: int = 5, timeout: int = 45,
          headers: dict | None = None) -> str:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers=headers or UA)
            with urllib.request.urlopen(request, timeout=timeout, context=CTX) as response:
                return response.read().decode("utf-8", "replace")
        except Exception as error:  # noqa: BLE001
            last = error
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"fetch_failed: {url} :: {type(last).__name__}: {last}")


def jsonp(text: str) -> object:
    start = text.index("[") if "[" in text else text.index("{")
    end = max(text.rindex("]"), text.rindex("}"))
    return json.loads(text[start:end + 1])


def save(name: str, payload: object) -> Path:
    path = RAW / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def collect_sina(symbol: str, filename: str, label: str) -> object:
    endpoint = SINA_GLOBAL if symbol in ("XAU", "XAG") else SINA_INNER
    data = jsonp(fetch(endpoint + symbol))
    save(filename, data)
    first, last = data[0]["d"] if "d" in data[0] else data[0]["date"], data[-1].get("d") or data[-1]["date"]
    log(f"{label}: {len(data)} 条，{first} ~ {last}")
    return data


def collect_sge(instid: str, filename: str, label: str) -> object:
    data = json.loads(fetch(SGE + urllib.parse.quote(instid)))
    save(filename, data)
    rows = data.get("time", [])
    log(f"{label}: {len(rows)} 条，{rows[0][0]} ~ {rows[-1][0]}")
    return data


def collect_brand_history(code: str, label: str) -> list[dict]:
    """集金号历史接口按页取数（每页 500 条），直到覆盖近两年起点。"""
    rows: dict[int, dict] = {}
    page = 1
    while page <= 8:
        query = urllib.parse.urlencode({"codes": code, "style": "2",
                                        "currentPage": page, "pageSize": 500})
        text = fetch(JIJINHAO + query, headers=JIJINHAO_HEADERS)
        payload = json.loads(text[text.index("{"): text.rindex("}") + 1])
        series = payload.get("data", {}).get(code) or []
        if not series:
            break
        for item in series:
            rows[item["time"]] = item
        oldest = datetime.fromtimestamp(min(rows) / 1000, CST)
        log(f"  {label} 第{page}页 {len(series)} 条，最早 {oldest:%Y-%m-%d}")
        if oldest <= HISTORY_START:
            break
        page += 1
        time.sleep(0.6)
    return [rows[key] for key in sorted(rows)]


def main() -> None:
    log("=" * 60)
    log("开始采集贵金属价格原始数据")

    log("-- 国际现货金银（新浪国际期货）--")
    collect_sina("XAU", "国际现货黄金_XAU_日线.json", "伦敦金现 XAU")
    collect_sina("XAG", "国际现货白银_XAG_日线.json", "伦敦银现 XAG")

    log("-- 国内期货主力（新浪国内期货）--")
    collect_sina("AU0", "沪金主连_AU0_日线.json", "沪金主连 AU0")
    collect_sina("AG0", "沪银主连_AG0_日线.json", "沪银主连 AG0")

    log("-- 上海黄金交易所官方日行情 --")
    collect_sge("Au99.99", "上金所_Au9999_日行情.json", "上金所 Au99.99")
    collect_sge("Ag99.99", "上金所_Ag9999_日行情.json", "上金所 Ag99.99")

    log("-- 品牌金价历史（金投网采集、集金号接口）--")
    brand_payload: dict[str, dict] = {}
    for brand, (_page, products) in BRANDS.items():
        brand_payload[brand] = {}
        for code, product in products.items():
            log(f"{brand} / {product} ({code})")
            brand_payload[brand][product] = collect_brand_history(code, f"{brand}/{product}")
            time.sleep(0.6)
    save("品牌金价历史_近两年.json", brand_payload)

    log("-- 品牌金价当日快照（tmini，交叉校验用）--")
    snapshot = json.loads(fetch("https://tmini.net/api/gold-price?type=json"))
    save("品牌金价快照_tmini.json", snapshot)
    stores = {item["brand"]: item.get("price") for item in snapshot.get("stores", [])}
    log(f"tmini 店铺 {len(stores)} 家，周大福={stores.get('周大福')} 周六福={stores.get('周六福')}")

    (ROOT / "数据采集" / "采集日志.txt").write_text("\n".join(log_lines), encoding="utf-8")
    log("采集完成")


if __name__ == "__main__":
    main()
