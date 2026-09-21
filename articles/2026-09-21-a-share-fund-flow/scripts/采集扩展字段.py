# -*- coding: utf-8 -*-
"""v1.0.0 | 2026-09-20 | 补采全市场扩展字段：成交额、换手率、总市值、流通市值。

在原有资金流字段之外，补充：
- f6  成交额（元）
- f8  换手率（%）
- f20 总市值（元）
- f21 流通市值（元）

用于「市值分层资金流」「资金强度（净额÷成交额）」等分析。
输出：资金流向_全市场_扩展.csv
"""
from __future__ import annotations
import csv, json, time, urllib.request

# v1.1.0（2026-09-21）：协议可用性会随时间变化，当天实测 HTTPS 可用 / HTTP 超时，统一走 HTTPS。
BASE = "https://push2delay.eastmoney.com/api/qt/clist/get"
UT = "bd1d9ddb04089700cf9c27f6f7426281"
FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
FIELDS = "f12,f14,f2,f3,f6,f8,f20,f21,f62,f184,f66,f72,f78,f84"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
    "Accept": "*/*",
    "Referer": "https://data.eastmoney.com/",
}


def get_page(pn: int, pz: int = 100, tries: int = 6):
    url = (f"{BASE}?pn={pn}&pz={pz}&po=1&np=1&fltt=2&invt=2&fid=f62"
           f"&fs={FS}&fields={FIELDS}&ut={UT}")
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            raw = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
            return json.loads(raw)
        except Exception as e:
            if i == tries - 1:
                raise
            print(f"  [retry {i+1}] {type(e).__name__}: {e}")
            time.sleep(2 + i)
    return None


def main():
    pz = 500                  # 先要最大值，服务端若忽略则按实际返回条数自适应
    rows, pn, total = [], 1, None
    while True:
        j = get_page(pn, pz)
        d = (j or {}).get("data") or {}
        diff = d.get("diff") or []
        if not diff:
            break
        if total is None:
            total = d.get("total", 0)
            if len(diff) < min(pz, total or pz):
                pz = len(diff)
                print(f"[adapt] 服务端返回 {len(diff)} 条，单页容量调整为 {pz}", flush=True)
        rows.extend(diff)
        print(f"page {pn} 累计 {len(rows)}/{total}", flush=True)
        if len(rows) >= (total or 0):
            break
        pn += 1
        time.sleep(3.5)

    out = "资金流向_全市场_扩展.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "name", "price", "pct", "amount", "turnover",
                    "mktcap", "float_cap", "main_net", "main_pct",
                    "xl_net", "l_net", "m_net", "s_net"])
        for it in rows:
            w.writerow([it.get("f12"), it.get("f14"), it.get("f2"), it.get("f3"),
                        it.get("f6"), it.get("f8"), it.get("f20"), it.get("f21"),
                        it.get("f62"), it.get("f184"), it.get("f66"),
                        it.get("f72"), it.get("f78"), it.get("f84")])
    print(f"[done] {out}  共 {len(rows)} 条")


if __name__ == "__main__":
    main()
