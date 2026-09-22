# -*- coding: utf-8 -*-
"""2026 爱知·名古屋亚运会 —— 图表绘制（输出到 图表/*.png）。

读取 分析/统计结果.json 与 分析/*.csv，产出适合公众号使用的中文图表。
"""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

from 映射 import (C_BRONZE, C_GOLD, C_SILVER, GRID, PALETTE, TEXT,
                  apply_style, disc, save)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "分析")
R = json.load(open(os.path.join(A, "统计结果.json"), encoding="utf-8"))
apply_style()

MADE = []


def out(fig, name):
    p = save(fig, name)
    MADE.append(os.path.basename(p))
    return p


def head(fig, main, sub=None, y=0.985, gap=0.022, main_size=18, sub_size=10.5):
    """画标题与副标题，返回建议的 subplots top 值（避免标题压住坐标区）。"""
    H = fig.get_figheight()
    fig.text(0.02, y, main, fontsize=main_size, fontweight="bold", color=TEXT,
             ha="left", va="top")
    top = y - (main_size * 1.32 / 72) / H - 0.008
    if sub:
        fig.text(0.02, top, sub, fontsize=sub_size, color="#6B7A90",
                 ha="left", va="top")
        top -= (sub_size * 1.45 / 72) / H
    return top - gap


def note(fig, text, y=0.014):
    fig.text(0.02, y, text, fontsize=9, color="#8A97A8", ha="left", va="bottom")


def flat(ax):
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)


# ============================================================ 01 奖牌榜前12
d = R["A_奖牌榜结构"]["前12"]
teams = [x["代表团"] for x in d][::-1]
g = [x["金"] for x in d][::-1]
s = [x["银"] for x in d][::-1]
b = [x["铜"] for x in d][::-1]
yy = np.arange(len(teams))
fig, ax = plt.subplots(figsize=(9.2, 6.4))
ax.barh(yy, g, 0.66, color=C_GOLD, label="金牌", zorder=3)
ax.barh(yy, s, 0.66, left=g, color=C_SILVER, label="银牌", zorder=3)
ax.barh(yy, b, 0.66, left=np.array(g) + np.array(s), color=C_BRONZE, label="铜牌", zorder=3)
for i, (a, c, e) in enumerate(zip(g, s, b)):
    ax.text(a + c + e + 0.8, i, str(a + c + e), va="center", fontsize=10.5,
            fontweight="bold", color=TEXT)
ax.set_yticks(yy)
ax.set_yticklabels(teams, fontsize=11.5)
ax.set_xlim(0, 60)
ax.set_xlabel("奖牌数（枚）")
ax.grid(axis="x", color=GRID, zorder=0)
ax.grid(axis="y", visible=False)
ax.tick_params(length=0)
ax.legend(loc="lower right")
top = head(fig, "第20届亚运会奖牌榜 · 前12名",
           "截至 2026-09-22（赛事第 4 日）；数字为奖牌合计")
fig.subplots_adjust(top=top, left=0.16, right=0.97, bottom=0.1)
out(fig, "01_奖牌榜前12.png")

# ============================================================ 02 中日韩对比
top3 = R["A_奖牌榜结构"]["前12"][:3]
labels = [t["代表团"] for t in top3]
x = np.arange(3)
fig, axes = plt.subplots(1, 3, figsize=(11.8, 4.8))
w = 0.26
for k, (col, cname, color) in enumerate([("金", "金牌", C_GOLD), ("银", "银牌", C_SILVER),
                                          ("铜", "铜牌", C_BRONZE)]):
    vals = [t[col] for t in top3]
    bars = axes[0].bar(x + (k - 1) * w, vals, w, color=color, label=cname, zorder=3)
    for bar, v in zip(bars, vals):
        axes[0].text(bar.get_x() + bar.get_width() / 2, v + 0.5, str(v), ha="center",
                     fontsize=10, fontweight="bold", color=TEXT)
axes[0].set_xticks(x)
axes[0].set_xticklabels(labels)
axes[0].set_title("金 / 银 / 铜", fontsize=12.5)
axes[0].set_ylim(0, 37)
axes[0].legend(loc="upper right", fontsize=9.5)
flat(axes[0])

mw = [[t["男金"] for t in top3], [t["女金"] for t in top3], [t["混合金"] for t in top3]]
bot = np.zeros(3)
for row, cname, color in zip(mw, ["男子金牌", "女子金牌", "混合金牌"],
                             ["#2F6FED", "#C8102E", "#8B5CF6"]):
    axes[1].bar(x, row, 0.5, bottom=bot, color=color, label=cname, zorder=3)
    for i, v in enumerate(row):
        if v:
            axes[1].text(i, bot[i] + v / 2, str(v), ha="center", va="center",
                         fontsize=10, color="white", fontweight="bold")
    bot += np.array(row)
axes[1].set_xticks(x)
axes[1].set_xticklabels(labels)
axes[1].set_title("金牌的性别构成", fontsize=12.5)
axes[1].set_ylim(0, 37)
axes[1].legend(loc="upper right", fontsize=9.5)
flat(axes[1])

rate = [t["合计"] / t["金"] for t in top3]
bars = axes[2].bar(x, rate, 0.5, color=["#2F6FED", "#C8102E", "#D9A21B"], zorder=3)
for bar, v in zip(bars, rate):
    axes[2].text(bar.get_x() + bar.get_width() / 2, v + 0.08, "%.2f" % v, ha="center",
                 fontsize=11, fontweight="bold", color=TEXT)
axes[2].axhline(1, color="#94A3B8", ls="--", lw=1, zorder=2)
axes[2].text(-0.45, 4.92, "虚线 1.0 = 拿到的全是金牌", fontsize=9, color="#8A97A8", ha="left", va="top")
axes[2].set_xticks(x)
axes[2].set_xticklabels(labels)
axes[2].set_title("总奖牌 ÷ 金牌（越小越“含金”）", fontsize=12.5)
axes[2].set_ylim(0, 5.2)
flat(axes[2])

top = head(fig, "中日韩三国奖牌结构对比",
           "中国金牌最集中；日本奖牌更多但偏“散”；韩国的奖牌主要靠铜牌堆积",
           y=0.99, gap=0.062)
fig.subplots_adjust(top=top, bottom=0.1, left=0.06, right=0.98, wspace=0.28)
note(fig, "数据来源：OCA 官方成绩系统 · 截止 2026-09-22", y=0.015)
out(fig, "02_中日韩对比.png")

# ============================================================ 03 奖牌性别结构
d14 = R["A_奖牌榜结构"]["男女金银铜拆分"]
names = [x["代表团"] for x in d14][::-1]
mm = np.array([x["男"] for x in d14][::-1], dtype=float)
ww = np.array([x["女"] for x in d14][::-1], dtype=float)
xx = np.array([x["混合"] for x in d14][::-1], dtype=float)
tot = mm + ww + xx
yy = np.arange(len(names))
fig, ax = plt.subplots(figsize=(9.4, 6.6))
ax.barh(yy, mm / tot * 100, 0.66, color="#2F6FED", label="男子项目", zorder=3)
ax.barh(yy, ww / tot * 100, 0.66, left=mm / tot * 100, color="#C8102E",
        label="女子项目", zorder=3)
ax.barh(yy, xx / tot * 100, 0.66, left=(mm + ww) / tot * 100, color="#8B5CF6",
        label="混合项目", zorder=3)
for i in range(len(names)):
    ax.text(102, i, "女 %.0f%%" % (ww[i] / tot[i] * 100), va="center", fontsize=9.5,
            color="#C8102E", fontweight="bold")
ax.set_yticks(yy)
ax.set_yticklabels(names, fontsize=11)
ax.set_xlim(0, 122)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.set_xlabel("奖牌构成")
ax.grid(axis="x", color=GRID, zorder=0)
ax.grid(axis="y", visible=False)
ax.tick_params(length=0)
ax.legend(loc="lower left", bbox_to_anchor=(0.0, -0.185), ncol=3)
top = head(fig, "奖牌榜前 14 名的男女项目构成",
           "中国、日本、韩国靠女子项目挑大梁；塔吉克斯坦的金牌则全部来自男子项目")
fig.subplots_adjust(top=top, left=0.16, right=0.96, bottom=0.16)
note(fig, "数据来源：OCA 官方成绩系统 · 截止 2026-09-22 · 混合项目指男女混合参赛的小项")
out(fig, "03_奖牌性别结构.png")

# ============================================================ 04 集中度
allm = R["A_奖牌榜结构"]["全部"]
vals = sorted([x["合计"] for x in allm], reverse=True)
cum = np.cumsum(vals) / sum(vals) * 100
gvals = sorted([x["金"] for x in allm], reverse=True)
gcum = np.cumsum(gvals) / sum(gvals) * 100
fig, ax = plt.subplots(figsize=(9.4, 5.4))
xi = np.arange(1, len(vals) + 1)
ax.plot(xi, cum, "-o", ms=4, color="#2F6FED", label="奖牌累计占比", zorder=3)
ax.plot(xi, gcum, "-s", ms=4, color=C_GOLD, label="金牌累计占比", zorder=3)
ax.fill_between(xi, 0, cum, color="#2F6FED", alpha=0.07)
for k, lab in ((5, "前5名"), (10, "前10名")):
    ax.axvline(k, color="#AAB6C6", ls=":", lw=1.2, zorder=1)
    ax.annotate("%s：%.0f%% 奖牌 / %.0f%% 金牌" % (lab, cum[k - 1], gcum[k - 1]),
                xy=(k, cum[k - 1]), xytext=(k + 1.5, cum[k - 1] - 18),
                fontsize=10, color=TEXT,
                arrowprops=dict(arrowstyle="-", color="#AAB6C6", lw=1))
ax.set_xlabel("代表团数（按奖牌数降序）")
ax.set_ylabel("累计占比（%）")
ax.set_xlim(1, len(vals))
ax.set_ylim(0, 103)
ax.grid(axis="x", visible=False)
ax.tick_params(length=0)
ax.legend(loc="lower right")
top = head(fig, "奖牌高度集中：5 个代表团拿走 79% 的金牌",
           "34 个已有奖牌的代表团中，前 5 名占 78.7% 金牌、57.4% 奖牌")
fig.subplots_adjust(top=top, left=0.085, right=0.97, bottom=0.13)
note(fig, "数据来源：OCA 官方成绩系统 · 截止 2026-09-22；奖牌基尼系数 0.59，金牌 0.62")
out(fig, "04_奖牌集中度.png")

# ============================================================ 05 优势项目热力图
B = R["B_各国优势项目图谱"]
orgs_l = B["矩阵"]["代表团"]
discs_l = B["矩阵"]["项目"]
V = np.array(B["矩阵"]["值"], dtype=float)
cmap = LinearSegmentedColormap.from_list("gold", ["#FFFFFF", "#FBF0CF", "#E9C363", "#C08A0A"])
fig, ax = plt.subplots(figsize=(10.8, 6.8))
im = ax.imshow(V, cmap=cmap, aspect="auto", vmin=0)
ax.set_xticks(np.arange(len(discs_l)))
ax.set_xticklabels(discs_l, rotation=42, ha="right", fontsize=10.5)
ax.set_yticks(np.arange(len(orgs_l)))
ax.set_yticklabels(orgs_l, fontsize=11)
for i in range(len(orgs_l)):
    for j in range(len(discs_l)):
        v = V[i, j]
        if v:
            ax.text(j, i, "%d" % v, ha="center", va="center", fontsize=10.5,
                    fontweight="bold", color="#4A3200")
ax.set_xticks(np.arange(-0.5, len(discs_l), 1), minor=True)
ax.set_yticks(np.arange(-0.5, len(orgs_l), 1), minor=True)
ax.grid(which="minor", color="#E6EBF2", lw=1.2)
ax.grid(which="major", visible=False)
ax.tick_params(which="both", length=0)
cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.015)
cb.set_label("金牌数（枚）", fontsize=10)
cb.outline.set_visible(False)
top = head(fig, "各国优势项目图谱：金牌都从哪来",
           "截至第 4 日仅 15 个项目产生金牌；游泳一国独大，空手道是唯一“九国分金”的分散项目")
fig.subplots_adjust(top=top, left=0.115, right=0.985, bottom=0.19)
note(fig, "数据来源：OCA 官方成绩系统 · 截止 2026-09-22 · 空白表示该项目尚未夺金")
out(fig, "05_优势项目热力图.png")

# ============================================================ 06 夺金广度
C = R["B_各国优势项目图谱"]["集中度"]
fig, ax = plt.subplots(figsize=(9.6, 5.8))
for i, c in enumerate(C):
    if c["金牌"] < 2:
        continue
    ax.scatter(c["夺金项目数"], c["等效项目数"], s=90 + c["金牌"] * 26,
               color=PALETTE[i % len(PALETTE)], alpha=0.85, edgecolor="white",
               lw=1.5, zorder=3)
    ax.annotate(c["代表团"], (c["夺金项目数"], c["等效项目数"]),
                textcoords="offset points", xytext=(0, 17), ha="center",
                fontsize=10.5, color=TEXT, fontweight="bold")
ax.plot([0, 10.2], [0, 10.2], ls="--", lw=1.1, color="#AAB6C6", zorder=2)
ax.text(4.7, 6.95, "对角线上方 = 金牌越平均分散\n对角线下方 = 越依赖单一项目",
        fontsize=9.5, color="#8A97A8", ha="left", va="top")
ax.set_xlabel("夺金项目数（个）")
ax.set_ylabel("等效项目数 = 1 / 赫芬达尔指数")
ax.set_xlim(0.2, 10.2)
ax.set_ylim(0.2, 7.2)
ax.tick_params(length=0)
top = head(fig, "夺金是“广撒网”还是“押单点”？",
           "中国 32 金分散在 9 个项目（最均衡）；泰国 4 金有 3 金来自台克球（最集中）")
fig.subplots_adjust(top=top, left=0.09, right=0.97, bottom=0.13)
note(fig, "等效项目数越小说明金牌越集中在少数项目；气泡大小代表金牌总数 · 仅展示金牌≥2 的代表团")
out(fig, "06_夺金广度.png")

# ============================================================ 07 中国金牌结构
cd = R["C_中国代表团拆解"]["金牌项目分布"]
labels = [x["项目"] for x in cd]
vals = [x["金牌"] for x in cd]
fig, ax = plt.subplots(figsize=(9.0, 6.2))
wedges, _ = ax.pie(vals, startangle=90, counterclock=False,
                   colors=plt.cm.Reds(np.linspace(0.88, 0.2, len(vals))),
                   wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
ax.text(0, 0.1, "32", ha="center", va="center", fontsize=42, fontweight="bold",
        color="#C8102E")
ax.text(0, -0.24, "枚金牌", ha="center", va="center", fontsize=13, color="#6B7A90")
ax.legend(wedges, ["%s %d金" % (a, b) for a, b in zip(labels, vals)],
          loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=11)
top = head(fig, "中国代表团 32 金的项目结构",
           "游泳一项贡献 15 金，接近半壁江山；跳水、举重等传统强项尚未开赛")
fig.subplots_adjust(top=top, left=0.0, right=0.72, bottom=0.08)
note(fig, "数据来源：OCA 官方成绩系统 · 截止 2026-09-22 · 中国暂列奖牌榜第一")
out(fig, "07_中国金牌结构.png")

# ============================================================ 08 中国统治力
cd = [x for x in R["C_中国代表团拆解"]["金牌项目分布"] if x["金牌"] >= 2][::-1]
names = [x["项目"] for x in cd]
mine = [x["金牌"] for x in cd]
share = [x["占该项目全球金牌比"] for x in cd]
fig, ax = plt.subplots(figsize=(9.8, 5.8))
yy = np.arange(len(names))
ax.barh(yy, [100] * len(names), 0.62, color="#F1F4F9", zorder=2)
bars = ax.barh(yy, share, 0.62, color="#C8102E", alpha=0.9, zorder=3)
for bar, m, s in zip(bars, mine, share):
    ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2,
            "%.0f%%  ·  %d金" % (s, m), va="center", fontsize=10.5,
            fontweight="bold", color="#C8102E")
ax.set_yticks(yy)
ax.set_yticklabels(names, fontsize=12)
ax.set_xlim(0, 120)
ax.set_xticks([0, 20, 40, 60, 80, 100])
ax.set_xticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
ax.set_xlabel("中国金牌 ÷ 该项目已产生的全部金牌")
ax.grid(axis="x", visible=False)
ax.grid(axis="y", visible=False)
ax.tick_params(length=0)
top = head(fig, "中国在已开赛项目上的“统治力”",
           "射击 5 金拿走 4 金（80%）、游泳 21 金拿走 15 金（71%）、武术 6 金拿走 4 金（67%）")
fig.subplots_adjust(top=top, left=0.13, right=0.97, bottom=0.13)
note(fig, "仅统计中国夺金 ≥2 枚的项目；灰色背景为该项目已产生的全部金牌")
out(fig, "08_中国统治力.png")

# ============================================================ 09 年龄
ages = []
with open(os.path.join(A, "D_奖牌选手年龄.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        ages.append(float(r["年龄"]))
by_disc = R["D_选手画像"]["年龄"]["分项目"]
fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.2))
axes[0].hist(ages, bins=np.arange(13, 39, 1.5), color="#C8102E", alpha=0.88, zorder=3,
             edgecolor="white", linewidth=1.2)
med = R["D_选手画像"]["年龄"]["中位数"]
axes[0].axvline(med, color="#1F2733", ls="--", lw=1.4, zorder=4)
axes[0].text(med + 0.6, axes[0].get_ylim()[1] * 0.86, "中位数 %.0f 岁" % med,
             fontsize=11, fontweight="bold", color=TEXT)
axes[0].set_xlabel("夺牌时年龄（岁）")
axes[0].set_ylabel("奖牌记录数")
axes[0].set_title("187 条奖牌记录的年龄分布", fontsize=13)
axes[0].grid(axis="x", visible=False)
axes[0].tick_params(length=0)

bd = [x for x in by_disc if x["人数"] >= 5][::-1]
nn = [x["项目"] for x in bd]
mv = [x["中位年龄"] for x in bd]
cols = ["#C8102E" if v <= 24 else "#2F6FED" for v in mv]
bars = axes[1].barh(np.arange(len(nn)), mv, 0.62, color=cols, zorder=3)
for bar, v, cnt in zip(bars, mv, [x["人数"] for x in bd]):
    axes[1].text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                 "%.1f 岁 · %d 人" % (v, cnt), va="center", fontsize=10, color=TEXT)
axes[1].set_yticks(np.arange(len(nn)))
axes[1].set_yticklabels(nn, fontsize=11)
axes[1].set_xlim(0, 36)
axes[1].set_xlabel("夺牌选手中位年龄（岁）")
axes[1].set_title("各项目夺牌选手的年龄差异", fontsize=13)
axes[1].grid(axis="y", visible=False)
axes[1].tick_params(length=0)

top = head(fig, "夺牌选手年龄：中位数 25 岁，最小 13 岁",
           "中国 13 岁小将已拿 2 金；游泳夺牌选手最年轻（22.4 岁），综合格斗最年长（27.5 岁）",
           y=0.99, gap=0.065)
fig.subplots_adjust(top=top, bottom=0.13, left=0.075, right=0.97, wspace=0.42)
note(fig, "样本为 251 条奖牌记录中 187 条有出生日期的记录；年龄按比赛日推算")
out(fig, "09_奖牌选手年龄.png")

# ============================================================ 10 规模 vs 产出
eff = R["F_参赛规模与产出效率"]["全部"]
with_medal = [e for e in eff if e["奖牌"] > 0]
fig, ax = plt.subplots(figsize=(9.8, 6.2))
xs = np.array([e["参赛人数"] for e in with_medal], dtype=float)
ys = np.array([e["奖牌"] for e in with_medal], dtype=float)
ax.scatter(xs, ys, s=60, color="#2F6FED", alpha=0.55, edgecolor="white", lw=1.2, zorder=3)
lab = {"中国", "日本", "韩国", "中国香港", "印度", "哈萨克斯坦", "泰国", "中国台北",
       "乌兹别克斯坦", "塔吉克斯坦", "新加坡", "伊朗", "中国澳门"}
OFFS = {"中国": (0, 14), "日本": (0, 14), "韩国": (0, 14),
        "哈萨克斯坦": (-34, 11), "中国香港": (30, 11),
        "中国台北": (-34, 8), "印度": (2, -19), "乌兹别克斯坦": (0, -19),
        "泰国": (0, 13), "塔吉克斯坦": (-46, 9), "中国澳门": (26, 9),
        "新加坡": (-6, 13), "伊朗": (34, 5)}
for e in with_medal:
    if e["代表团"] in lab:
        dx, dy = OFFS.get(e["代表团"], (0, 12))
        ax.annotate(e["代表团"], (e["参赛人数"], e["奖牌"]), textcoords="offset points",
                    xytext=(dx, dy), ha="center", fontsize=10.5, fontweight="bold",
                    color=TEXT)
for ref in (200, 500, 1000):
    x_end = min(1190.0, 57.0 * 10000 / ref)
    xr = np.linspace(20, x_end, 50)
    ax.plot(xr, ref / 10000 * xr, ls=":", lw=1.1, color="#C3CCDA", zorder=1)
    ax.text(x_end - 12, ref / 10000 * x_end - 1.0, "%d枚/万人" % ref, fontsize=8.5,
            color="#9AA6B2", ha="right", va="top")
ax.set_xlabel("参赛人数（人，按注册号去重）")
ax.set_ylabel("奖牌数（枚）")
ax.set_xlim(0, 1330)
ax.set_ylim(0, 60)
ax.tick_params(length=0)
top = head(fig, "参赛规模和奖牌产出：不是人越多牌越多",
           "中国 939 人拿 53 牌，产出率最高；日本 1082 人参赛最多、奖牌 46 枚；12 个代表团颗粒无收")
fig.subplots_adjust(top=top, left=0.085, right=0.97, bottom=0.12)
note(fig, "虚线为“每万人 200/500/1000 枚奖牌”的等产出率参考线 · 仅展示已有奖牌的代表团")
out(fig, "10_规模与产出.png")

# ============================================================ 11 每日节奏
E = R["E_赛事节奏与场馆"]
dates = E["赛程日期"]
comp = [x["项目数"] for x in E["每日有比赛的项目数"]]
medl = [x["项目数"] for x in E["每日产生奖牌的项目数"]]
act = {x["日期"]: x["金牌"] for x in E["每日实际金牌(已开赛部分)"]}
short = [d[5:].replace("-", "/") for d in dates]
xi = np.arange(len(dates))
fig, ax = plt.subplots(figsize=(12.6, 5.8))
ax.axvspan(-0.5, 8.5, color="#F5F7FA", zorder=0)
ax.bar(xi, comp, 0.72, color="#DCE4EF", label="当日有比赛的项目数", zorder=3)
ax.bar(xi, medl, 0.72, color="#E9C363", label="当日产生奖牌的项目数", zorder=4)
ax2 = ax.twinx()
gold_line = [act.get(d, 0) for d in dates]
ax2.plot(xi, gold_line, "-o", ms=5.5, color="#C8102E", lw=2.2,
         label="当日实际金牌数", zorder=6)
for i, v in enumerate(gold_line):
    if v:
        ax2.annotate(str(v), (i, v), textcoords="offset points", xytext=(0, 9),
                     ha="center", fontsize=10, color="#C8102E", fontweight="bold")
ax2.set_ylim(0, 40)
ax2.set_ylabel("当日实际金牌数（枚）", color="#C8102E")
ax2.tick_params(axis="y", colors="#C8102E", length=0)
ax2.grid(False)
ax.set_xticks(xi)
ax.set_xticklabels(short, rotation=60, ha="right", fontsize=9)
ax.set_ylabel("项目数（个）")
ax.set_ylim(0, 34)
ax.set_xlabel("赛程日期")
ax.grid(axis="x", visible=False)
ax.tick_params(length=0)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="lower left", bbox_to_anchor=(0.0, 1.005), ncol=3,
          fontsize=10)
top = head(fig, "25 天赛程节奏：9/26 与 9/27 是最忙的两天",
           "灰柱=当日开赛项目数，黄柱=当日出奖牌的项目数，红线=实际已产生金牌（数据截止 9/22）",
           gap=0.078)
fig.subplots_adjust(top=top, left=0.06, right=0.93, bottom=0.22)
note(fig, "赛程来自官方赛程矩阵；实际金牌按奖牌明细的完赛日期统计 · 灰色带为 9/10-9/18 开幕前提前开赛的足球、篮球等项目 · 9/19 为开幕式日")
out(fig, "11_每日节奏.png")

# ============================================================ 12 项目赛程热力图
mx = json.load(open(os.path.join(ROOT, "数据", "官方_赛程矩阵.json"), encoding="utf-8"))
m_dates = mx["dates"]
rows = []
for it in mx["matrix"]:
    rows.append((disc(it["Disc"]["Key"]),
                 [{"N": 0, "0": 1, "1": 2}.get(v, 0) for v in it["Dates"]]))
rows.sort(key=lambda a: (-sum(1 for v in a[1] if v), a[0]))
M = np.array([r[1] for r in rows], dtype=float)
cmap2 = ListedColormap(["#FBFCFE", "#CFE0F7", "#D9A21B"])
fig, ax = plt.subplots(figsize=(12.8, 11.6))
ax.imshow(M, cmap=cmap2, aspect="auto", vmin=0, vmax=2)
ax.set_xticks(np.arange(len(m_dates)))
ax.set_xticklabels([d[5:].replace("-", "/") for d in m_dates], fontsize=9.5)
ax.set_yticks(np.arange(len(rows)))
ax.set_yticklabels([r[0] for r in rows], fontsize=10)
ax.set_xticks(np.arange(-0.5, len(m_dates), 1), minor=True)
ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
ax.grid(which="minor", color="#F0F3F8", lw=0.8)
ax.grid(which="major", visible=False)
ax.tick_params(which="both", length=0)
ax.axvline(8.5, color="#C8102E", lw=1.6, zorder=5)
for i, lb in enumerate(ax.get_xticklabels()):
    if m_dates[i] == "2026-09-19":
        lb.set_color("#C8102E")
        lb.set_fontweight("bold")
ax.legend(handles=[mpatches.Patch(color="#FBFCFE", label="无安排"),
                   mpatches.Patch(color="#CFE0F7", label="比赛日（无奖牌）"),
                   mpatches.Patch(color="#D9A21B", label="产生奖牌")],
          loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3, fontsize=10.5)
top = head(fig, "59 个项目的 25 天赛程全景",
           "金色格子 = 当天产生奖牌；射击、电子竞技、空手道几乎“天天出牌”", y=0.99,
           gap=0.055)
fig.subplots_adjust(top=top, left=0.115, right=0.99, bottom=0.055)
note(fig, "红色竖线 = 9/19 开幕式 · 数据来源：OCA 官方成绩系统赛程矩阵", y=0.012)
out(fig, "12_项目赛程热力图.png")

# ============================================================ 13 场馆城市
vc = sorted(E["场馆"]["城市分布"], key=lambda x: -x["场馆数"])
fig, ax = plt.subplots(figsize=(10.6, 5.4))
names = [x["城市"] for x in vc][::-1]
vals = [x["场馆数"] for x in vc][::-1]
cols = ["#C8102E" if v >= 6 else "#2F6FED" if v >= 3 else "#9BB4E0" for v in vals]
bars = ax.barh(np.arange(len(names)), vals, 0.7, color=cols, zorder=3)
for bar, v in zip(bars, vals):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2, str(v),
            va="center", fontsize=10.5, fontweight="bold", color=TEXT)
ax.set_yticks(np.arange(len(names)))
ax.set_yticklabels(names, fontsize=11)
ax.set_xlim(0, 31)
ax.set_xlabel("场馆数（个）")
ax.grid(axis="x", visible=False)
ax.grid(axis="y", visible=False)
ax.tick_params(length=0)
top = head(fig, "场馆分布在 24 个城市：名古屋一城占四成",
           "59 个唯一场馆（71 条场馆-项目记录）；名古屋 28 条，东京、静冈也承办了部分项目")
fig.subplots_adjust(top=top, left=0.1, right=0.97, bottom=0.12)
note(fig, "数据来源：OCA 官方成绩系统场馆接口；同一场馆承办多个项目时重复计入")
out(fig, "13_场馆城市分布.png")

# ============================================================ 14 项目参赛人数
dd = R["D_选手画像"]["规模"]["项目规模前12"]
fig, ax = plt.subplots(figsize=(9.8, 5.8))
names = [x["项目"] for x in dd][::-1]
vals = [x["人数"] for x in dd][::-1]
bars = ax.barh(np.arange(len(names)), vals, 0.66,
               color=[plt.cm.Blues(0.35 + 0.5 * v / max(vals)) for v in vals], zorder=3)
for bar, v in zip(bars, vals):
    ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height() / 2, str(v),
            va="center", fontsize=10.5, fontweight="bold", color=TEXT)
ax.set_yticks(np.arange(len(names)))
ax.set_yticklabels(names, fontsize=11.5)
ax.set_xlim(0, 990)
ax.set_xlabel("参赛人数（人）")
ax.grid(axis="x", visible=False)
ax.grid(axis="y", visible=False)
ax.tick_params(length=0)
top = head(fig, "哪些项目人最多：田径 851 人、电子竞技 722 人",
           "12,753 名参赛选手中，田径、电子竞技、足球三项就占了近三成")
fig.subplots_adjust(top=top, left=0.12, right=0.97, bottom=0.12)
note(fig, "按参赛选手注册号去重；同一选手兼项时只计一次")
out(fig, "14_项目参赛人数.png")

print("已生成 %d 张图表:" % len(MADE))
for m in MADE:
    print("  " + m)
