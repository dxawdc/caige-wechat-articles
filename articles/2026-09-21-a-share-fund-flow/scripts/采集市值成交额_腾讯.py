# -*- coding: utf-8 -*-
"""v1.0.0 | 2026-09-21 | 用腾讯行情批量补采市值与成交额。

背景：东方财富 clist 接口（f6 成交额 / f20 总市值 / f21 流通市值）当天被 IP 级限流，
      改由腾讯行情补齐。腾讯行情风控独立且宽松，单次可批量请求数十只。

数据源：https://qt.gtimg.cn/q=sh600000,sz000001,...   （GBK 编码）
字段索引（~ 分隔，共 88 段）：
  3  现价        37 成交额(万元)   38 换手率(%)
  44 流通市值(亿) 45 总市值(亿)
输出：市值成交额_腾讯.csv
  列：code,name,price,amount(元),turnover(%),float_cap(亿),mktcap(亿)
"""
from __future__ import annotations
import csv, time, urllib.request

SRC = "数据中心_当日个股.csv"
OUT = "市值成交额_腾讯.csv"
BATCH = 50
GAP = 0.35
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Referer": "https://gu.qq.com/",
}


def prefix(code: str) -> str:
    return ("sh" if code.startswith(("6", "9", "5")) else "sz") + code


def _num(f, i):
    try:
        v = float(f[i])
        return v
    except Exception:  # noqa: BLE001
        return None


def fetch_batch(codes: list, tries: int = 4) -> dict:
    url = "https://qt.gtimg.cn/q=" + ",".join(prefix(c) for c in codes)
    last = None
    for i in range(tries):
        try:
            raw = urllib.request.urlopen(
                urllib.request.Request(url, headers=HEADERS), timeout=15
            ).read().decode("gbk", "ignore")
            out = {}
            for line in raw.strip().split("\n"):
                if "=" not in line:
                    continue
                body = line.split("=", 1)[1].strip().strip(";").strip('"')
                f = body.split("~")
                if len(f) < 46:
                    continue
                aw = _num(f, 37)
                out[f[2]] = {
                    "name": f[1],
                    "price": _num(f, 3),
                    "amount": aw * 1e4 if aw is not None else None,   # 万元 → 元
                    "turnover": _num(f, 38),
                    "float_cap": _num(f, 44),                        # 亿元
                    "mktcap": _num(f, 45),                           # 亿元
                }
            return out
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}"
            time.sleep(1.0 + i * 0.8)
    raise RuntimeError(f"腾讯批量失败: {last}")


def main():
    with open(SRC, encoding="utf-8-sig") as f:
        codes = [r["SECURITY_CODE"].zfill(6) for r in csv.DictReader(f) if r.get("SECURITY_CODE")]
    codes = list(dict.fromkeys(codes))
    print(f"[tencent] 待采 {len(codes)} 只，分 { (len(codes)+BATCH-1)//BATCH } 批", flush=True)

    rows, miss = [], []
    for i in range(0, len(codes), BATCH):
        chunk = codes[i:i + BATCH]
        try:
            got = fetch_batch(chunk)
            for c in chunk:
                d = got.get(c)
                if d:
                    rows.append({"code": c, **d})
                else:
                    miss.append(c)
        except Exception as e:  # noqa: BLE001
            print(f"  批 {i//BATCH+1} FAIL {e}", flush=True)
            miss.extend(chunk)
        if (i // BATCH + 1) % 10 == 0:
            print(f"  进度 {i+len(chunk)}/{len(codes)}", flush=True)
        time.sleep(GAP)

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "name", "price", "amount",
                                          "turnover", "float_cap", "mktcap"])
        w.writeheader()
        w.writerows(rows)
    print(f"[done] {OUT} 共 {len(rows)} 条，未采到 {len(miss)} 只")


if __name__ == "__main__":
    main()
