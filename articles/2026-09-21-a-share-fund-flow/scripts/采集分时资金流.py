"""v1.1.0 | 2026-09-21 | 采集候选股的分钟级资金流K线（用于回放全天资金榜演变）。

候选集：按当日主力净额取流入Top50 + 流出Top30。
数据源：东方财富 push2delay fflow/kline（分钟级累计净额）。
字段：时间, 主力净额, 小单净额, 中单净额, 大单净额, 超大单净额（均为当日累计值，元）。

v1.1.0（2026-09-21）修复三处：
1. 单只最多尝试 2 次（原 6 次、退避最长 8s）——当天有个别次新股返回空，
   原策略会把整轮拖到十几分钟且没有任何进度输出；
2. 每只结果**即时落盘**到 分时缓存_候选股.json，中断后可续采，不再整轮重来；
3. 全程 flush=True，进度实时可见。

v1.2.0（2026-09-21 晚）：
4. 接口入口改为多域名/多协议候选轮换（见 BASES）。当天实测 push2delay/push2 的
   HTTPS 与 HTTP 交替可用，把入口写死必然整轮失败；82.push2 的 HTTP 是最后可用的。
"""
from __future__ import annotations
import argparse, csv, json, os, time, urllib.request

# v1.2.0：东财各域名/协议的可用性当天多次反转，写死单一入口必然失效。
# 这里按"2026-09-21 22:00 实测"的顺序做候选，逐次轮换重试。
BASES = [
    "http://82.push2.eastmoney.com/api/qt/stock/fflow/kline/get",   # 实测唯一返回 240 分钟
    "https://push2delay.eastmoney.com/api/qt/stock/fflow/kline/get",
    "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get",
    "http://push2delay.eastmoney.com/api/qt/stock/fflow/kline/get",
    "https://82.push2.eastmoney.com/api/qt/stock/fflow/kline/get",
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://data.eastmoney.com/zjlx/",
    "Connection": "keep-alive",
}
UT = "bd1d9ddb04089700cf9c27f6f7426281"
CACHE = "分时缓存_候选股.json"


def secid(code: str) -> str:
    # 6开头沪市=1.，其余（0/3开头深市）=0.
    return ("1." if code.startswith(("6", "9", "5")) else "0.") + code


def fetch_fflow(code: str, tries: int = len(BASES)) -> dict:
    tail = (f"?secid={secid(code)}&klt=1&fields1=f1,f2,f3,f7"
            f"&fields2=f51,f52,f53,f54,f55,f56&lmt=0&ut={UT}")
    last = None
    for i in range(tries):
        base = BASES[i % len(BASES)]
        try:
            req = urllib.request.Request(base + tail, headers=HEADERS)
            j = json.loads(urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore"))
            data = j.get("data") or {}
            kl = data.get("klines") or []
            if not kl:
                last = f"{base.split('/')[2]} klines为空"
                time.sleep(0.4)
                continue
            return data
        except Exception as e:  # noqa: BLE001
            code_ = getattr(e, "code", "")
            last = f"{base.split('/')[2]} {type(e).__name__}{code_}"
            time.sleep(0.4)
    raise RuntimeError(f"{code} 尝试{tries}次仍失败: {last}")


def _load_cache() -> dict:
    if os.path.exists(CACHE):
        try:
            with open(CACHE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return {}
    return {}


def main(csv_in: str, out_json: str, n_in: int = 50, n_out: int = 30):
    with open(csv_in, encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r["main_net"] not in ("-", "")]
    rows.sort(key=lambda r: float(r["main_net"]), reverse=True)
    cands = rows[:n_in] + rows[-n_out:]
    cache = _load_cache()
    print(f"[cands] 候选 {len(cands)} 只（流入Top{n_in} + 流出Top{n_out}）；缓存已有 "
          f"{len([1 for v in cache.values() if v.get('series')])} 只", flush=True)

    for i, r in enumerate(cands, 1):
        code, name = r["code"], r["name"]
        if (cache.get(code) or {}).get("series"):
            print(f"[{i}/{len(cands)}] {code} {name} 跳过（已缓存）", flush=True)
            continue
        try:
            data = fetch_fflow(code)
            cache[code] = {
                "name": name,
                "main_net_final": float(r["main_net"]),
                "series": [k.split(",") for k in data["klines"]],
            }
            print(f"[{i}/{len(cands)}] {code} {name} {len(data['klines'])}条", flush=True)
        except Exception as e:  # noqa: BLE001
            cache.setdefault(code, {})["error"] = str(e)[:120]
            print(f"[{i}/{len(cands)}] {code} {name} FAIL {str(e)[:80]}", flush=True)
        with open(CACHE, "w", encoding="utf-8") as f:          # 即时落盘，支持续采
            json.dump(cache, f, ensure_ascii=False)
        time.sleep(0.6)

    out = {k: v for k, v in cache.items() if v.get("series")}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    fails = [k for k, v in cache.items() if not v.get("series")]
    print(f"[done] {len(out)}/{len(cands)} 只写入 {out_json}" + (f"；失败 {fails}" if fails else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="资金流向_全市场.csv")
    ap.add_argument("--out", default="分时资金流_候选股.json")
    args = ap.parse_args()
    main(args.csv, args.out)
