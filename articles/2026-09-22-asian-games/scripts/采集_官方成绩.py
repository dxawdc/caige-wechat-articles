# -*- coding: utf-8 -*-
"""
2026 爱知·名古屋亚运会 官方成绩数据采集
数据源：OCA 官方成绩系统 Bornan WebResults
  https://back.results.asiangames2026.org/s/AG2026/{lang}/...
说明：响应体存在 charset 转换导致的畸形压缩流，需 utf8->latin1 回转后再 inflate。
"""
import csv
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request
import zlib
from datetime import date, timedelta

BASE = "https://back.results.asiangames2026.org"
CHAMP = "AG2026"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "数据")
os.makedirs(DATA, exist_ok=True)

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _inflate(b):
    if b[:2] == b"\x1f\x8b":
        return gzip.decompress(b)
    if b[:1] == b"\x78":
        return zlib.decompress(b)
    return zlib.decompress(b, -zlib.MAX_WBITS)


def api(path, lang="en", retries=3):
    """请求官方 API，自动处理畸形压缩流。"""
    url = f"{BASE}/s/{CHAMP}/{lang}{path}"
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip",
                "Origin": "https://results.asiangames2026.org",
                "Referer": "https://results.asiangames2026.org/"})
            with opener.open(req, timeout=30) as resp:
                raw = resp.read()
                if "gzip" in (resp.headers.get("Content-Encoding") or "").lower():
                    try:
                        raw = gzip.decompress(raw)
                    except Exception:  # noqa: BLE001
                        pass
            try:
                return json.loads(raw.decode("utf-8"))
            except Exception:  # noqa: BLE001
                fixed = _inflate(raw.decode("utf-8").encode("latin-1"))
                return json.loads(fixed.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last = e
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(1.5 * (i + 1))
    print(f"  ! 失败 {path}: {last}")
    return None


def dump(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_csv(name, rows, fields):
    with open(os.path.join(DATA, name), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


log = []

# ---------- 1. 代表团 ----------
orgs = api("/ALL/orgs/list") or []
dump("官方_代表团.json", orgs)
log.append(("代表团", len(orgs)))

# ---------- 2. 项目（大项+分项） ----------
discs = api("/ALL/disc/list") or []
dump("官方_项目.json", discs)
log.append(("项目/分项", len(discs)))

# ---------- 3. 奖牌榜 ----------
standings = api("/ALL/medals/standings") or []
rows = []
for s in standings:
    c = s.get("Count", {})
    rows.append({
        "排名": s.get("Rk"), "并列": s.get("RkEq"), "代表团": s.get("OrgDesc"),
        "代码": s.get("Org"),
        "金": c.get("ME_GOLD", {}).get("total", 0),
        "银": c.get("ME_SILVER", {}).get("total", 0),
        "铜": c.get("ME_BRONZE", {}).get("total", 0),
        "合计": c.get("total", {}).get("total", 0),
        "男金": c.get("ME_GOLD", {}).get("M", 0),
        "女金": c.get("ME_GOLD", {}).get("W", 0),
        "混合金": c.get("ME_GOLD", {}).get("X", 0),
    })
dump("官方_奖牌榜.json", standings)
write_csv("官方_奖牌榜.csv", rows,
          ["排名", "并列", "代表团", "代码", "金", "银", "铜", "合计", "男金", "女金", "混合金"])
log.append(("奖牌榜代表团数", len(rows)))

# ---------- 4. 奖牌明细（逐日聚合） ----------
days = [date(2026, 9, 19) + timedelta(days=i) for i in range(16)]  # 9/19 - 10/4
medals, day_stat = [], []
for d in days:
    ds = d.isoformat()
    items = api(f"/ALL/medals/daily/{ds}")
    if not items:
        continue
    for it in items:
        medals.append({
            "日期": ds,
            "奖牌": it.get("Medal"),
            "项目": it.get("DiscDesc"),
            "项目代码": it.get("Disc"),
            "小项": it.get("EventDesc"),
            "小项代码": it.get("Event"),
            "代表团": it.get("OrgDesc"),
            "代码": it.get("Org"),
            "姓名": it.get("Name"),
            "类型": it.get("Type"),
            "性别": it.get("Gender"),
            "出生日期": it.get("BirthDate", ""),
            "成员": " / ".join(m.get("Name", "") for m in (it.get("Members") or [])),
            "成员数": len(it.get("Members") or []),
            "时间": (it.get("DateRaw") or "")[:16],
        })
    day_stat.append((ds, len(items)))

fields = ["日期", "奖牌", "项目", "项目代码", "小项", "小项代码", "代表团", "代码",
          "姓名", "类型", "性别", "出生日期", "成员数", "成员", "时间"]
write_csv("官方_奖牌明细.csv", medals, fields)
log.append(("奖牌明细条数", len(medals)))
for ds, n in day_stat:
    log.append((f"  {ds}", n))

# ---------- 5. 多牌选手 ----------
multi = api("/ALL/medals/multi-medallists") or []
flat = []
for m in multi:
    for md in (m.get("Medals") or []):
        flat.append({
            "姓名": m.get("Name"), "简写": m.get("NameS"),
            "代表团代码": m.get("Org"), "金": m.get("ME_GOLD"), "银": m.get("ME_SILVER"),
            "铜": m.get("ME_BRONZE"), "合计": m.get("total"),
            "项目": md.get("Disc"), "小项": md.get("EventDesc"),
            "奖牌": md.get("Medal"),
        })
dump("官方_多牌选手.json", multi)
write_csv("官方_多牌选手明细.csv", flat,
          ["姓名", "简写", "代表团代码", "金", "银", "铜", "合计", "项目", "小项", "奖牌"])
log.append(("多牌选手人数", len(multi)))

# ---------- 6. 场馆 & 赛程矩阵 ----------
venues = api("/ALL/venues/list") or []
dump("官方_场馆.json", venues)
log.append(("场馆", len(venues)))
matrix = api("/ALL/schedule/matrix")
dump("官方_赛程矩阵.json", matrix)

# ---------- 7. 参赛名单接口探测 ----------
entry_probe = {}
for p in ["/ALL/entries/list", "/SWM/entries/list", "/ALL/participants/list",
          "/ALL/athletes", "/SWM/entries", "/ALL/medals/params"]:
    r = api(p)
    entry_probe[p] = ("list:%d" % len(r)) if isinstance(r, list) else (
        "dict:%s" % list(r.keys())[:8] if isinstance(r, dict) else "无")
dump("官方_参赛名单接口探测.json", entry_probe)

# ---------- 汇总 ----------
summary = {
    "采集时间": time.strftime("%Y-%m-%d %H:%M:%S"),
    "数据源": "OCA 官方成绩系统 Bornan WebResults (back.results.asiangames2026.org)",
    "赛事": "第20届亚运会 2026 爱知·名古屋（2026-09-19 至 2026-10-04）",
    "统计": dict(log),
    "参赛名单接口探测": entry_probe,
}
dump("官方_采集汇总.json", summary)

for k, v in log:
    print(f"{k}: {v}")
print("参赛名单接口探测:", entry_probe)
