# -*- coding: utf-8 -*-
"""近十年国际金银价格动态曲线图（GIF）。

- 黄金左轴、白银右轴，时间轴从 2016-09-19 推进到 2026-09-18；
- 逐帧重绘同一张固定版式的图，静态元素（标题、脚注、坐标轴）只画一次，避免抖动；
- 自行量化调色板并做帧间优化，控制 GIF 体积，另存末帧 PNG 作为静态兜底。
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from 图表风格 import (BRAND, CHARTS, CLEAN, GOLD, GREY, INK, RED, SILVER, setup)

setup()

SRC = ("数据来源：新浪财经国际期货日线（伦敦金现 / 伦敦银现），2016-09-19 至 2026-09-18，"
       "由「可以叫我才哥」整理")
SILVER_TEXT = "#6F7B8A"

FIG_W, FIG_H, DPI = 10.6, 5.3, 100
N_FRAMES = 110
FRAME_MS = 75
HOLD_MS = 1600
PALETTE_COLORS = 128

GIF_PATH = CHARTS / "动图01_近十年金银价格走势.gif"
PNG_PATH = CHARTS / "动图01_近十年金银价格走势_末帧.png"

金 = pd.read_csv(CLEAN / "01_伦敦金现_近十年.csv", parse_dates=["date"])[["date", "收盘"]]
金 = 金.rename(columns={"收盘": "gold"})
银 = pd.read_csv(CLEAN / "02_伦敦银现_近十年.csv", parse_dates=["date"])[["date", "收盘"]]
银 = 银.rename(columns={"收盘": "silver"})
frame = 金.merge(银, on="date", how="inner").sort_values("date").reset_index(drop=True)

dates = frame["date"].to_numpy()
gold = frame["gold"].to_numpy(dtype=float)
silver = frame["silver"].to_numpy(dtype=float)
count = len(frame)

X0, X1 = dates[0], dates[-1]
XSPAN = mdates.date2num(X1) - mdates.date2num(X0)
GOLD_LO, GOLD_HI = float(gold.min()) * 0.92, float(gold.max()) * 1.16
SILV_LO, SILV_HI = 0.0, float(silver.max()) * 1.22
PEAK = int(np.argmax(gold))

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
ax2 = ax.twinx()
fig.subplots_adjust(left=0.074, right=0.926, top=0.838, bottom=0.15)

fig.text(0.012, 0.955, "近十年国际金银价格：从 2016 走到 2026",
         fontsize=17, fontweight="bold", color=INK, ha="left", va="top")
fig.text(0.012, 0.9, "黄金看左轴、白银看右轴（美元/盎司）；时间轴 2016-09-19 → 2026-09-18 逐日推进",
         fontsize=10.5, color=GREY, ha="left", va="top")
fig.text(0.012, 0.022, SRC, fontsize=9.5, color=GREY, ha="left")
fig.text(0.988, 0.022, BRAND, fontsize=10.5, color=GREY, ha="right", fontweight="bold")

ax.set_xlim(mdates.date2num(X0) - 12, mdates.date2num(X1) + 12)
ax.set_ylim(GOLD_LO, GOLD_HI)
ax2.set_ylim(SILV_LO, SILV_HI)
ax.set_ylabel("伦敦金现（美元/盎司）", color=GOLD)
ax2.set_ylabel("伦敦银现（美元/盎司）", color=SILVER_TEXT)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.grid(axis="x", visible=False)
ax2.grid(False)
for each in (ax, ax2):
    each.spines["top"].set_visible(False)
    each.tick_params(length=0)
ax.spines["right"].set_visible(False)
ax2.spines["left"].set_visible(False)

dynamic: list = []


def clear_dynamic() -> None:
    while dynamic:
        artist = dynamic.pop()
        try:
            artist.remove()
        except (ValueError, AttributeError):
            pass


def draw(upto: int) -> None:
    """绘制第 upto 个交易日为止的走势。"""
    stop = upto + 1
    xv, gv, sv = dates[:stop], gold[:stop], silver[:stop]

    dynamic.append(ax.fill_between(xv, gv, GOLD_LO, color=GOLD, alpha=0.10, linewidth=0))
    dynamic.append(ax.plot(xv, gv, color=GOLD, linewidth=2.1, zorder=4)[0])
    dynamic.append(ax2.plot(xv, sv, color=SILVER, linewidth=1.7, zorder=3)[0])
    dynamic.append(ax.axvline(xv[-1], color=GREY, linewidth=1.0,
                              linestyle=(0, (4, 3)), zorder=2, alpha=0.75))
    dynamic.append(ax.scatter([xv[-1]], [gv[-1]], color=GOLD, s=30, zorder=6))
    dynamic.append(ax2.scatter([xv[-1]], [sv[-1]], color=SILVER, s=26, zorder=6))

    gold_pct = (gv[-1] / gold[0] - 1) * 100
    silver_pct = (sv[-1] / silver[0] - 1) * 100
    dynamic.append(ax.text(0.014, 0.985, f"伦敦金现 {gv[-1]:,.0f} 美元/盎司",
                           transform=ax.transAxes, fontsize=12, fontweight="bold",
                           color=GOLD, ha="left", va="top"))
    dynamic.append(ax.text(0.014, 0.915, f"较 2016-09-19 {gold_pct:+.1f}%",
                           transform=ax.transAxes, fontsize=10.5, color=GOLD,
                           ha="left", va="top"))
    dynamic.append(ax.text(0.014, 0.845, f"伦敦银现 {sv[-1]:,.1f} 美元/盎司",
                           transform=ax.transAxes, fontsize=12, fontweight="bold",
                           color=SILVER_TEXT, ha="left", va="top"))
    dynamic.append(ax.text(0.014, 0.775, f"较 2016-09-19 {silver_pct:+.1f}%",
                           transform=ax.transAxes, fontsize=10.5, color=SILVER_TEXT,
                           ha="left", va="top"))

    fraction = (mdates.date2num(xv[-1]) - mdates.date2num(X0)) / XSPAN
    align = "right" if fraction > 0.88 else ("left" if fraction < 0.06 else "center")
    dynamic.append(ax.text(min(max(fraction, 0.0), 1.0), -0.058,
                           f"{pd.Timestamp(xv[-1]):%Y-%m-%d}",
                           transform=ax.transAxes, fontsize=11, fontweight="bold",
                           color=INK, ha=align, va="top"))

    if upto >= PEAK:
        dynamic.append(ax.scatter([dates[PEAK]], [gold[PEAK]], color=RED, s=40, zorder=7))
        dynamic.append(ax.annotate(
            f"{pd.Timestamp(dates[PEAK]):%Y-%m-%d} 见顶 {gold[PEAK]:,.0f} 美元/盎司",
            xy=(dates[PEAK], gold[PEAK]), xytext=(dates[PEAK], gold[PEAK] * 1.035),
            fontsize=10.5, color=INK, ha="right", va="bottom"))


indices = sorted(set(np.round(np.linspace(0, count - 1, N_FRAMES)).astype(int).tolist()))
frames: list[Image.Image] = []
for position, index in enumerate(indices):
    clear_dynamic()
    draw(int(index))
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=DPI)
    buffer.seek(0)
    with Image.open(buffer) as shot:
        frames.append(shot.convert("RGB"))
    if position % 25 == 0:
        print(f"渲染 {position + 1}/{len(indices)}", flush=True)

width, height = frames[0].size
montage = Image.new("RGB", (width, height * 3))
for slot, frame_index in enumerate((0, len(frames) // 2, len(frames) - 1)):
    montage.paste(frames[frame_index], (0, height * slot))
palette = montage.quantize(colors=PALETTE_COLORS, method=Image.Quantize.MEDIANCUT,
                          dither=Image.Dither.NONE)
quantized = [shot.quantize(palette=palette, dither=Image.Dither.NONE) for shot in frames]

durations = [FRAME_MS] * (len(quantized) - 1) + [HOLD_MS]
quantized[0].save(GIF_PATH, save_all=True, append_images=quantized[1:],
                  duration=durations, loop=0, optimize=True, disposal=2)
fig.savefig(PNG_PATH, dpi=130)
plt.close(fig)

print(f"已生成 {GIF_PATH.name}：{width}×{height}，{len(quantized)} 帧，"
      f"{GIF_PATH.stat().st_size / 1048576:.2f} MB，"
      f"总时长 {sum(durations) / 1000:.1f} 秒", flush=True)
print(f"已生成 {PNG_PATH.name}", flush=True)
