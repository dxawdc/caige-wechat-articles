# -*- coding: utf-8 -*-
"""v2.0.0 | 2026-09-21 | 采集一级行业资金流（改用 fflow/kline 接口）。

背景：行业板块的 clist 接口当天被 IP 级限流（RemoteDisconnected）；
      fflow/kline 对行业指数（secid=90.BKxxxx）同样返回当日 5 档累计净额，
      且风控独立、实测可用。31 个一级行业 → 仅 31 次请求，代价极低。

klines 末条格式：
  时间, 主力净额, 小单净额, 中单净额, 大单净额, 超大单净额   （当日累计，元）
  其中 主力 = 大单 + 超大单（已验证恒等）

板块代码来源：一级行业代码表.csv（首次运行自动从旧的板块全量文件抽取，之后固定）。
输出：资金流向_行业_全量.csv（列与 v1 一致，供绘图脚本无缝使用）
"""
from __future__ import annotations
import csv, json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OLD_CSV = os.path.join(HERE, "资金流向_行业_全量.csv")
MAP_CSV = os.path.join(HERE, "一级行业代码表.csv")
OUT_CSV = os.path.join(HERE, "资金流向_行业_全量.csv")

L1 = ["农林牧渔", "基础化工", "钢铁", "有色金属", "电子", "家用电器", "食品饮料",
      "纺织服饰", "轻工制造", "医药生物", "公用事业", "交通运输", "房地产",
      "商贸零售", "社会服务", "综合", "建筑材料", "建筑装饰", "电力设备",
      "机械设备", "国防军工", "汽车", "计算机", "传媒", "通信", "银行", "非银金融",
      "环保", "煤炭", "石油石化", "美容护理"]

BASE = "https://push2delay.eastmoney.com/api/qt/stock/fflow/kline/get"
UT = "bd1d9ddb04089700cf9c27f6f7426281"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://data.eastmoney.com/bkzj/",
    "Connection": "keep-alive",
}


def load_or_build_map() -> dict:
    """name -> BK 代码。优先读映射表，缺失时从旧的板块全量文件抽取并落盘。"""
    if os.path.exists(MAP_CSV):
        with open(MAP_CSV, encoding="utf-8-sig") as f:
            m = {r["name"]: r["code"] for r in csv.DictReader(f) if r["name"] in L1}
        if len(m) >= 25:
            return m
    m = {}
    if os.path.exists(OLD_CSV):
        with open(OLD_CSV, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                n = (r.get("name") or "").strip().rstrip("－-— ")
                c = (r.get("code") or "").strip()
                if n in L1 and c.startswith("BK"):
                    m[n] = c
        with open(MAP_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["name", "code"])
            for n, c in sorted(m.items()):
                w.writerow([n, c])
        print(f"[map] 从旧板块文件抽取一级行业代码 {len(m)} 个 → {os.path.basename(MAP_CSV)}")
    return m


def fetch_industry(bk: str, tries: int = 8) -> dict:
    url = (f"{BASE}?secid=90.{bk}&klt=1&fields1=f1,f2,f3,f7"
           f"&fields2=f51,f52,f53,f54,f55,f56&lmt=0&ut={UT}")
    last = None
    for i in range(tries):
        try:
            raw = urllib.request.urlopen(
                urllib.request.Request(url, headers=HEADERS), timeout=20
            ).read().decode("utf-8", "ignore")
            d = (json.loads(raw).get("data") or {})
            kl = d.get("klines") or []
            if not kl:
                last = "klines为空"
                time.sleep(1.2)
                continue
            v = kl[-1].split(",")          # 时间,主力,小单,中单,大单,超大单
            return {
                "name": d.get("name"), "trade_time": v[0],
                "main_net": float(v[1]), "s_net": float(v[2]),
                "m_net": float(v[3]), "l_net": float(v[4]), "xl_net": float(v[5]),
            }
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}"
            time.sleep(min(1.0 + i * 0.4, 3.5))
    raise RuntimeError(f"{bk} 重试{tries}次仍失败: {last}")


def main():
    m = load_or_build_map()
    if not m:
        raise SystemExit("未能获得一级行业代码映射，请检查旧的 资金流向_行业_全量.csv")
    print(f"[industry] 一级行业 {len(m)} 个，逐个拉取当日净额", flush=True)

    rows, miss = [], []
    for i, (name, bk) in enumerate(sorted(m.items()), 1):
        try:
            d = fetch_industry(bk)
            rows.append({
                "code": bk, "name": d["name"] or name,
                "main_net": d["main_net"], "main_pct": "",
                "xl_net": d["xl_net"], "l_net": d["l_net"],
                "m_net": d["m_net"], "s_net": d["s_net"],
            })
            print(f"[{i}/{len(m)}] {name:6} {d['main_net']/1e8:+8.1f}亿  @{d['trade_time']}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(m)}] {name:6} FAIL {e}", flush=True)
            miss.append(name)
        time.sleep(0.6)

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "name", "main_net", "main_pct",
                                          "xl_net", "l_net", "m_net", "s_net"])
        w.writeheader()
        w.writerows(rows)
    print(f"[done] {OUT_CSV} 共 {len(rows)} 个行业；未采到 {len(miss)} 个 {miss}")


if __name__ == "__main__":
    main()
