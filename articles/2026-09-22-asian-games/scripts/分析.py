# -*- coding: utf-8 -*-
"""2026 爱知·名古屋亚运会 —— 六大主题数据分析。

输入：数据/ 目录下的官方采集结果
输出：分析/统计结果.json + 分析/*.csv（供绘图与报告使用）

六大主题：
  A 奖牌榜结构    B 各国优势项目图谱   C 中国代表团拆解
  D 选手画像      E 赛事节奏与场馆     F 参赛规模与产出效率
"""
import csv
import json
import os
from collections import Counter, defaultdict

from 映射 import org, org_code, disc, city, athlete, MEDAL_SHORT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "数据")
OUT = os.path.join(ROOT, "分析")
os.makedirs(OUT, exist_ok=True)

REF_DATE = "2026-09-22"  # 数据截止日（赛事第 4 日）

LOG = []


def log(*a):
    LOG.append(" ".join(str(x) for x in a))


def load_json(n):
    with open(os.path.join(D, n), encoding="utf-8") as f:
        return json.load(f)


def load_csv(n):
    with open(os.path.join(D, n), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(name, rows, fields):
    with open(os.path.join(OUT, name), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


# ================================================================ 载入
orgs = load_json("官方_代表团.json")
discs = load_json("官方_项目.json")
standings = load_json("官方_奖牌榜.json")
multi = load_json("官方_多牌选手.json")
medals = load_csv("官方_奖牌明细_全量.csv")
entry = load_json("官方_参赛名单.json")
venues = load_json("官方_场馆.json")
matrix = load_json("官方_赛程矩阵.json")
finals = load_json("官方_每日决赛日程.json")   # 小项级决赛日程（含 Medal 标记）
records = load_csv("官方_破纪录明细.csv")      # 官方破纪录明细

DISC_NAME = {d["Key"]: d["Desc"] for d in discs}
participants = entry["participants"]

# 唯一选手（Reg 去重）
uniq = {}
for p in participants:
    uniq.setdefault(p["Reg"], p)
athletes = list(uniq.values())
log("报名记录 %d 条 -> 唯一选手 %d 人" % (len(participants), len(athletes)))

R = {}

# ================================================================ A 奖牌榜结构
rows, tsum = [], Counter()
for s in standings:
    c = s["Count"]

    def g(kind, g=None):
        v = c.get(kind, {})
        return v.get(g, 0) if g else v.get("total", 0)

    code = s["Org"]
    rows.append({
        "排名": s["Rk"], "并列": s["RkEq"], "代码": code, "代表团": org(code),
        "金": g("ME_GOLD"), "银": g("ME_SILVER"), "铜": g("ME_BRONZE"),
        "合计": g("total"),
        "男金": g("ME_GOLD", "M"), "女金": g("ME_GOLD", "W"), "混合金": g("ME_GOLD", "X"),
        "男银": g("ME_SILVER", "M"), "女银": g("ME_SILVER", "W"), "混合银": g("ME_SILVER", "X"),
        "男铜": g("ME_BRONZE", "M"), "女铜": g("ME_BRONZE", "W"), "混合铜": g("ME_BRONZE", "X"),
        "男牌": c["total"]["M"], "女牌": c["total"]["W"], "混合牌": c["total"]["X"],
    })
    for k in ("金", "银", "铜", "合计", "男牌", "女牌", "混合牌"):
        tsum[k] += rows[-1][k]

rows.sort(key=lambda r: (int(r["排名"]), -r["合计"]))
save_csv("A_奖牌榜_含性别.csv", rows,
         ["排名", "并列", "代码", "代表团", "金", "银", "铜", "合计",
          "男金", "女金", "混合金", "男银", "女银", "混合银", "男铜", "女铜", "混合铜",
          "男牌", "女牌", "混合牌"])

n_org = len(orgs)
n_org_medal = len(rows)
gold_total = tsum["金"]

top5_gold = sum(r["金"] for r in rows[:5])
top10_gold = sum(r["金"] for r in rows[:10])
top5_tot = sum(r["合计"] for r in rows[:5])
top10_tot = sum(r["合计"] for r in rows[:10])


def gini(vals):
    """基尼系数（衡量奖牌分布不均程度，0=完全平均 1=完全集中）"""
    x = sorted(v for v in vals if v > 0)
    n = len(x)
    if n == 0:
        return 0.0
    s = sum(x)
    cum = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(x))
    return round(cum / (n * s), 4)


R["A_奖牌榜结构"] = {
    "口径": "OCA 官方成绩系统奖牌榜，截止 %s（赛事第 4 日）" % REF_DATE,
    "代表团总数": n_org,
    "已有奖牌代表团数": n_org_medal,
    "金牌总数": gold_total, "银牌总数": tsum["银"], "铜牌总数": tsum["铜"],
    "奖牌总数": tsum["合计"],
    "金银铜比例说明": "银牌少于铜牌属正常：拳击/柔道/空手道/台球等项目每个级别颁发 2 枚铜牌",
    "集中度": {
        "前5代表团金牌占比": round(top5_gold / gold_total * 100, 1),
        "前10代表团金牌占比": round(top10_gold / gold_total * 100, 1),
        "前5代表团奖牌占比": round(top5_tot / tsum["合计"] * 100, 1),
        "前10代表团奖牌占比": round(top10_tot / tsum["合计"] * 100, 1),
        "金牌基尼系数": gini([r["金"] for r in rows]),
        "奖牌基尼系数": gini([r["合计"] for r in rows]),
    },
    "性别结构": {
        "男牌": tsum["男牌"], "女牌": tsum["女牌"], "混合牌": tsum["混合牌"],
        "女牌占比": round(tsum["女牌"] / tsum["合计"] * 100, 1),
        "男牌占比": round(tsum["男牌"] / tsum["合计"] * 100, 1),
    },
    "前12": [{"名次": r["排名"], "代表团": r["代表团"], "金": r["金"], "银": r["银"],
              "铜": r["铜"], "合计": r["合计"], "男金": r["男金"], "女金": r["女金"],
              "混合金": r["混合金"]} for r in rows[:12]],
    "全部": [{"代表团": r["代表团"], "代码": r["代码"], "金": r["金"], "银": r["银"],
              "铜": r["铜"], "合计": r["合计"]} for r in rows],
    "男女金银铜拆分": [
        {"代表团": r["代表团"], "男": r["男牌"], "女": r["女牌"], "混合": r["混合牌"]}
        for r in rows[:14]],
}

# ================================================================ B 各国优势项目图谱
# 金牌矩阵：代表团 × 项目
gold_pairs = Counter()
medal_pairs = Counter()
all_pairs = Counter()
for r in medals:
    all_pairs[(r["代码"], r["项目代码"])] += 1
    medal_pairs[(r["代码"], r["项目代码"])] += 1
    if r["奖牌"] == "ME_GOLD":
        gold_pairs[(r["代码"], r["项目代码"])] += 1

# 各代表团的金牌项目结构与集中度
org_gold = defaultdict(Counter)
for (o, d), n in gold_pairs.items():
    org_gold[o][d] = n

conc = []
for o, cnts in org_gold.items():
    tot = sum(cnts.values())
    shares = [v / tot for v in cnts.values()]
    hhi = sum(s * s for s in shares)
    top_d, top_n = cnts.most_common(1)[0]
    conc.append({
        "代码": o, "代表团": org(o), "金牌": tot, "夺金项目数": len(cnts),
        "等效项目数": round(1 / hhi, 2),
        "最大单项目": disc(top_d), "最大单项目金牌": top_n,
        "最大单项目占比": round(top_n / tot * 100, 1),
        "集中度HHI": round(hhi, 3),
        "项目分布": "、".join("%s%d" % (disc(k), v) for k, v in cnts.most_common()),
    })
conc.sort(key=lambda x: (-x["金牌"], x["等效项目数"]))
save_csv("B_夺金结构集中度.csv", conc,
         ["代表团", "代码", "金牌", "夺金项目数", "等效项目数", "最大单项目",
          "最大单项目金牌", "最大单项目占比", "集中度HHI", "项目分布"])

# 金牌 × 代表团 矩阵（前 12 代表团 × 有金牌的项目）
top_orgs = [r["代码"] for r in rows[:12]]
disc_gold_total = Counter()
for (o, d), n in gold_pairs.items():
    disc_gold_total[d] += n
top_discs = [d for d, _ in disc_gold_total.most_common()]
mx_rows = []
for o in top_orgs:
    row = {"代表团": org(o), "代码": o, "金牌": sum(org_gold[o].values())}
    for d in top_discs:
        row[disc(d)] = org_gold[o].get(d, 0)
    mx_rows.append(row)
save_csv("B_金牌项目矩阵.csv", mx_rows,
         ["代表团", "代码", "金牌"] + [disc(d) for d in top_discs])

# 项目侧：各项目的金牌归属
disc_rows = []
for d, tot in disc_gold_total.most_common():
    owners = sorted([(o, n) for (o, dd), n in gold_pairs.items() if dd == d],
                    key=lambda a: -a[1])
    disc_rows.append({
        "项目代码": d, "项目": disc(d), "金牌数": tot,
        "参与代表团数": len({o for (o, dd) in all_pairs if dd == d}),
        "夺金代表团数": len(owners),
        "金牌归属": "、".join("%s%d" % (org(o), n) for o, n in owners),
        "头名": org(owners[0][0]) if owners else "",
        "头名金牌": owners[0][1] if owners else 0,
    })
save_csv("B_项目金牌归属.csv", disc_rows,
         ["项目", "项目代码", "金牌数", "参与代表团数", "夺金代表团数", "头名", "头名金牌", "金牌归属"])

R["B_各国优势项目图谱"] = {
    "口径": "基于奖牌明细 251 条（75 金 / 73 银 / 103 铜），截止 %s" % REF_DATE,
    "已产生金牌的项目数": len(disc_gold_total),
    "项目总数": len(discs),
    "矩阵": {"代表团": [org(o) for o in top_orgs],
             "项目": [disc(d) for d in top_discs],
             "值": [[org_gold[o].get(d, 0) for d in top_discs] for o in top_orgs]},
    "集中度": conc[:16],
    "项目金牌归属": [{"项目": d["项目"], "金牌数": d["金牌数"],
                       "夺金代表团数": d["夺金代表团数"],
                       "头名": d["头名"], "头名金牌": d["头名金牌"]} for d in disc_rows],
}

# ================================================================ C 中国代表团拆解
CHN = [r for r in medals if r["代码"] == "CHN"]
chn_gold = [r for r in CHN if r["奖牌"] == "ME_GOLD"]
chn_by_disc = Counter(r["项目代码"] for r in chn_gold)
chn_medal_by_disc = Counter(r["项目代码"] for r in CHN)
chn_by_gender = Counter(r["性别"] for r in chn_gold)
chn_medal_gender = Counter(r["性别"] for r in CHN)
chn_athletes = [a for a in athletes if a["Org"] == "CHN"]
chn_disc_cover = Counter(a["Disc"] for a in chn_athletes)
chn_stand = next(r for r in rows if r["代码"] == "CHN")
chn_multi = [m for m in multi if m["Org"] == "CHN"]
chn_multi.sort(key=lambda m: (-m["total"], -(m.get("ME_GOLD") or 0), m["Name"]))

R["C_中国代表团拆解"] = {
    "奖牌": {"金": chn_stand["金"], "银": chn_stand["银"], "铜": chn_stand["铜"],
              "合计": chn_stand["合计"], "名次": chn_stand["排名"]},
    "金牌项目数": len(chn_by_disc),
    "金牌项目分布": [{"项目": disc(k), "金牌": v,
                       "占中国金牌比": round(v / len(chn_gold) * 100, 1),
                       "占该项目全球金牌比": round(v / disc_gold_total[k] * 100, 1)}
                      for k, v in chn_by_disc.most_common()],
    "奖牌项目分布": [{"项目": disc(k), "奖牌": v} for k, v in chn_medal_by_disc.most_common()],
    "性别结构": {"金牌": dict(chn_by_gender), "奖牌": dict(chn_medal_gender)},
    "参赛规模": {
        "报名人数": len(chn_athletes),
        "覆盖项目数": len(chn_disc_cover),
        "人数最多项目": [{"项目": disc(k), "人数": v} for k, v in chn_disc_cover.most_common(8)],
        "每金所需参赛人数": round(len(chn_athletes) / chn_stand["金"], 1),
    },
    "游泳15金明细": [
        {"小项": r["小项"], "姓名": r["姓名"], "性别": r["性别"],
         "出生日期": r["出生日期"], "时间": r["时间"]}
        for r in chn_gold if r["项目代码"] == "SWM"],
    "全部金牌明细": [
        {"项目": disc(r["项目代码"]), "小项": r["小项"], "姓名": r["姓名"],
         "性别": r["性别"], "出生日期": r["出生日期"], "成员数": r["成员数"],
         "成员": r["成员"], "时间": r["时间"]} for r in chn_gold],
    "多牌选手": [{"姓名": m["Name"], "金": m.get("ME_GOLD"), "银": m.get("ME_SILVER"),
                   "铜": m.get("ME_BRONZE"), "合计": m["total"],
                   "项目": "、".join(sorted({disc(x["Disc"]) for x in m["Medals"]}))}
                  for m in chn_multi],
    "多牌选手人数": len(chn_multi),
}

# ================================================================ D 选手画像
gender_map = {"M": "男", "W": "女", "X": "混合", "O": "其他/公开"}
g_all = Counter(gender_map.get(a["Gender"], a["Gender"]) for a in athletes)
type_map = {"A": "运动员", "T": "团体项目成员", "D": "双打配对", "O": "官员"}
org_size = Counter(a["Org"] for a in athletes)
disc_size = Counter(a["Disc"] for a in athletes)
insc = Counter(len(a.get("Inscriptions") or []) for a in athletes)
cross = Counter(len([p for p in participants if p["Reg"] == a["Reg"]]) for a in athletes)

# 兼项（同一 Reg 出现在多个项目）
reg_disc = defaultdict(set)
for p in participants:
    reg_disc[p["Reg"]].add(p["Disc"])
cross_disc = [r for r, ds in reg_disc.items() if len(ds) > 1]

# 奖牌选手年龄
from datetime import date


def parse(d):
    try:
        y, m, dd = d.split("-")
        return date(int(y), int(m), int(dd))
    except Exception:  # noqa: BLE001
        return None


ref = parse(REF_DATE)
ages, age_rows = [], []
for r in medals:
    b = parse(r["出生日期"]) if r["出生日期"].strip() else None
    if not b:
        continue
    dt = parse(r["时间"][:10]) or ref
    age = (dt - b).days / 365.25
    ages.append(age)
    age_rows.append({"姓名": r["姓名"], "代表团": org(r["代码"]), "项目": disc(r["项目代码"]),
                      "小项": r["小项"], "奖牌": MEDAL_SHORT[r["奖牌"]],
                      "性别": r["性别"], "年龄": round(age, 1),
                      "出生日期": r["出生日期"]})
ages_sorted = sorted(ages)
n = len(ages_sorted)


def pct(p):
    return round(ages_sorted[min(n - 1, int(n * p))], 1)


age_rows.sort(key=lambda x: x["年龄"])
save_csv("D_奖牌选手年龄.csv", age_rows,
         ["姓名", "代表团", "项目", "小项", "奖牌", "性别", "年龄", "出生日期"])

# 分组统计：金牌 / 银牌 / 铜牌 年龄
by_medal = defaultdict(list)
by_type = defaultdict(list)
for r in medals:
    b = parse(r["出生日期"]) if r["出生日期"].strip() else None
    if not b:
        continue
    dt = parse(r["时间"][:10]) or ref
    by_medal[MEDAL_SHORT[r["奖牌"]]].append((dt - b).days / 365.25)
    by_type[r["项目代码"]].append((dt - b).days / 365.25)

gender_age = defaultdict(list)
for r in medals:
    b = parse(r["出生日期"]) if r["出生日期"].strip() else None
    if not b:
        continue
    dt = parse(r["时间"][:10]) or ref
    gender_age[gender_map.get(r["性别"], r["性别"])].append((dt - b).days / 365.25)

multi_sorted = sorted(multi, key=lambda m: (-m["total"], -(m.get("ME_GOLD") or 0), m["Name"]))
multi_ge2 = [m for m in multi if m["total"] >= 2]

R["D_选手画像"] = {
    "口径": "参赛名单 12,781 条报名记录（Reg 去重后 12,753 名唯一选手）；年龄仅覆盖有出生日期的 %d 条奖牌记录" % n,
    "规模": {
        "报名记录数": len(participants),
        "唯一选手数": len(athletes),
        "兼项选手数": len(cross_disc),
        "兼项选手": [{"姓名": uniq[r]["Name"], "代表团": org(uniq[r]["Org"]),
                       "项目": "、".join(disc(x) for x in sorted(reg_disc[r]))}
                      for r in cross_disc][:30],
        "性别分布": dict(g_all),
        "性别比例": "男 %.1f%% / 女 %.1f%%" % (g_all["男"] / len(athletes) * 100,
                                                g_all["女"] / len(athletes) * 100),
        "身份分布": dict(Counter(type_map.get(a["Type"], a["Type"]) for a in athletes)),
        "代表团规模前12": [{"代表团": org(o), "人数": c} for o, c in org_size.most_common(12)],
        "项目规模前12": [{"项目": disc(d), "人数": c} for d, c in disc_size.most_common(12)],
        "参赛人数最少代表团": [{"代表团": org(o), "人数": c} for o, c in org_size.most_common()[-6:]],
        "报名小项数分布": [{"报名小项数": k, "人数": v} for k, v in sorted(insc.items())],
        "人均报名小项数": round(sum(k * v for k, v in insc.items()) / len(athletes), 2),
        "兼项记录数分布": [{"同时参赛项目数": k, "人数": v} for k, v in sorted(cross.items())],
    },
    "年龄": {
        "样本量": n,
        "中位数": pct(0.5), "均值": round(sum(ages) / n, 1),
        "最小": round(ages_sorted[0], 1), "最大": round(ages_sorted[-1], 1),
        "P25": pct(0.25), "P75": pct(0.75), "P90": pct(0.90),
        "最年轻5人": age_rows[:5],
        "最年长5人": age_rows[-5:][::-1],
        "分奖牌颜色": [{"奖牌": k, "人数": len(v), "中位年龄": round(sorted(v)[len(v) // 2], 1),
                         "均值": round(sum(v) / len(v), 1)}
                        for k, v in sorted(by_medal.items())],
        "分性别": [{"性别": k, "人数": len(v), "中位年龄": round(sorted(v)[len(v) // 2], 1)}
                    for k, v in sorted(gender_age.items())],
        "分项目": [{"项目": disc(k), "人数": len(v), "中位年龄": round(sorted(v)[len(v) // 2], 1)}
                    for k, v in sorted(by_type.items(), key=lambda a: -len(a[1]))][:15],
    },
    "多牌选手": {
        "奖牌得主总数": len(multi),
        "个人奖牌条数": sum(m["total"] for m in multi),
        "多牌选手数(2枚及以上)": len(multi_ge2),
        "多牌选手占比": round(len(multi_ge2) / len(multi) * 100, 1),
        "说明": "奖牌明细 251 条为“项次”口径（团体项目计 1 条）；此处 430 人为个人口径（团体成员逐个展开），故人数多于条数", 
        "分布": dict(Counter(m["total"] for m in multi)),
        "前20": [{"姓名": m["Name"], "代表团": org(m["Org"]), "金": m.get("ME_GOLD"),
                   "银": m.get("ME_SILVER"), "铜": m.get("ME_BRONZE"), "合计": m["total"],
                   "项目": "、".join(sorted({disc(x["Disc"]) for x in m["Medals"]}))}
                  for m in multi_sorted[:20]],
        "各代表团人数": [{"代表团": org(o), "人数": c}
                          for o, c in Counter(m["Org"] for m in multi).most_common(10)],
    },
}

# ================================================================ E 赛事节奏与场馆
dates = matrix["dates"]

# matrix 每日值含义校验
val_counter = Counter()
for it in matrix["matrix"]:
    val_counter.update(it["Dates"])
log("赛程矩阵取值分布:", dict(val_counter))

day_compete = Counter()   # 当天有安排的项目数
day_medal = Counter()     # 当天有奖牌的项目数
for it in matrix["matrix"]:
    for i, v in enumerate(it["Dates"]):
        if v in ("0", "1"):
            day_compete[dates[i]] += 1
        if v == "1":
            day_medal[dates[i]] += 1

# 实际已产生金牌：按明细日期
actual_gold = Counter(r["时间"][:10] for r in medals if r["奖牌"] == "ME_GOLD" and r["时间"])
actual_medal = Counter(r["时间"][:10] for r in medals if r["时间"])

# 场馆
venue_city = Counter(v.get("City") for v in venues)
uniq_venue = {v["Key"]: v for v in venues}
venue_disc = defaultdict(set)
for v in venues:
    venue_disc[v["Key"]].update([v.get("Discipline")])

# 各项目比赛天数
disc_days = []
for it in matrix["matrix"]:
    k = it["Disc"]["Key"]
    c = sum(1 for v in it["Dates"] if v in ("0", "1"))
    md = sum(1 for v in it["Dates"] if v == "1")
    act = [dates[i] for i, v in enumerate(it["Dates"]) if v in ("0", "1")]
    md_days = [dates[i] for i, v in enumerate(it["Dates"]) if v == "1"]
    disc_days.append({"项目": disc(k), "代码": k, "比赛天数": c, "出奖牌天数": md,
                       "首日": act[0] if act else "", "末日": act[-1] if act else "",
                       "奖牌日": "、".join(md_days)})
disc_days.sort(key=lambda x: -x["比赛天数"])
save_csv("E_项目赛程天数.csv", disc_days,
         ["项目", "代码", "比赛天数", "出奖牌天数", "首日", "末日", "奖牌日"])

R["E_赛事节奏与场馆"] = {
    "口径": "赛程矩阵覆盖 %s 至 %s 共 %d 天；'1'=该日产生奖牌，'0'=比赛日无奖牌，'N'=无安排" % (
        dates[0], dates[-1], len(dates)),
    "赛程日期": dates,
    "每日有比赛的项目数": [{"日期": d, "项目数": day_compete.get(d, 0)} for d in dates],
    "每日产生奖牌的项目数": [{"日期": d, "项目数": day_medal.get(d, 0)} for d in dates],
    "每日实际金牌(已开赛部分)": [{"日期": d, "金牌": actual_gold.get(d, 0),
                                    "奖牌": actual_medal.get(d, 0)}
                                   for d in sorted(set(list(actual_gold) + list(actual_medal)))],
    "比赛总天数": len([d for d in dates if day_compete.get(d, 0) > 0]),
    "峰值日": max(((d, day_compete.get(d, 0)) for d in dates), key=lambda a: a[1]),
    "奖牌峰值日": max(((d, day_medal.get(d, 0)) for d in dates), key=lambda a: a[1]),
    "项目赛程天数前12": disc_days[:12],
    "项目赛程天数后8": disc_days[-8:],
    "场馆": {
        "记录数": len(venues), "唯一场馆数": len(uniq_venue),
        "城市数": len(venue_city),
        "城市分布": [{"城市": city(c), "场馆数": n} for c, n in venue_city.most_common()],
        "承办项目数": len({v.get("Discipline") for v in venues}),
    },
}

# ================================================================ F 参赛规模与产出效率
size_medal = defaultdict(Counter)
for r in medals:
    size_medal[r["代码"]][MEDAL_SHORT[r["奖牌"]]] += 1

eff = []
for o, size in org_size.items():
    m = size_medal.get(o, Counter())
    g, s, b = m.get("金", 0), m.get("银", 0), m.get("铜", 0)
    tot = g + s + b
    cover = len({a["Disc"] for a in athletes if a["Org"] == o})
    eff.append({
        "代码": o, "代表团": org(o), "参赛人数": size, "覆盖项目数": cover,
        "金": g, "银": s, "铜": b, "奖牌": tot,
        "人均奖牌(万分之)": round(tot / size * 10000, 1),
        "每金所需人数": round(size / g, 1) if g else "",
        "奖牌产出率%": round(tot / size * 100, 1),
        "上榜": "是" if tot else "否",
    })
eff.sort(key=lambda x: (-x["金"], -x["奖牌"], x["参赛人数"]))
save_csv("F_规模与产出.csv", eff,
         ["代表团", "代码", "参赛人数", "覆盖项目数", "金", "银", "铜", "奖牌",
          "人均奖牌(万分之)", "每金所需人数", "奖牌产出率%", "上榜"])

with_medal = [e for e in eff if e["奖牌"] > 0]
R["F_参赛规模与产出效率"] = {
    "口径": "参赛人数按姓名注册号去重；奖牌数来自官方奖牌榜",
    "整体": {
        "参赛人数最多": max(eff, key=lambda x: x["参赛人数"])["代表团"] if eff else "",
        "覆盖项目最全": [e["代表团"] for e in eff if e["覆盖项目数"] == len(discs)],
        "平均每队覆盖项目数": round(sum(e["覆盖项目数"] for e in eff) / len(eff), 1),
        "平均每金所需人数": round(sum(e["参赛人数"] for e in with_medal) /
                                  max(1, sum(e["金"] for e in with_medal)), 1),
        "说明": "“每金所需人数”与“人均奖牌”为投入产出代理指标，受项目结构影响，不能直接等价于竞技水平", 
        "仅参赛未夺牌代表团数": len([e for e in eff if e["奖牌"] == 0]),
        "夺牌代表团数": len(with_medal),
    },
    "参赛人数前15": eff[:15],
    "效率榜_每金人数最少": sorted([e for e in with_medal if e["金"] > 0 and e["参赛人数"] >= 30],
                                    key=lambda x: x["参赛人数"] / x["金"])[:12],
    "效率榜_人均奖牌": sorted(with_medal, key=lambda x: -x["人均奖牌(万分之)"])[:12],
    "规模大但产出低": sorted([e for e in eff if e["参赛人数"] >= 150 and e["人均奖牌(万分之)"] < 20],
                                key=lambda x: x["参赛人数"])[-10:][::-1],
    "全部": eff,
}

# ================================================================ G 全程金牌节奏（实际 + 预排）
# 官方日程接口在每条场次上带 Medal 标记（"1" = 金牌场次），据此算出每日预排金牌数，
# 累加即整届金牌总数；截止日之后为「预排值」，与「实际值」分开呈现。
# 口径校验：9/20 预排 31 = 实际 30（有日期）+ 1 枚未标日期的现代五项男子个人金；
#           9/21 预排 18 → 实发 19 金（男子 100 米蛙泳并列冠军）；9/22 预排 = 实际 25。
plan_total = sum(v["金牌小项数"] for v in finals.values())
gold_days = [d for d in sorted(finals) if finals[d]["金牌小项数"] > 0]
actual_gold = Counter(r["时间"][:10] for r in medals if r["奖牌"] == "ME_GOLD" and r["时间"])
undated_gold = sum(1 for r in medals if r["奖牌"] == "ME_GOLD" and not r["时间"])
gold_total_actual = sum(1 for r in medals if r["奖牌"] == "ME_GOLD")

timeline, cum_plan, cum_real = [], 0, 0
for d in gold_days:
    plan = finals[d]["金牌小项数"]
    real = actual_gold.get(d, 0) if d <= REF_DATE else None
    cum_plan += plan
    if real is not None:
        cum_real += real
    timeline.append({
        "日期": d, "预排金牌": plan,
        "实际金牌": real if real is not None else "",
        "出金项目数": finals[d]["出金项目数"],
        "累计预排": cum_plan,
        "累计实际": cum_real if real is not None else "",
        "状态": "已开赛" if real is not None else "预排",
    })
save_csv("G_每日金牌实际与预排.csv", timeline,
         ["日期", "预排金牌", "实际金牌", "出金项目数", "累计预排", "累计实际", "状态"])

# 各项目的出金日，用于说明「后面还有哪些大项没开赛」
disc_gold_days = defaultdict(list)
for d in gold_days:
    for k in finals[d]["出金项目"]:
        disc_gold_days[k].append(d)
not_started = sorted(
    [(disc(k), min(v), max(v), len(v)) for k, v in disc_gold_days.items() if min(v) > REF_DATE],
    key=lambda x: x[1])
finishing = sorted(
    [(disc(k), max(v)) for k, v in disc_gold_days.items()
     if min(v) <= REF_DATE <= max(v)], key=lambda x: x[1])

R["G_全程金牌节奏"] = {
    "口径": "预排金牌数 = 官方日程中 Medal 标记为金牌场次的唯一小项数；实际金牌数取自奖牌明细（按 DateRaw 归类）",
    "整届预排金牌总数": plan_total,
    "已产生金牌": gold_total_actual,
    "已完成比例%": round(gold_total_actual / plan_total * 100, 1),
    "官方未给日期的金牌": undated_gold,
    "已开赛比赛日": len([t for t in timeline if t["状态"] == "已开赛"]),
    "剩余比赛日": len([t for t in timeline if t["状态"] == "预排"]),
    "预排峰值日": max(timeline, key=lambda t: t["预排金牌"]),
    "剩余日预排前三": sorted([t for t in timeline if t["状态"] == "预排"],
                              key=lambda t: -t["预排金牌"])[:3],
    "每日节奏": timeline,
    "尚未开赛的项目": [{"项目": n, "首金日": a, "末金日": b, "出金天数": c}
                        for n, a, b, c in not_started],
    "进行中且将收尾的项目": [{"项目": n, "末金日": b} for n, b in finishing],
}

# ================================================================ H 破纪录
def record_level(name: str) -> str:
    low = (name or "").strip().lower()
    if not low:
        return "其他"
    if "world" in low:
        return "世界纪录"
    if low in ("gr",) or "games" in low:
        return "赛会纪录"
    if low in ("ar",) or "asian" in low:
        return "亚洲纪录"
    return "其他"


# 官方 records 接口返回的 Org / Disc 是英文全称，用官方清单建反向映射再转中文
ORG_BY_DESC = {o.get("Desc"): o["Key"] for o in orgs}
DISC_BY_EN = {d.get("Desc"): d["Key"] for d in discs}

for r in records:
    r["纪录级别"] = record_level(r["记录类型"])
    r["代码"] = ORG_BY_DESC.get(r["代码"], r["代码"])
    r["代表团"] = org(r["代码"])
    r["项目"] = disc(DISC_BY_EN.get(r["项目"], r["项目"]))
    r["项目代码"] = DISC_BY_EN.get(r["项目代码"], r["项目代码"])
    r["选手中文"] = athlete(r["选手"])

LEVEL_ORDER = ["世界纪录", "亚洲纪录", "赛会纪录", "其他"]
rec_by_level = Counter(r["纪录级别"] for r in records)
rec_by_org = Counter(r["代表团"] for r in records)
rec_by_disc = Counter(r["项目"] for r in records)
CODE_BY_NAME = {org(o["Key"]): o["Key"] for o in orgs}   # 中文名 -> 三字码

# 按「选手 + 小项 + 级别」去重，避免同一次成绩被多次计入
seen, athletes = set(), Counter()
for r in records:
    key = (r["选手"], r["小项"], r["纪录级别"])
    if key in seen:
        continue
    seen.add(key)
    athletes[r["选手"]] += 1

raw_by_athlete = Counter(r["选手"] for r in records)
team_records = [r for r in records if r["选手"] == "People's Republic of China"]

save_csv("H_破纪录明细.csv", records,
         ["时间", "项目", "小项", "轮次", "纪录级别", "记录类型", "成绩",
          "选手", "选手中文", "代码", "代表团", "地点", "小项代码", "项目代码"])

china_rec = [r for r in records if r["代码"] == "CHN"]
R["H_破纪录"] = {
    "口径": "官方 records-v2/broken 接口；同一次成绩可能同时刷新多个级别的纪录，故按「条」计数",
    "总数": len(records),
    "按级别": [{"级别": k, "条数": rec_by_level.get(k, 0)} for k in LEVEL_ORDER if rec_by_level.get(k)],
    "按代表团": [{"代表团": k, "代码": CODE_BY_NAME.get(k, k), "条数": n}
                  for k, n in rec_by_org.most_common()],
    "按项目": [{"项目": k, "条数": n} for k, n in rec_by_disc.most_common()],
    "中国条数": len(china_rec),
    "中国占全部纪录比%": round(len(china_rec) / len(records) * 100, 1),
    "世界纪录": [r for r in records if r["纪录级别"] == "世界纪录"],
    "选手榜_原始条数": [{"选手": k, "选手中文": athlete(k), "纪录条数": v}
                        for k, v in raw_by_athlete.most_common(10)],
    "选手榜_去重条数": [{"选手": k, "选手中文": athlete(k), "纪录条数": v}
                        for k, v in athletes.most_common(10)],
    "中国队团体纪录条数": len(team_records),
    "中国个人纪录条数": len(china_rec) - len(team_records),
    "全部纪录": records,
    "中国纪录": china_rec,
    "中国合计场次": len(records) - len(china_rec),
}

# ================================================================ 输出
R["元信息"] = {
    "赛事": "第20届亚洲运动会（2026 爱知·名古屋）",
    "赛期": "2026-09-19 至 2026-10-04",
    "数据截止": REF_DATE + "（赛事第 4 日，进行中）",
    "数据来源": "亚奥理事会（OCA）官方成绩系统 Bornan WebResults",
    "生成时间": "见运行时刻",
    "采集日志": LOG,
}

with open(os.path.join(OUT, "统计结果.json"), "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=2)

log("统计结果已写入 分析/统计结果.json")
with open(os.path.join(OUT, "_run_log.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(LOG))
print("\n".join(LOG))
