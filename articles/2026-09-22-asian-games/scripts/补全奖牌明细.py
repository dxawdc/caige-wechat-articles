# -*- coding: utf-8 -*-
"""用「按代表团」接口补全奖牌明细，并与逐日口径交叉复核。"""
import csv
import gzip
import json
import os
import time
import urllib.request
import zlib

BASE = "https://back.results.asiangames2026.org"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "数据")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _inflate(b):
    if b[:2] == b"\x1f\x8b":
        return gzip.decompress(b)
    if b[:1] == b"\x78":
        return zlib.decompress(b)
    return zlib.decompress(b, -zlib.MAX_WBITS)


def api(path):
    req = urllib.request.Request(BASE + "/s/AG2026/en" + path, headers={
        "User-Agent": UA, "Accept": "application/json, text/plain, */*",
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
        return json.loads(_inflate(raw.decode("utf-8").encode("latin-1")).decode("utf-8"))


orgs = json.load(open(os.path.join(DATA, "官方_代表团.json"), encoding="utf-8"))
all_medals = []
for o in orgs:
    code = o["Key"]
    data = api(f"/ALL/medals/org/{code}")
    if not data:
        continue
    for it in data:
        all_medals.append({
            "代表团": it.get("OrgDesc"), "代码": it.get("Org"),
            "奖牌": it.get("Medal"), "项目": it.get("DiscDesc"), "项目代码": it.get("Disc"),
            "小项": it.get("EventDesc"), "小项代码": it.get("Event"),
            "姓名": it.get("Name"), "类型": it.get("Type"), "性别": it.get("Gender"),
            "出生日期": it.get("BirthDate", ""), "Bib": it.get("Bib", ""),
            "成员数": len(it.get("Members") or []),
            "成员": " / ".join(m.get("Name", "") for m in (it.get("Members") or [])),
            "时间": (it.get("DateRaw") or "")[:16],
        })
    time.sleep(0.2)

fields = ["代表团", "代码", "奖牌", "项目", "项目代码", "小项", "小项代码", "姓名",
          "类型", "性别", "出生日期", "Bib", "成员数", "成员", "时间"]
with open(os.path.join(DATA, "官方_奖牌明细_全量.csv"), "w", encoding="utf-8-sig",
          newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in all_medals:
        w.writerow(r)

# 复核
from collections import Counter
cnt = Counter((r["代码"], r["奖牌"]) for r in all_medals)
print("全量明细条数:", len(all_medals))
print("奖牌类型:", dict(Counter(r["奖牌"] for r in all_medals)))
with open(os.path.join(DATA, "官方_奖牌榜.csv"), encoding="utf-8-sig") as f:
    st = list(csv.DictReader(f))
bad = 0
for r in st:
    for medal, col in (("ME_GOLD", "金"), ("ME_SILVER", "银"), ("ME_BRONZE", "铜")):
        a, b = int(r[col]), cnt.get((r["代码"], medal), 0)
        if a != b:
            print(f"  差异 {r['代表团']} {col}: 榜单{a} 明细{b}")
            bad += 1
print("差异条目数:", bad)
print("明细日期范围:", min(r["时间"][:10] for r in all_medals if r["时间"]),
      "~", max(r["时间"][:10] for r in all_medals if r["时间"]))
print("涉及项目数:", len({r["项目"] for r in all_medals}))
print("涉及代表团数:", len({r["代表团"] for r in all_medals}))
