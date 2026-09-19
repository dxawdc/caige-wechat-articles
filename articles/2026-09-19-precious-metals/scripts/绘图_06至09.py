# -*- coding: utf-8 -*-
"""绘制贵金属价格趋势配图（图06~图09）。"""
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

SRC = ("数据来源：上海黄金交易所官方日行情、金投网品牌金价；数据截至 2026-09-18，"
       "由「可以叫我才哥」整理")

ten_au = pd.read_csv(CLEAN / "03_上金所Au9999_近十年.csv", parse_dates=["date"])
brand = pd.read_csv(CLEAN / "06_品牌金价_近两年.csv", parse_dates=["日期"])
ratio = pd.read_csv(CLEAN / "07_金银比_近十年.csv", parse_dates=["date"])
xau = pd.read_csv(CLEAN / "01_伦敦金现_近十年.csv", parse_dates=["date"])
xag = pd.read_csv(CLEAN / "02_伦敦银现_近十年.csv", parse_dates=["date"])
metrics = json.loads((ROOT / "输出" / "统计指标.json").read_text(encoding="utf-8"))

START = pd.Timestamp("2024-09-19")


def chart06() -> None:
    """周大福零售价 vs 上金所基准价，溢价面积图。"""
    zhou = brand[(brand["品牌"] == "周大福") & (brand["品种"] == "黄金价格")].sort_values("日期")
    base = ten_au.rename(columns={"date": "日期"})[["日期", "收盘"]]
    merged = pd.merge(zhou[["日期", "价格"]], base, on="日期", how="inner")

    fig, ax = plt.subplots(figsize=(11.2, 5.6))
    ax.plot(merged["日期"], merged["价格"], color=GOLD, linewidth=2.2, label="周大福足金饰品零售价")
    ax.plot(merged["日期"], merged["收盘"], color=ACCENT, linewidth=2.0, label="上金所 Au99.99 基准价")
    ax.fill_between(merged["日期"], merged["收盘"], merged["价格"], color=GOLD, alpha=0.16,
                    label="两者差额（品牌溢价）")

    last = merged.iloc[-1]
    premium = last["价格"] - last["收盘"]
    ax.annotate(f"{last['日期']:%Y-%m-%d}\n零售 {last['价格']:.0f}，基准 {last['收盘']:.0f}\n"
                f"差额 {premium:.0f} 元/克",
                xy=(last["日期"], last["价格"]),
                xytext=(last["日期"] - timedelta(days=430), 1720),
                fontsize=10.5, color=INK, ha="center",
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    first = merged.iloc[0]
    ax.annotate(f"起点差额 {first['价格'] - first['收盘']:.0f} 元/克",
                xy=(first["日期"], first["价格"] - 40),
                xytext=(first["日期"] + timedelta(days=60), 380),
                fontsize=10.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    ax.set_ylim(300, 1900)
    ax.set_ylabel("元/克")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", fontsize=11)
    titles(ax, "买一件金饰，比金价本身贵了多少",
           "近两年周大福零售价与上金所 Au99.99 基准价的差额，平均约 294 元/克（约 34%）")
    finish(fig, [ax], "图07_品牌零售价与基准金价差额.png", SRC)


def chart07() -> None:
    """近十年金银比。"""
    fig, ax = plt.subplots(figsize=(11.2, 5.2))
    ax.plot(ratio["date"], ratio["金银比"], color=GOLD, linewidth=2.0)
    mean_value = float(ratio["金银比"].mean())
    ax.axhline(mean_value, color=GREY, linestyle="--", linewidth=1.2)
    ax.text(ratio["date"].iloc[6], mean_value + 2.2, f"近十年均值 {mean_value:.0f}",
            fontsize=10.5, color=GREY)
    low = ratio.loc[ratio["金银比"].idxmin()]
    high = ratio.loc[ratio["金银比"].idxmax()]
    latest = ratio.iloc[-1]
    ax.scatter([high["date"]], [high["金银比"]], color=GOLD, zorder=5, s=42)
    ax.annotate(f"{high['date']:%Y-%m-%d} 十年最高 {high['金银比']:.0f}",
                xy=(high["date"], high["金银比"]),
                xytext=(high["date"] - timedelta(days=520), high["金银比"] + 6),
                fontsize=10.5, color=INK, ha="center",
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    ax.scatter([low["date"]], [low["金银比"]], color=RED, zorder=5, s=42)
    ax.annotate(f"{low['date']:%Y-%m-%d} 十年最低 {low['金银比']:.0f}",
                xy=(low["date"], low["金银比"]),
                xytext=(low["date"] - timedelta(days=380), low["金银比"] + 9),
                fontsize=10.5, color=INK, ha="center",
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    ax.scatter([latest["date"]], [latest["金银比"]], color=ACCENT, zorder=5, s=42)
    ax.annotate(f"{latest['date']:%Y-%m-%d} 最新 {latest['金银比']:.0f}",
                xy=(latest["date"], latest["金银比"]),
                xytext=(latest["date"] - timedelta(days=330), latest["金银比"] - 16),
                fontsize=10.5, color=INK, ha="center",
                arrowprops=dict(arrowstyle="-", color=GREY, linewidth=0.9))
    ax.set_ylim(36, 140)
    ax.set_ylabel("金银比（黄金价格 ÷ 白银价格）")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="x", visible=False)
    titles(ax, "金银比：白银相对黄金的贵贱温度计",
           "比值越高说明白银越便宜；2026-01-27 一度低到 46，为近十年最低")
    finish(fig, [ax], "图09_近十年金银比.png", SRC)


def chart08() -> None:
    """2026 年内归一化走势。"""
    start = pd.Timestamp("2026-01-01")
    series = {}
    for label, frame, column in (("伦敦金现", xau, "收盘"), ("伦敦银现", xag, "收盘"),
                                 ("上金所Au99.99", ten_au, "收盘")):
        sub = frame[frame["date"] >= start][["date", column]].copy()
        sub = sub.rename(columns={column: label})
        sub[label] = sub[label] / sub[label].iloc[0] * 100
        series[label] = sub.set_index("date")[label]
    combined = pd.concat(series, axis=1).dropna()
    combined.columns = ["伦敦金现", "伦敦银现", "上海金 Au99.99"]

    fig, ax = plt.subplots(figsize=(11.2, 5.4))
    colors = {"伦敦金现": GOLD, "伦敦银现": SILVER, "上海金 Au99.99": ACCENT}
    for column in combined.columns:
        ax.plot(combined.index, combined[column], color=colors[column], linewidth=2.0,
                label=f"{column}（最新 {combined[column].iloc[-1]:.0f}）")
    ax.axhline(100, color="#B9C2CC", linewidth=1, linestyle=":")
    peak_date = combined["伦敦银现"].idxmax()
    ax.axvline(peak_date, color=RED, linewidth=1.0, linestyle="--", alpha=0.6)
    ax.text(peak_date, 152, f" 1 月 {peak_date.day} 日集体见顶", fontsize=10.5, color=RED)
    ax.set_ylabel("2026 年首个交易日 = 100")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m月"))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="lower left", fontsize=11)
    titles(ax, "2026 年：1 月集体冲顶，之后黄金守住、白银深跌",
           "白银较年初高点回撤 43.2%，黄金回撤 19.1%，上海金回撤 23.8%")
    finish(fig, [ax], "图05_2026年内金银走势对比.png", SRC)


def chart09() -> None:
    """品牌溢价与两年涨幅。"""
    premium = metrics["品牌溢价(品牌零售价-上金所Au99.99, 元/克)"]
    two_year = {item["品牌"]: item for item in metrics["品牌金价近两年"]}
    names = [item["品牌"] for item in premium]
    premium_values = [item["最新溢价率%"] for item in premium]
    growth_values = [two_year[name]["两年涨幅%"] for name in names]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.9),
                                  gridspec_kw={"wspace": 0.42})
    order = np.argsort(premium_values)
    ax.barh([names[i] for i in order], [premium_values[i] for i in order],
            color=[BRAND_COLORS.get(names[i], GREY) for i in order], height=0.62)
    for index, i in enumerate(order):
        ax.text(premium_values[i] + 0.6, index, f"{premium_values[i]:.1f}%",
                va="center", fontsize=10.5, color=INK)
    ax.set_xlim(0, max(premium_values) * 1.22)
    ax.set_xlabel("最新溢价率 %（零售价相对上金所基准价）")
    ax.grid(axis="y", visible=False)
    titles(ax, "今天买金饰要多付多少")

    order2 = np.argsort(growth_values)
    ax2.barh([names[i] for i in order2], [growth_values[i] for i in order2],
             color=RED, alpha=0.82, height=0.62)
    for index, i in enumerate(order2):
        ax2.text(growth_values[i] + 0.6, index, f"{growth_values[i]:.1f}%",
                 va="center", fontsize=10.5, color=INK)
    ax2.set_xlim(0, max(growth_values) * 1.22)
    ax2.set_xlabel("近两年涨幅 %（2024-09-19 起）")
    ax2.grid(axis="y", visible=False)
    titles(ax2, "同一克金饰，两年涨了多少")
    fig.subplots_adjust(bottom=0.20)
    finish(fig, [ax, ax2], "图08_品牌溢价与两年涨幅.png", SRC)


if __name__ == "__main__":
    chart06()
    chart07()
    chart08()
    chart09()
