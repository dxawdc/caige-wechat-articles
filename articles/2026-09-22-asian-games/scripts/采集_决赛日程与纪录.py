# -*- coding: utf-8 -*-
"""采集：① 全程 25 天的小项级决赛日程（用于每日金牌「实际 + 预排」）② 各项目破纪录明细。

为什么需要这个脚本：
    奖牌榜只告诉已经发出去的牌，看不出「后面还剩多少」。官方日程接口 /ALL/schedule/day/{date}
    在每条场次上带 Medal 标记（1 = 金牌场次），因此可以算出每一天预排多少枚金牌，
    并据此得到整届的金牌总数——截止日之后的日期就成了可展示的「预排值」。

口径校验（已实测）：
    2026-09-20 预排 31 场 → 实际 30 枚（有日期）+ 1 枚未标日期的现代五项男子个人金 = 31；
    2026-09-21 预排 18 场 → 实际 19 枚金（男子 100 米蛙泳出现并列冠军，18 场发出 19 金）；
    2026-09-22 预排 25 场 → 实际 25 枚金。
    三处差异都能被「并列冠军」与「DateRaw 缺失」解释，未发现口径漏洞。

输出：
    数据/官方_每日决赛日程.json    每日金牌小项数、出金项目数、出金项目分布
    数据/官方_破纪录.json          按项目返回的原始破纪录数据
    数据/官方_破纪录明细.csv       展开后的逐条记录（含选手、代表团、成绩、纪录类别）
"""
from __future__ import annotations

import csv
import gzip
import json
import os
import time
import urllib.request
import zlib
from collections import Counter, defaultdict

API = "https://back.results.asiangames2026.org/s/AG2026/en"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Encoding": "gzip",
    "Origin": "https://results.asiangames2026.org",
    "Referer": "https://results.asiangames2026.org/",
}
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "数据")

DATES = (["2026-09-%02d" % d for d in range(10, 31)]
         + ["2026-10-%02d" % d for d in range(1, 5)])


def decode(raw: bytes):
    """响应体可能是明文 JSON、纯 gzip，或「被 charset 破坏的 zlib 流」。"""
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return json.loads(zlib.decompress(raw.decode("utf-8").encode("latin-1")).decode("utf-8"))


def fetch(path: str, tries: int = 3):
    last = None
    for _ in range(tries):
        try:
            request = urllib.request.Request(API + path, headers=HEADERS)
            with OPENER.open(request, timeout=30) as response:
                return decode(response.read())
        except Exception as error:          # 网络抖动重试，不改行为
            last = error
            time.sleep(1.5)
    raise last


# ---------------------------------------------------------------- ① 每日决赛日程
daily = {}
for date in DATES:
    day = fetch("/ALL/schedule/day/%s" % date)
    golds = [u for u in day if str(u.get("Medal")) == "1"]
    by_disc = Counter(u["Disc"] for u in golds)
    daily[date] = {
        "条目数": len(day),
        "金牌小项数": len({(u["Disc"], u["Event"]) for u in golds}),
        "金牌场次数": len(golds),
        "铜牌场次数": sum(1 for u in day if str(u.get("Medal")) == "2"),
        "出金项目数": len(by_disc),
        "出金项目": dict(sorted(by_disc.items(), key=lambda kv: -kv[1])),
    }
    print("  %s 条目 %4d | 金牌小项 %3d" % (date, len(day), daily[date]["金牌小项数"]))

with open(os.path.join(DATA, "官方_每日决赛日程.json"), "w", encoding="utf-8") as f:
    json.dump(daily, f, ensure_ascii=False, indent=1)
print("[①] %d 天；整届预排金牌 %d 枚"
      % (len(daily), sum(v["金牌小项数"] for v in daily.values())))

# ---------------------------------------------------------------- ② 破纪录
with open(os.path.join(DATA, "官方_项目.json"), encoding="utf-8") as f:
    discs = json.load(f)
with open(os.path.join(DATA, "官方_代表团.json"), encoding="utf-8") as f:
    orgs = json.load(f)
ORG_NAME = {o["Key"]: o.get("Desc") for o in orgs}
DISC_NAME = {d["Key"]: d.get("Desc") for d in discs}

records = {}
for key in ["ALL"] + [d["Key"] for d in discs if d.get("HasRecords")]:
    block = fetch("/%s/records-v2/broken" % key)
    if block.get("records"):
        records[key] = block
        print("  [命中] %-4s %d 条" % (key, len(block["records"])))

with open(os.path.join(DATA, "官方_破纪录.json"), "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=1)

# 展平成明细：只保留真正填了选手姓名的记录（未开赛项目会返回空占位）
rows = []
for key, block in records.items():
    for event in block["records"]:
        for record in event.get("Records") or []:
            if not (record.get("Name") or "").strip():
                continue
            rows.append({
                "项目": DISC_NAME.get(key, key), "项目代码": key,
                "小项": event.get("EvtDesc") or "", "小项代码": event.get("EvtKey") or "",
                "轮次": event.get("TypeDesc") or event.get("Type") or "",
                "记录类型": record.get("Indicator") or record.get("Indicator1") or "",
                "成绩": record.get("Result") or "",
                "选手": record.get("Name") or "", "代码": record.get("Org") or "",
                "代表团": ORG_NAME.get(record.get("Org")) or record.get("OrgDesc") or "",
                "时间": (record.get("DateTimeRaw") or "").strip(),
                "地点": (record.get("Loc") or "").strip(),
            })
rows.sort(key=lambda r: (r["时间"], r["项目"], r["小项"]))
with open(os.path.join(DATA, "官方_破纪录明细.csv"), "w",
          encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print("[②] 破纪录明细 %d 条 | 按代表团 %s"
      % (len(rows), dict(Counter(r["代表团"] for r in rows))))
