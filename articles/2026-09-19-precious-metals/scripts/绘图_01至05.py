# -*- coding: utf-8 -*-
"""绘制贵金属价格趋势配图（图01~图05）。"""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from 图表风格 import (ACCENT, BRAND_COLORS, CHARTS, CLEAN, GOLD, GOLD_LIGHT, GREEN,
                    GREY, INK, RED, ROOT, SILVER, SILVER_LIGHT, finish, setup, titles)

setup()

SRC = ("数据来源：新浪财经国际期货日线、上海黄金交易所官方日行情、金投网品牌金价；"
       "数据截至 2026-09-18，由「可以叫我才哥」整理")

ten_xau = pd.read_csv(CLEAN / "01_伦敦金现_近十年.csv", parse_dates=["date"])
ten_xag = pd.read_csv(CLEAN / "02_伦敦银现_近十年.csv", parse_dates=["date"])
ten_au = pd.read_csv(CLEAN / "03_上金所Au9999_近十年.csv", parse_dates=["date"])
two_brand = pd.read_csv(CLEAN / "06_品牌金价_近两年.csv", parse_dates=["日期"])
ratio = pd.read_csv(CLEAN / "07_金银比_近十年.csv", parse_dates=["date"])
metrics = json.loads((ROOT / "输出" / "统计指标.json").read_text(encoding="utf-8"))


def chart01() -> None:
    """近十年国际金银：黄金左轴、白银右轴。"""
    fig, ax = plt.subplots(figsize=(11.2, 5.6))
    ax2 = ax.twinx()
    ax.plot(ten_xau["date"], ten_xau["收盘"], color=GOLD, linewidth=2.2, label="伦敦金现（左轴）")
    ax2.plot(ten_xag["date"], ten_xag["收盘"], color=SILVER, linewidth=1.8, label="伦敦银现（右轴）")
    ax.fill_between(ten_xau["date"], ten_xau["收盘"], ten_xau["收盘"].min() * 0.92,
                    color=GOLD, alpha=0.10)

    for date, text, series, offset in (
        ("2016-12-30", "2016 年末\n约 1157 美元", ten_xau, 400),
        ("2020-08-04", "2020 年抗疫行情\n首次收于 2000 美元上方", ten_xau, 500),
        ("2025-10-20", "2025 年加速上行", ten_xau, 700),
        ("2026-01-28", "2026年1月 5414 美元\n区间最高", ten_xau, 260),
    ):
        point = series[series["date"] == date]
        if point.empty:
            near = series.iloc[(series["date"] - pd.Timestamp(date)).abs().argsort()[:1]]
            point = near
        value = float(point["收盘"].iloc[0])
        real_date = point["date"].iloc[0]
        ax.annotate(text, xy=(real_date, value), xytext=(real_date, value + offset),
                    fontsize=10, color=INK, ha="center",
                    arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))

    ax.set_ylim(float(ten_xau["收盘"].min()) * 0.9, float(ten_xau["收盘"].max()) * 1.16)
    ax2.set_ylim(0, float(ten_xag["收盘"].max()) * 1.22)
    ax.set_ylabel("伦敦金现（美元/盎司）", color=GOLD)
    ax2.set_ylabel("伦敦银现（美元/盎司）", color=SILVER)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="x", visible=False)
    ax2.grid(False)
    handles = ax.get_lines() + ax2.get_lines()
    ax.legend(handles, [h.get_label() for h in handles], loc="upper left", fontsize=11)
    titles(ax, "近十年国际金银价格：黄金涨 2.3 倍，白银涨 2.5 倍",
           f"区间：2016-09-19 至 2026-09-18，伦敦金现 {metrics['区间涨跌幅%']['伦敦金现']['近10年']}%，"
           f"伦敦银现 {metrics['区间涨跌幅%']['伦敦银现']['近10年']}%")
    finish(fig, [ax], "图01_近十年国际金银价格.png", SRC)


def chart02() -> None:
    """近十年国内人民币金价 + 年度均价柱。"""
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11.2, 6.6),
                                  gridspec_kw={"height_ratios": [3, 1.25], "hspace": 0.42})
    ax.plot(ten_au["date"], ten_au["收盘"], color=ACCENT, linewidth=2.0)
    ax.fill_between(ten_au["date"], ten_au["收盘"], ten_au["收盘"].min() * 0.85,
                    color=ACCENT, alpha=0.12)
    peak = ten_au.loc[ten_au["收盘"].idxmax()]
    ax.scatter([peak["date"]], [peak["收盘"]], color=RED, zorder=5, s=42)
    ax.annotate(f"{peak['date']:%Y-%m-%d}\n{peak['收盘']:.0f} 元/克（区间最高）",
                xy=(peak["date"], peak["收盘"]), xytext=(peak["date"] - timedelta(days=560),
                                                          peak["收盘"] * 1.03),
                fontsize=10, color=INK,
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    latest = ten_au.iloc[-1]
    ax.annotate(f"最新 {latest['收盘']:.0f} 元/克", xy=(latest["date"], latest["收盘"]),
                xytext=(latest["date"] - timedelta(days=560), latest["收盘"] * 0.72),
                fontsize=10, color=INK,
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    ax.set_ylabel("元/克")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="x", visible=False)
    titles(ax, "近十年上海金（Au99.99）：从 270 元/克到 947 元/克",
           f"上海黄金交易所官方日收盘价，区间涨幅 {metrics['区间涨跌幅%']['上金所Au99.99']['近10年']}%")

    yearly = ten_au.set_index("date")["收盘"].resample("YE").mean()
    labels, values = [], []
    for stamp, value in yearly.items():
        year_data = ten_au[ten_au["date"].dt.year == stamp.year]
        # 2016 年仅含 12 月下旬，单独标注
        labels.append(f"{stamp.year}*" if year_data["date"].min().month > 1 else f"{stamp.year}")
        values.append(float(value))
    ax2.bar(labels, values, color=[GOLD_LIGHT if l != labels[-1] else GOLD for l in labels],
            width=0.62)
    for label, value in zip(labels, values):
        ax2.text(label, value + max(values) * 0.03, f"{value:.0f}", ha="center",
                 fontsize=9.5, color=GREY)
    ax2.set_ylim(0, max(values) * 1.2)
    ax2.set_ylabel("年均价 元/克")
    ax2.grid(axis="x", visible=False)
    ax2.set_title("各年度均价（* 为 2016 年 12 月 19 日起）", loc="left", fontsize=13,
                  color=INK, pad=6)
    finish(fig, [ax, ax2], "图02_近十年上海金价格.png", SRC)


def chart03() -> None:
    """近十年金、银年度涨跌幅分组柱状（红涨绿跌）。"""
    gold = metrics["年度涨跌幅%"]["伦敦金现"]
    silver = metrics["年度涨跌幅%"]["伦敦银现"]
    years = [y for y in gold if y in silver and y != "2026"]
    x = np.arange(len(years))
    width = 0.38
    fig, ax = plt.subplots(figsize=(11.2, 5.2))
    gold_values = [gold[y] for y in years]
    silver_values = [silver[y] for y in years]
    ax.bar(x - width / 2, gold_values, width,
           color=[RED if v >= 0 else GREEN for v in gold_values], label="伦敦金现")
    ax.bar(x + width / 2, silver_values, width,
           color=[RED if v >= 0 else GREEN for v in silver_values], alpha=0.45,
           label="伦敦银现")
    for xs, values, offset in ((x - width / 2, gold_values, -0.6), (x + width / 2, silver_values, -0.6)):
        for xi, value in zip(xs, values):
            ax.text(xi, value + (2.5 if value >= 0 else -6), f"{value:.0f}",
                    ha="center", fontsize=8.6, color=GREY)
    ax.axhline(0, color="#B9C2CC", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.set_ylabel("年度涨跌幅 %")
    ax.legend(loc="upper left", fontsize=11)
    ax.grid(axis="x", visible=False)
    titles(ax, "近十年年度涨跌幅：2025 年是金银的大年",
           "2025 年伦敦金现上涨 62.5%，伦敦银现上涨 142.0%；2026 年为年初至今（截至 9-18）")
    finish(fig, [ax], "图03_近十年年度涨跌幅.png", SRC)


def chart04() -> None:
    """近两年国际金银放大图。"""
    start = pd.Timestamp("2024-09-19")
    js = ten_xau[ten_xau["date"] >= start]
    jg = ten_xag[ten_xag["date"] >= start]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11.2, 7.0), sharex=True,
                                  gridspec_kw={"height_ratios": [1, 1], "hspace": 0.22})
    ax.plot(js["date"], js["收盘"], color=GOLD, linewidth=2.1)
    ax.fill_between(js["date"], js["收盘"], js["收盘"].min() * 0.94, color=GOLD, alpha=0.12)
    ax.set_ylabel("美元/盎司", color=GOLD)
    titles(ax, "近两年黄金与白银：一条先冲高、后回落的曲线",
           f"2024-09-19 至 2026-09-18，黄金 +{metrics['区间涨跌幅%']['伦敦金现']['近2年']}%，"
           f"白银 +{metrics['区间涨跌幅%']['伦敦银现']['近2年']}%")

    peak = js.loc[js["收盘"].idxmax()]
    ax.scatter([peak["date"]], [peak["收盘"]], color=RED, zorder=5, s=40)
    ax.annotate(f"{peak['date']:%Y-%m-%d} 最高 {peak['收盘']:.0f}",
                xy=(peak["date"], peak["收盘"]),
                xytext=(peak["date"] - timedelta(days=620), peak["收盘"] + 40),
                fontsize=10.5, color=INK, ha="center",
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    ax.set_ylim(float(js["收盘"].min()) * 0.88, float(js["收盘"].max()) * 1.12)
    last = js.iloc[-1]
    ax.annotate(f"{last['date']:%Y-%m-%d}\n{last['收盘']:.0f} 美元（回撤 "
                f"{metrics['2026年内']['伦敦金现']['较最高回撤%']}%）",
                xy=(last["date"], last["收盘"]),
                xytext=(last["date"] - timedelta(days=380), last["收盘"] - 700),
                fontsize=10.5, color=INK, ha="center",
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))

    ax2.plot(jg["date"], jg["收盘"], color=SILVER, linewidth=1.9)
    ax2.fill_between(jg["date"], jg["收盘"], jg["收盘"].min() * 0.72, color=SILVER, alpha=0.16)
    ax2.set_ylabel("美元/盎司", color=SILVER)
    ax2.set_title("伦敦银现", loc="left", fontsize=14, color=SILVER, pad=8)
    peak2 = jg.loc[jg["收盘"].idxmax()]
    ax2.scatter([peak2["date"]], [peak2["收盘"]], color=RED, zorder=5, s=40)
    ax2.annotate(f"{peak2['date']:%Y-%m-%d} 最高 {peak2['收盘']:.0f}",
                 xy=(peak2["date"], peak2["收盘"]),
                 xytext=(peak2["date"] - timedelta(days=320), peak2["收盘"] + 6),
                 fontsize=10.5, color=INK,
                 arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    last2 = jg.iloc[-1]
    ax2.annotate(f"{last2['收盘']:.0f} 美元（回撤 "
                 f"{metrics['2026年内']['伦敦银现']['较最高回撤%']}%）",
                 xy=(last2["date"], last2["收盘"]),
                 xytext=(last2["date"] - timedelta(days=400), last2["收盘"] + 16),
                 fontsize=10.5, color=INK,
                 arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for axis in (ax, ax2):
        axis.grid(axis="x", visible=False)
    finish(fig, [ax, ax2], "图04_近两年国际金银价格.png", SRC)


def chart05() -> None:
    """近两年六大品牌金饰零售价。"""
    gold_only = two_brand[two_brand["品种"] == "黄金价格"]
    fig, ax = plt.subplots(figsize=(11.2, 5.8))
    for brand in sorted(gold_only["品牌"].unique()):
        sub = gold_only[gold_only["品牌"] == brand].sort_values("日期")
        ax.plot(sub["日期"], sub["价格"], linewidth=1.7,
                color=BRAND_COLORS.get(brand, GREY), label=f"{brand}（{sub['价格'].iloc[-1]:.0f}）")
        if brand in ("周大福", "菜百", "周六福"):
            ax.scatter([sub["日期"].iloc[-1]], [sub["价格"].iloc[-1]],
                       color=BRAND_COLORS.get(brand, GREY), s=26, zorder=5)

    peak = gold_only[gold_only["品牌"] == "老庙黄金"].sort_values("日期")
    top = peak.loc[peak["价格"].idxmax()]
    ax.scatter([top["日期"]], [top["价格"]], color=RED, s=44, zorder=6)
    ax.annotate(f"{top['日期']:%Y-%m-%d} 历史高点\n老庙黄金 {top['价格']:.0f} 元/克",
                xy=(top["日期"], top["价格"]),
                xytext=(top["日期"] - timedelta(days=250), top["价格"] + 100),
                fontsize=10.5, color=INK, ha="center",
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    latest_date = gold_only["日期"].max()
    latest_prices = gold_only[gold_only["日期"] == latest_date]["价格"]
    ax.annotate(f"{latest_date:%Y-%m-%d}\n各品牌 {latest_prices.min():.0f}~{latest_prices.max():.0f} 元/克",
                xy=(latest_date, float(latest_prices.median())),
                xytext=(latest_date - timedelta(days=170), 1090),
                fontsize=10.5, color=INK, ha="center",
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    ax.set_ylim(700, 1860)
    ax.set_ylabel("元/克")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="lower right", fontsize=10.5, ncol=2)
    titles(ax, "近两年六大品牌金饰零售价：一个模子刻出来的走势",
           "周大福/周六福/老凤祥/周生生/老庙黄金/菜百，足金饰品挂牌价，近两年涨幅均超 73%")
    finish(fig, [ax], "图06_品牌金饰零售价近两年.png", SRC)


if __name__ == "__main__":
    chart01()
    chart02()
    chart03()
    chart04()
    chart05()
