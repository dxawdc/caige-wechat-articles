# -*- coding: utf-8 -*-
"""提取文章叙事需要的关键节点数据。"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
brand = pd.read_csv(ROOT / "data" / "clean" / "06_品牌金价_近两年.csv", parse_dates=["日期"])
au = pd.read_csv(ROOT / "data" / "clean" / "03_上金所Au9999_近十年.csv", parse_dates=["date"])
xau = pd.read_csv(ROOT / "data" / "clean" / "01_伦敦金现_近十年.csv", parse_dates=["date"])
xag = pd.read_csv(ROOT / "data" / "clean" / "02_伦敦银现_近十年.csv", parse_dates=["date"])

lines = []
zhou = brand[(brand["品牌"] == "周大福") & (brand["品种"] == "黄金价格")].sort_values("日期")

# 周大福季度末节点
for quarter_end, label in (("2024-12-31", "2024年末"), ("2025-03-31", "2025Q1末"),
                           ("2025-06-30", "2025Q2末"), ("2025-09-30", "2025Q3末"),
                           ("2025-12-31", "2025年末"), ("2026-03-31", "2026Q1末"),
                           ("2026-06-30", "2026Q2末")):
    sub = zhou[zhou["日期"] <= quarter_end]
    if len(sub):
        row = sub.iloc[-1]
        lines.append(f"周大福 {label}（{row['日期']:%Y-%m-%d}）：{row['价格']:.0f} 元/克")

peak = zhou.loc[zhou["价格"].idxmax()]
lines.append(f"周大福 最高：{peak['日期']:%Y-%m-%d} {peak['价格']:.0f} 元/克")
after = zhou[zhou["日期"] > peak["日期"]]
low = after.loc[after["价格"].idxmin()]
lines.append(f"周大福 顶点后最低：{low['日期']:%Y-%m-%d} {low['价格']:.0f} 元/克"
             f"（较顶点 {(low['价格'] / peak['价格'] - 1) * 100:.1f}%）")
lines.append(f"周大福 最新：{zhou['日期'].max():%Y-%m-%d} {zhou['价格'].iloc[-1]:.0f} 元/克")

# 2026 年 6 月低点对照
for label, frame, column in (("伦敦金现", xau, "收盘"), ("伦敦银现", xag, "收盘")):
    sub = frame[(frame["date"] >= "2026-01-01") & (frame["date"] <= "2026-09-18")].set_index("date")[column]
    low_point = sub.idxmin()
    lines.append(f"{label} 2026 年内最低：{low_point:%Y-%m-%d} {sub.min():.2f}")

# 上金所关键点
au_2y = au[au["date"] >= "2024-09-19"]
lines.append(f"上金所 Au99.99 起点：{au_2y['date'].min():%Y-%m-%d} {au_2y['收盘'].iloc[0]:.2f}")
lines.append(f"上金所 Au99.99 最新：{au_2y['date'].max():%Y-%m-%d} {au_2y['收盘'].iloc[-1]:.2f}")

# 首破千元日期（上金所）
thousand = au[au["收盘"] >= 1000]
if len(thousand):
    lines.append(f"上金所 Au99.99 首次收于 1000 元/克上方：{thousand['date'].min():%Y-%m-%d} "
                 f"{thousand['收盘'].iloc[0]:.2f}")
first_800 = au[au["收盘"] >= 800]
first_900 = au[au["收盘"] >= 900]
lines.append(f"上金所 Au99.99 首次收于 800 元上方：{first_800['date'].min():%Y-%m-%d}")
lines.append(f"上金所 Au99.99 首次收于 900 元上方：{first_900['date'].min():%Y-%m-%d}")

zhou_1000 = zhou[zhou["价格"] >= 1000]
zhou_1500 = zhou[zhou["价格"] >= 1500]
lines.append(f"周大福 首次报 1000 元/克：{zhou_1000['日期'].min():%Y-%m-%d} "
             f"{zhou_1000['价格'].iloc[0]:.0f}")
lines.append(f"周大福 首次报 1500 元/克：{zhou_1500['日期'].min():%Y-%m-%d} "
             f"{zhou_1500['价格'].iloc[0]:.0f}")

# 十年前起点
ten_start = au[au["date"] >= "2016-09-19"]
lines.append(f"上金所 近十年起点：{ten_start['date'].min():%Y-%m-%d} {ten_start['收盘'].iloc[0]:.2f} 元/克")

out = ROOT / "输出" / "叙事关键点.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print(out)
