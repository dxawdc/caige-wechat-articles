# -*- coding: utf-8 -*-
"""生成公众号文章使用的复核指标与图表。

统一口径：
- A 股主样本为《游戏公司_A股_分层.csv》中的“核心”与“重要”两层，共 24 家。
- 除特别注明外，营收均为上市公司合并营业总收入，可能包含非游戏业务。
- 同比聚合使用 2026H1 合计值 / 2025H1 合计值，不对公司同比做简单平均。
"""

import csv
import hashlib
import json
import os
import statistics as st
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 绘图样式 as T  # noqa: E402


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "数据")
ANA = os.path.join(BASE, "分析")
CHART = os.path.join(BASE, "图表")
os.makedirs(CHART, exist_ok=True)

SRC = "数据来源：东方财富财报数据／上市公司公告　制图：可以叫我才哥"


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(value):
    if value in (None, "", "-"):
        return None
    return float(value)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def pct(current, previous):
    return None if not previous else (current / previous - 1) * 100


T.setup()

tier_path = os.path.join(DATA, "游戏公司_A股_分层.csv")
metric_path = os.path.join(ANA, "公司指标汇总.csv")
income_2025_path = os.path.join(DATA, "游戏公司_A股_利润表_2025H06.csv")
income_2026_path = os.path.join(DATA, "游戏公司_A股_利润表_2026H06.csv")

tier_rows = read_csv(tier_path)
metric_rows = read_csv(metric_path)
income_2025 = read_csv(income_2025_path)
income_2026 = read_csv(income_2026_path)

tier = {r["代码"]: r for r in tier_rows}
codes = [r["代码"] for r in tier_rows if r["层级"] in ("核心", "重要")]
metrics = {r["代码"]: r for r in metric_rows if r["代码"] in codes}
inc25 = {r["SECURITY_CODE"]: r for r in income_2025}
inc26 = {r["SECURITY_CODE"]: r for r in income_2026}

if len(codes) != 24 or len(metrics) != 24:
    raise RuntimeError(f"主样本应为 24 家，实际 codes={len(codes)}, metrics={len(metrics)}")

rows = []
for code in codes:
    m = metrics[code]
    r25 = inc25[code]
    r26 = inc26[code]
    rev25 = num(r25["TOTAL_OPERATE_INCOME"]) / 1e8
    rev26 = num(r26["TOTAL_OPERATE_INCOME"]) / 1e8
    np25 = num(r25["PARENT_NETPROFIT"]) / 1e8
    np26 = num(r26["PARENT_NETPROFIT"]) / 1e8
    rows.append({
        "代码": code,
        "公司": m["公司"],
        "层级": tier[code]["层级"],
        "营收2025_亿": rev25,
        "营收2026_亿": rev26,
        "营收增量_亿": rev26 - rev25,
        "营收同比_%": num(m["营收同比_%"]),
        "归母2025_亿": np25,
        "归母2026_亿": np26,
        "归母增量_亿": np26 - np25,
        # 公司同比使用财报接口披露字段。尤其在上年亏损或接近零时，
        # 直接用本期/上期重算会出现符号方向与披露口径不一致的问题。
        "归母同比_%": num(m["归母同比_%"]),
        "销售费用率_%": num(m["销售费用率_%"]),
        "研发费用率_%": num(m["研发费用率_%"]),
        "经营现金流_亿": num(m["经营现金流_亿"]),
        "游戏收入_亿": num(tier[code]["游戏收入_亿"]),
    })

rev26 = sum(r["营收2026_亿"] for r in rows)
rev25 = sum(r["营收2025_亿"] for r in rows)
np26 = sum(r["归母2026_亿"] for r in rows)
np25 = sum(r["归母2025_亿"] for r in rows)

rev_growth = pct(rev26, rev25)
np_growth = pct(np26, np25)
rev_median = st.median(r["营收同比_%"] for r in rows)
np_median = st.median(r["归母同比_%"] for r in rows)

revenue_delta_rank = sorted(rows, key=lambda r: r["营收增量_亿"], reverse=True)
profit_delta_rank = sorted(rows, key=lambda r: r["归母增量_亿"], reverse=True)
top3_revenue_codes = {r["代码"] for r in revenue_delta_rank[:3]}
top3_profit_codes = {r["代码"] for r in profit_delta_rank[:3]}

rev_top3_delta = sum(r["营收增量_亿"] for r in revenue_delta_rank[:3])
rev_other_delta = sum(r["营收增量_亿"] for r in rows if r["代码"] not in top3_revenue_codes)
rev_other_2025 = sum(r["营收2025_亿"] for r in rows if r["代码"] not in top3_revenue_codes)
rev_other_2026 = sum(r["营收2026_亿"] for r in rows if r["代码"] not in top3_revenue_codes)

np_top3_delta = sum(r["归母增量_亿"] for r in profit_delta_rank[:3])
np_other_2025 = sum(r["归母2025_亿"] for r in rows if r["代码"] not in top3_profit_codes)
np_other_2026 = sum(r["归母2026_亿"] for r in rows if r["代码"] not in top3_profit_codes)

known_game_revenue = 0.0
for r in rows:
    # 电魂网络、吉比特的主营构成未按产品拆分，但均为纯游戏公司，取公司营收。
    known_game_revenue += r["游戏收入_亿"] if r["游戏收入_亿"] is not None else r["营收2026_亿"]

summary = {
    "报告期": "2026H1",
    "样本口径": "A股核心14家+重要10家，共24家",
    "样本家数": len(rows),
    "营收": {
        "2026H1_亿元": round(rev26, 2),
        "2025H1_亿元": round(rev25, 2),
        "合计同比_%": round(rev_growth, 2),
        "公司同比中位数_%": round(rev_median, 2),
        "正增长家数": sum(r["营收增量_亿"] > 0 for r in rows),
        "CR3_%": round(sum(r["营收2026_亿"] for r in sorted(rows, key=lambda x: x["营收2026_亿"], reverse=True)[:3]) / rev26 * 100, 2),
        "增量前三家": [r["公司"] for r in revenue_delta_rank[:3]],
        "增量前三合计_亿元": round(rev_top3_delta, 2),
        "其余21家合计增量_亿元": round(rev_other_delta, 2),
        "其余21家合计同比_%": round(pct(rev_other_2026, rev_other_2025), 2),
    },
    "归母净利润": {
        "2026H1_亿元": round(np26, 2),
        "2025H1_亿元": round(np25, 2),
        "合计同比_%": round(np_growth, 2),
        "公司同比中位数_%": round(np_median, 2),
        "盈利家数": sum(r["归母2026_亿"] > 0 for r in rows),
        "亏损家数": sum(r["归母2026_亿"] < 0 for r in rows),
        "由盈转亏家数": sum(r["归母2025_亿"] > 0 and r["归母2026_亿"] < 0 for r in rows),
        "扭亏家数": sum(r["归母2025_亿"] < 0 and r["归母2026_亿"] > 0 for r in rows),
        "连续两期盈利家数": sum(r["归母2025_亿"] > 0 and r["归母2026_亿"] > 0 for r in rows),
        "连续盈利且利润增加家数": sum(
            r["归母2025_亿"] > 0 and r["归母2026_亿"] > r["归母2025_亿"] for r in rows
        ),
        "增量前三家": [r["公司"] for r in profit_delta_rank[:3]],
        "增量前三合计_亿元": round(np_top3_delta, 2),
        "其余21家合计同比_%": round(pct(np_other_2026, np_other_2025), 2),
    },
    "游戏分部估算": {
        "可识别游戏相关收入_亿元": round(known_game_revenue, 2),
        "占样本公司总营收_%": round(known_game_revenue / rev26 * 100, 2),
        "说明": "按公司主营构成披露汇总；电魂网络、吉比特按纯游戏公司取总营收。用于校验样本纯度，不作为市场规模。",
    },
    "输入文件SHA256": {
        os.path.relpath(p, BASE).replace("\\", "/"): sha256(p)
        for p in (tier_path, metric_path, income_2025_path, income_2026_path)
    },
    "公司明细": rows,
}

with open(os.path.join(ANA, "文章关键指标.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)


def save(fig, filename):
    path = os.path.join(CHART, filename)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=T.CARD)
    plt.close(fig)
    print(path)


def chart_growth_bridge():
    labels = ["2025H1\n样本营收", "增量前三家\n贡献", "其余21家\n贡献", "2026H1\n样本营收"]
    bottoms = [0, rev25, rev25 + rev_top3_delta, 0]
    heights = [rev25, rev_top3_delta, rev_other_delta, rev26]
    colors = [T.BLUE, T.UP, T.DOWN, T.INK]

    fig, ax = T.canvas(
        10.2, 6.2,
        "总营收增长 18.2%，但增量被三家公司包办",
        f"24 家样本营收同比中位数为 {rev_median:.1f}%；剔除世纪华通、巨人网络、恺英网络后，其余 21 家合计同比 {pct(rev_other_2026, rev_other_2025):+.1f}%",
        SRC, top=0.84, bottom=0.16,
    )
    x = np.arange(4)
    for i, (bottom, height, color) in enumerate(zip(bottoms, heights, colors)):
        ax.bar(i, height, bottom=bottom, color=color, width=0.58, zorder=3)
        if i in (0, 3):
            text = f"{height:.1f} 亿元"
            y = height + 13
        else:
            text = f"{height:+.1f} 亿元"
            y = bottom + height + (10 if height >= 0 else -14)
        ax.text(i, y, text, ha="center", va="center", fontsize=11,
                fontweight="bold", color=color if i not in (0, 3) else T.INK)

    levels = [rev25, rev25 + rev_top3_delta, rev26]
    for i, level in enumerate(levels):
        ax.plot([i + 0.29, i + 0.71], [level, level], color=T.NEUTRAL, lw=1.1, zorder=2)

    ax.text(3, rev26 * 0.53, f"同比\n+{rev_growth:.1f}%", color="white", ha="center", va="center",
            fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("营业总收入（亿元）")
    ax.set_ylim(0, max(rev26, rev25 + rev_top3_delta) * 1.16)
    T.strip(ax)
    T.grid(ax, "y")
    fig.text(0.09, 0.075, "注：营业总收入为公司合并口径，部分公司同时经营非游戏业务。", fontsize=8.5, color=T.SUB)
    save(fig, "01_增长集中_营收增量桥.png")


def chart_revenue_ranking():
    ranked = sorted(rows, key=lambda r: r["营收2026_亿"])
    names = [r["公司"] for r in ranked]
    vals = [r["营收2026_亿"] for r in ranked]
    colors = [T.TIER_CORE if r["层级"] == "核心" else T.TIER_IMP for r in ranked]
    fig, ax = T.canvas(
        10.2, 8.0,
        "24 家 A 股游戏样本，头部三家占总营收 57%",
        "深蓝＝核心样本（游戏收入占比较高／纯游戏）　橙色＝游戏为重要业务；括号内为营业总收入同比",
        SRC, bottom=0.145,
    )
    ax.barh(names, vals, color=colors, height=0.66, zorder=3)
    maxv = max(vals)
    for i, (v, r) in enumerate(zip(vals, ranked)):
        g = r["营收同比_%"]
        ax.text(v + maxv * 0.012, i, f"{v:.1f}", va="center", fontsize=8.8,
                fontweight="bold", color=T.INK)
        ax.text(v + maxv * 0.085, i, f"({g:+.1f}%)", va="center", fontsize=8.3,
                color=T.UP if g > 0 else T.DOWN)
    ax.set_xlim(0, maxv * 1.34)
    ax.set_xlabel("2026H1 营业总收入（亿元，含非游戏业务）")
    ax.tick_params(axis="y", labelsize=9.2)
    T.strip(ax)
    T.grid(ax, "x")
    fig.text(0.09, 0.072, "注：分层按游戏业务相关性确定，不代表投资评级。", fontsize=8.5, color=T.SUB)
    save(fig, "02_营收排行_统一口径.png")


def chart_profit_delta():
    ranked = sorted(rows, key=lambda r: r["归母增量_亿"])
    names = [r["公司"] for r in ranked]
    vals = [r["归母增量_亿"] for r in ranked]
    colors = [T.UP if v >= 0 else T.DOWN for v in vals]
    fig, ax = T.canvas(
        10.2, 8.0,
        "净利润合计增长 34.8%，利润改善同样集中在头部",
        f"按归母净利润绝对增量排序；剔除世纪华通、巨人网络、恺英网络后，其余 21 家归母净利润合计同比 {pct(np_other_2026, np_other_2025):+.1f}%",
        SRC, bottom=0.16,
    )
    ax.barh(names, vals, color=colors, height=0.66, zorder=3)
    ax.axvline(0, color=T.NEUTRAL, lw=1.1)
    span = max(max(vals), abs(min(vals)))
    for i, v in enumerate(vals):
        ax.text(v + (0.35 if v >= 0 else -0.35), i, f"{v:+.2f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=8.2, color=T.INK)
    ax.set_xlim(min(vals) - span * 0.16, max(vals) + span * 0.17)
    ax.set_xlabel("2026H1 归母净利润同比增量（亿元）")
    ax.tick_params(axis="y", labelsize=9.2)
    T.strip(ax)
    T.grid(ax, "x")
    fig.text(0.09, 0.072, "注：采用绝对增量，避免上年利润接近零或正负切换时同比百分比失真。", fontsize=8.5, color=T.SUB)
    save(fig, "03_利润分化_绝对增量.png")


def chart_cost_structure():
    core = [r for r in rows if r["层级"] == "核心" and r["销售费用率_%"] is not None and r["研发费用率_%"] is not None]
    core = sorted(core, key=lambda r: r["销售费用率_%"])
    names = [r["公司"] for r in core]
    sale = [r["销售费用率_%"] for r in core]
    rd = [r["研发费用率_%"] for r in core]
    y = np.arange(len(core))
    fig, ax = T.canvas(
        10.2, 7.0,
        "同样是游戏公司，销售与研发的投入结构差异很大",
        "仅展示 14 家核心样本；橙色＝销售费用率，蓝色＝研发费用率",
        SRC, bottom=0.165,
    )
    for i, (s, r) in enumerate(zip(sale, rd)):
        ax.plot([min(s, r), max(s, r)], [i, i], color="#D6DCE5", lw=2, zorder=1)
    ax.scatter(sale, y, s=58, color=T.ACCENT, label="销售费用率", zorder=3)
    ax.scatter(rd, y, s=58, color=T.BLUE, label="研发费用率", zorder=3)
    for i, (s, r) in enumerate(zip(sale, rd)):
        ax.text(max(s, r) + 1.1, i, f"{s:.0f} / {r:.0f}", va="center", fontsize=8.4, color=T.SUB)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.2)
    ax.set_xlabel("占营业总收入比重（%）　标注顺序：销售 / 研发")
    ax.set_xlim(0, max(max(sale), max(rd)) + 10)
    ax.legend(frameon=False, loc="lower right")
    T.strip(ax)
    T.grid(ax, "x")
    fig.text(0.09, 0.075, "注：销售费用不等同于买量，研发费用也不等同于全部研发投入；本图只比较财报费用率。", fontsize=8.5, color=T.SUB)
    save(fig, "04_费用结构_核心样本.png")


chart_growth_bridge()
chart_revenue_ranking()
chart_profit_delta()
chart_cost_structure()

print(json.dumps({k: v for k, v in summary.items() if k not in ("公司明细", "输入文件SHA256")}, ensure_ascii=False, indent=2))
