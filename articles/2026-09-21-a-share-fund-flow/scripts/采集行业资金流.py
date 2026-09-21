"""v1.0.0 | 2026-09-21 | 采集东方财富行业板块资金流（用于「钱去了哪些行业」图）。

数据源：东方财富 push2delay clist/get，板块类型 m:90+t:2（行业板块，含一级与二级）。
输出：资金流向_行业_全量.csv
字段：code,name,main_net,main_pct,xl_net,l_net,m_net,s_net

v1.1.0（2026-09-21）：协议可用性会随时间变化，当天实测 HTTPS 可用 / HTTP 超时，统一走 HTTPS。
"""
from __future__ import annotations
import csv, json, time, urllib.request

BASE = "https://push2delay.eastmoney.com/api/qt/clist/get"
UT = "bd1d9ddb04089700cf9c27f6f7426281"
# m:90+t:2 = 行业板块（一级+二级），f:!50 去掉已退出的板块
FS = "m:90+t:2+f:!50"
FIELDS = "f12,f14,f62,f184,f66,f72,f78,f84"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://data.eastmoney.com/bkzj/",
    "Connection": "keep-alive",
}


def get_page(pn: int, pz: int = 100, tries: int = 6):
    url = (f"{BASE}?pn={pn}&pz={pz}&po=1&np=1&fltt=2&invt=2&fid=f62"
           f"&fs={FS}&fields={FIELDS}&ut={UT}")
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
            return json.loads(raw)
        except Exception as e:  # noqa: BLE001
            print(f"  [retry {i+1}] {type(e).__name__}: {e}", flush=True)
            time.sleep(2 + i)
    raise RuntimeError(f"第{pn}页拉取失败")


def main():
    pz = 500                  # 先要最大值，服务端若忽略则按实际返回条数自适应
    rows, pn, total = [], 1, None
    while True:
        d = (get_page(pn, pz) or {}).get("data") or {}
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

    out = "资金流向_行业_全量.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "name", "main_net", "main_pct",
                    "xl_net", "l_net", "m_net", "s_net"])
        for it in rows:
            w.writerow([it.get("f12"), it.get("f14"), it.get("f62"), it.get("f184"),
                        it.get("f66"), it.get("f72"), it.get("f78"), it.get("f84")])
    print(f"[done] {out} 共 {len(rows)} 个板块")


if __name__ == "__main__":
    main()
