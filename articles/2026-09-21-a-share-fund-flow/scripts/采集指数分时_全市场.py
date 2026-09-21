# -*- coding: utf-8 -*-
"""v1.0.0 | 2026-09-21 | 采集沪市+深市指数分时资金流，拼出"全市场"口径。

背景：东财没有"全市场 5195 只直接聚合"的分钟级资金流接口，唯一的分钟级四档
资金流接口是 `fflow/kline`（单只 / 单指数）。它对指数返回"该市场成分股聚合"的
分时资金流，因此：

    全市场 ≈ 上证指数(沪市, 1.000001) + 深证综指(深市, 0.399106)

上证指数分时已在 `分时缓存_慢速.json` 里采到（全天主力 +30.6 亿），本脚本负责补采
深证综指，并把两者相加写入 `分时资金流_全市场.json`（供绘图脚本直接用）。

要点（沿用当晚踩坑总结）：
- `fflow/kline` 是"极小配额时间窗"接口，必须最小请求数（这里只有 1 个深市指数）；
- 多域名 × 协议轮换，被拒后彻底静默再试，不高频重试（重试会续期封禁）；
- 每只成功即落盘，断点可续。
"""
from __future__ import annotations
import argparse
import json
import os
import time
import urllib.request

UT = "bd1d9ddb04089700cf9c27f6f7426281"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://data.eastmoney.com/zjlx/dpzjlx.html",
    "Connection": "keep-alive",
}

# 沪市 / 深市指数 secid（东财 fflow 对指数返回该市场聚合资金流）
INDEX_SH = "1.000001"   # 上证指数（沪市）
INDEX_SZ = "0.399106"   # 深证综指（深市，覆盖深市全量，比深证成指更全）

CACHE = "分时缓存_指数.json"

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _combos():
    hosts = ["82.push2.eastmoney.com", "push2delay.eastmoney.com",
             "push2.eastmoney.com", "push2his.eastmoney.com"]
    out = []
    for sch in ("https", "http"):
        for h in hosts:
            out.append((sch, h))
    return out


def fetch_fflow(secid: str, tries: int = 3):
    combos = _combos()
    last = None
    for i in range(tries):
        sch, host = combos[i % len(combos)]
        url = (f"{sch}://{host}/api/qt/stock/fflow/kline/get?secid={secid}&klt=1"
               f"&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56&lmt=0&ut={UT}")
        try:
            raw = _OPENER.open(urllib.request.Request(url, headers=HEADERS),
                               timeout=12).read().decode("utf-8", "ignore")
            d = json.loads(raw).get("data") or {}
            kl = d.get("klines") or []
            if kl:
                return {"name": d.get("name"), "series": kl}
            last = "klines为空"
        except Exception as e:  # noqa: BLE001
            last = f"{sch}://{host}: {type(e).__name__}"
        time.sleep(1.5 + i)
    raise RuntimeError(f"{secid} 尝试{tries}次仍失败: {last}")


def load_cache() -> dict:
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(c: dict):
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait", type=int, default=0, help="开始前静默秒数")
    ap.add_argument("--gap", type=float, default=3.0, help="请求间隔")
    ap.add_argument("--cycles", type=int, default=10, help="失败后重试轮数")
    ap.add_argument("--retry-wait", type=int, default=300, help="整轮失败后静默秒数")
    args = ap.parse_args()

    if args.wait > 0:
        print(f"[wait] 静默 {args.wait}s，等待接口解除封禁…", flush=True)
        time.sleep(args.wait)

    cache = load_cache()
    need = [INDEX_SZ]  # 上证已在慢速缓存里，这里只补深市
    # 若上证也没采到，一起采
    if not cache.get(INDEX_SH, {}).get("series"):
        need = [INDEX_SH, INDEX_SZ]

    for cyc in range(1, args.cycles + 1):
        done = True
        for secid in need:
            if cache.get(secid, {}).get("series"):
                continue
            try:
                data = fetch_fflow(secid)
                cache[secid] = data
                save_cache(cache)
                n = len(data["series"])
                last = data["series"][-1]
                print(f"[ok] {secid} {data['name']} {n}分钟 末条主力="
                      f"{float(last[1])/1e8:+.1f}亿", flush=True)
            except RuntimeError as e:
                done = False
                print(f"[fail] {secid} {e}", flush=True)
                break  # 一个失败即停本轮，不浪费配额
            time.sleep(args.gap)

        if done:
            break
        print(f"[cool] 第{cyc}轮未完成，静默 {args.retry_wait}s 后重试…", flush=True)
        time.sleep(args.retry_wait)

    # 汇总：沪+深 = 全市场
    if cache.get(INDEX_SH, {}).get("series") and cache.get(INDEX_SZ, {}).get("series"):
        sh = cache[INDEX_SH]["series"]
        sz = cache[INDEX_SZ]["series"]
        times = [r[0] for r in sh]
        merged = []
        for i, t in enumerate(times):
            # 字段：[时间,主力,小单,中单,大单,超大单]
            merged.append([
                t,
                float(sh[i][1]) + float(sz[i][1]),
                float(sh[i][2]) + float(sz[i][2]),
                float(sh[i][3]) + float(sz[i][3]),
                float(sh[i][4]) + float(sz[i][4]),
                float(sh[i][5]) + float(sz[i][5]),
            ])
        out = {
            "meta": {"source": "东财 fflow/kline 指数聚合（沪+深）",
                     "index_sh": INDEX_SH, "index_sz": INDEX_SZ,
                     "note": "全市场口径 = 上证指数(沪市) + 深证综指(深市) 分时资金流相加"},
            "times": times,
            "main": [r[1] for r in merged],
            "small": [r[2] for r in merged],
            "mid": [r[3] for r in merged],
            "large": [r[4] for r in merged],
            "super": [r[5] for r in merged],
        }
        out_path = "分时资金流_全市场.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"[done] 全市场分时已写入 {out_path}：全天主力 "
              f"{float(merged[-1][1])/1e8:+.1f} 亿", flush=True)
    else:
        print("[warn] 未凑齐沪+深两个指数，无法生成全市场分时", flush=True)


if __name__ == "__main__":
    main()
