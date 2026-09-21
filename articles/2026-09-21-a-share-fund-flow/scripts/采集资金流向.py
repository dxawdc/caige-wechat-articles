"""v1.2.0 | 2026-09-21 | 采集沪深A股全市场主力资金流数据（四档口径）。

数据源：东方财富 push2 公开接口（clist/get 按主力净额排序分页拉取全市场）。
字段含义：
  f12 代码  f14 名称  f2 最新价  f3 涨跌幅%
  f62 主力净流入额(元)  f184 主力净流入占比%
  f66 超大单净额  f72 大单净额  f78 中单净额  f84 小单净额

v1.2.0 三条经验（2026-09-21 实测）：
1. **协议会变**：此前 HTTP 可用、HTTPS 被断连；今天反转为 HTTPS 可用、HTTP 超时。
   因此不再写死协议，改为 (scheme × host) 组合轮换。
2. 多域名轮换：push2delay / push2 / 82.push2 任一可用即可，单域名连发更易被掐。
3. 断点续传：每页成功即写 `_pages_cache.json`，中断后重跑直接跳过已采页。

注意：clist 是本组接口里风控最紧的一个（曾出现连续 0.8s 间隔拉到第 14 页即被断连）。
      若整轮失败，可改用 `数据中心_当日个股.csv`（datacenter-web 报表，风控独立且宽松）
      或 `fflow/kline`（分时接口，风控独立）作为替代数据源。
"""
from __future__ import annotations
import argparse, csv, json, os, time, urllib.request
from datetime import datetime

HOSTS = [
    "push2delay.eastmoney.com",
    "push2.eastmoney.com",
    "82.push2.eastmoney.com",
]
SCHEMES = ["https", "http"]          # 逐组合轮换，谁通用谁
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://data.eastmoney.com/zjlx/",
    "Connection": "keep-alive",
}
UT = "bd1d9ddb04089700cf9c27f6f7426281"
# 沪深A股：m:0+t:6(深主板) m:0+t:80(创业板) m:1+t:2(沪主板) m:1+t:23(科创板)
FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
FIELDS = "f12,f14,f2,f3,f62,f184,f66,f72,f78,f84"
PAGE_SIZE = 100
PAGE_GAP = 1.0                       # 页间间隔（秒）
CACHE = "_pages_cache.json"


def _combos():
    """(scheme, host) 轮换序列：先 https 全域名，再 http 全域名。"""
    return [(s, h) for s in SCHEMES for h in HOSTS]


def _get(url: str, timeout: int = 20) -> str:
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=HEADERS), timeout=timeout
    ).read().decode("utf-8", "ignore")


def fetch_page(pn: int, pz: int = PAGE_SIZE, tries: int = 16) -> dict:
    """(协议×域名) 轮换 + 递增退避。返回 data 字段。"""
    combos = _combos()
    last = None
    for i in range(tries):
        sch, host = combos[i % len(combos)]
        url = (f"{sch}://{host}/api/qt/clist/get?pn={pn}&pz={pz}&po=1&np=1&fltt=2"
               f"&invt=2&fid=f62&fs={FS}&fields={FIELDS}&ut={UT}")
        try:
            raw = _get(url)
            j = json.loads(raw)
            if j.get("data") is None:
                last = f"{sch}://{host} data为空"
                time.sleep(1.0)
                continue
            return j["data"]
        except Exception as e:  # noqa: BLE001
            last = f"{sch}://{host}: {type(e).__name__}"
            time.sleep(min(0.8 + i * 0.25, 3.0))
    raise RuntimeError(f"第{pn}页重试{tries}次仍失败: {last}")


def probe_page_size(tries: int = 3) -> int:
    """探测单页容量上限，返回可用的最大 pz；越少页数=越少请求=越低限流风险。"""
    for pz in (500, 300, 200, 100):
        try:
            d = fetch_page(1, pz=pz, tries=tries)
            n = len(d.get("diff") or [])
            total = d.get("total") or 0
            if n >= min(pz, total):
                print(f"[probe] 单页容量 {pz} 可用（返回 {n} 条 / 共 {total}）", flush=True)
                return pz
        except Exception as e:  # noqa: BLE001
            print(f"[probe] pz={pz} 不可用（{type(e).__name__}）", flush=True)
        time.sleep(0.8)
    return PAGE_SIZE


def load_cache() -> dict:
    if os.path.exists(CACHE):
        try:
            with open(CACHE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save_cache(cache: dict):
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def fetch_trade_date(tries: int = 8) -> str:
    """取上证指数日K 的最后一根，作为本次快照对应的交易日（周末/假日采集时尤其需要）。"""
    combos = _combos()
    for i in range(tries):
        sch, host = combos[i % len(combos)]
        url = (f"{sch}://{host}/api/qt/stock/kline/get?secid=1.000001&klt=101&fqt=1"
               f"&lmt=1&end=20500101&fields1=f1,f2,f3&fields2=f51,f53&ut={UT}")
        try:
            kl = (json.loads(_get(url, timeout=15)).get("data") or {}).get("klines") or []
            if kl:
                return kl[-1].split(",")[0]
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1.2)
    return ""


def collect(out_csv: str, out_json: str):
    cache = load_cache()
    first = cache.get("1")
    if first is None:
        pz = probe_page_size()
        first = fetch_page(1, pz=pz)
        cache["_pz"] = pz
        cache["1"] = first
        save_cache(cache)
    pz = int(cache.get("_pz") or PAGE_SIZE)
    total = first["total"]
    pages = (total + pz - 1) // pz
    done = len([k for k in cache if k.isdigit()])
    print(f"[collect] 全市场共 {total} 只 / {pages} 页（每页 {pz}）；缓存已有 {done} 页", flush=True)

    for pn in range(1, pages + 1):
        key = str(pn)
        if key in cache:
            continue
        cache[key] = fetch_page(pn, pz=pz)
        save_cache(cache)
        print(f"[collect] 进度 {pn}/{pages}", flush=True)
        time.sleep(PAGE_GAP)

    rows = []
    for pn in range(1, pages + 1):
        for it in (cache.get(str(pn)) or {}).get("diff") or []:
            rows.append({
                "code": it.get("f12", ""),
                "name": it.get("f14", ""),
                "price": it.get("f2"),
                "pct": it.get("f3"),
                "main_net": it.get("f62"),          # 主力净额(元)
                "main_pct": it.get("f184"),         # 主力净流入占比%
                "xl_net": it.get("f66"),            # 超大单净额
                "l_net": it.get("f72"),             # 大单净额
                "m_net": it.get("f78"),             # 中单净额
                "s_net": it.get("f84"),             # 小单净额
            })

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    td = fetch_trade_date()
    meta = {
        "source": "东方财富 push2 clist/get",
        "trade_date": td,
        "fetched_at": stamp,
        "total": len(rows),
        "fields": {
            "main_net": "主力净流入额(元)", "main_pct": "主力净流入占比%",
            "xl_net": "超大单净额", "l_net": "大单净额",
            "m_net": "中单净额", "s_net": "小单净额",
        },
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "rows": rows}, f, ensure_ascii=False, indent=1)
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[done] 写入 {out_csv} / {out_json}，共 {len(rows)} 条，交易日 {td}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-csv", default="资金流向_全市场.csv")
    ap.add_argument("--out-json", default="资金流向_全市场.json")
    ap.add_argument("--reset", action="store_true", help="清空分页缓存重新采集")
    args = ap.parse_args()
    if args.reset and os.path.exists(CACHE):
        os.remove(CACHE)
    collect(args.out_csv, args.out_json)
