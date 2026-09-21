# -*- coding: utf-8 -*-
"""v1.0.0 | 2026-09-21 | 慢速分批采集分时资金流（应对东财 fflow 接口的超紧配额）。

背景（当日实测规律）：
  该接口不是"速率封禁"，而是**配额极小的时间窗封禁**——
  - 21:40 前后连续 31 个请求（31 个行业）全部成功；
  - 随后 80 只连发 → 立刻全 502；
  - 静默约 2 分钟后单个请求又能通过；
  - 再一次 80 只连发 → 又全断。
说明：窗口内可承受约 30 个请求，超出即封，封禁期约数分钟到数十分钟。

策略：
  1. 把请求数砍到最少（默认 12 流入 + 12 流出 + 指数，共 25 个）；
  2. 请求间留 gap 秒（默认 6s），避免速率触发；
  3. 任一请求失败即**停止本轮**（不浪费额度），静默 retry-wait 秒后从断点续采；
  4. 每只即时落盘，中断可续，最多 cycles 轮。

用法：
  python 采集分时_慢速分批.py                    # 立刻开始
  python 采集分时_慢速分批.py --wait 1500        # 先静默 25 分钟再开始
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import time
import urllib.request

BASES = [
    "http://82.push2.eastmoney.com/api/qt/stock/fflow/kline/get",
    "https://push2delay.eastmoney.com/api/qt/stock/fflow/kline/get",
    "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get",
]
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://data.eastmoney.com/zjlx/",
    "Connection": "keep-alive",
}
UT = "bd1d9ddb04089700cf9c27f6f7426281"
CACHE = "分时缓存_慢速.json"
# 上证指数：用于"全天资金节奏"图，单个请求即可拿到全市场级的分钟累计净额
INDEXES = [("1.000001", "上证指数")]


def secid(code: str) -> str:
    return ("1." if code.startswith(("6", "9", "5")) else "0.") + code


def fetch(sid: str, base: str) -> dict:
    url = (f"{base}?secid={sid}&klt=1&fields1=f1,f2,f3,f7"
           f"&fields2=f51,f52,f53,f54,f55,f56&lmt=0&ut={UT}")
    req = urllib.request.Request(url, headers=HEADERS)
    j = json.loads(urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore"))
    d = j.get("data") or {}
    if not (d.get("klines") or []):
        raise RuntimeError("klines为空")
    return d


def load_cache() -> dict:
    if os.path.exists(CACHE):
        try:
            with open(CACHE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return {}
    return {}


def save(cache: dict):
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="资金流向_全市场.csv")
    ap.add_argument("--top-in", type=int, default=12)
    ap.add_argument("--top-out", type=int, default=12)
    ap.add_argument("--gap", type=float, default=6.0, help="请求间隔秒")
    ap.add_argument("--wait", type=float, default=0, help="开始前静默秒数")
    ap.add_argument("--retry-wait", type=float, default=600, help="本轮失败后静默秒数")
    ap.add_argument("--cycles", type=int, default=8)
    args = ap.parse_args()

    with open(args.csv, encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r["main_net"] not in ("-", "")]
    rows.sort(key=lambda r: float(r["main_net"]), reverse=True)
    picks = rows[:args.top_in] + rows[-args.top_out:]

    targets = [(secid(r["code"]), r["name"]) for r in picks] + INDEXES
    cache = load_cache()
    cache = {k: v for k, v in cache.items() if v.get("series")}   # 丢掉历史失败记录

    if args.wait > 0:
        print(f"[wait] 静默 {args.wait:.0f}s 后开始（避开封禁窗口）", flush=True)
        time.sleep(args.wait)

    print(f"[plan] 目标 {len(targets)} 个请求 = 流入Top{args.top_in} + 流出Top{args.top_out}"
          f" + {len(INDEXES)} 指数；间隔 {args.gap}s", flush=True)

    for cyc in range(1, args.cycles + 1):
        todo = [(s, n) for s, n in targets if s not in cache]
        if not todo:
            print("[done] 全部完成", flush=True)
            break
        print(f"[cycle {cyc}] 待采 {len(todo)} 个，开始 @{time.strftime('%H:%M:%S')}", flush=True)
        blocked = False
        for i, (sid, nm) in enumerate(todo, 1):
            ok = False
            for base in BASES:
                try:
                    d = fetch(sid, base)
                    cache[sid] = {"name": d.get("name") or nm,
                                  "series": [k.split(",") for k in d["klines"]]}
                    save(cache)
                    print(f"  [{i}/{len(todo)}] {sid:10} {cache[sid]['name']:8} "
                          f"{len(d['klines'])}条  via {base.split('/')[2]}", flush=True)
                    ok = True
                    break
                except Exception as e:  # noqa: BLE001
                    print(f"  [{i}/{len(todo)}] {sid:10} {base.split('/')[2]} "
                          f"{type(e).__name__}{getattr(e,'code','')}", flush=True)
            if not ok:
                blocked = True
                break
            time.sleep(args.gap)
        if blocked:
            left = len([1 for s, n in targets if s not in cache])
            print(f"[cycle {cyc}] 遇阻中断，剩 {left} 个；静默 {args.retry_wait:.0f}s "
                  f"后重试 @{time.strftime('%H:%M:%S')}", flush=True)
            time.sleep(args.retry_wait)

    got = len([1 for s, n in targets if s in cache])
    print(f"[result] {got}/{len(targets)} 成功 @{time.strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
