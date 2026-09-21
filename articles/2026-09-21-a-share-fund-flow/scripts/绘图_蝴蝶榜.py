# -*- coding: utf-8 -*-
"""v1.2.0 | 2026-09-21 | 镜像双向榜单（蝴蝶图）：主力净流入TOP10 vs 净流出TOP10。

- 排名语义清晰（名次即行序），无瀑布图"任意排序连接线"的伪流程暗示；
- 左右同刻度（量程按当日数据自适应），流入/流出强弱可直接对称比较；
- 名字放条形上方空隙（不占中缝），数值放条端，移动端可读性好。

v1.2.0：交易日与量程不再硬编码——日期取自采集元数据，刻度按当日最大净额自适应。
"""
from __future__ import annotations
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import _common as C

C.add_fonts(matplotlib)
MONO = "Consolas"
RED, GREEN = "#D93025", "#0E8F63"
INK, MUTED, LINE = "#2B2B2B", "#8A8A8A", "#E3E3E3"


def main():
    df = C.load_market()
    tin = df.nlargest(10, "main_net").reset_index(drop=True)
    tout = df.nsmallest(10, "main_net").reset_index(drop=True)

    valsL = tout["main_net"].to_numpy() / 1e8
    valsR = tin["main_net"].to_numpy() / 1e8
    # 量程自适应：左右同刻度，向上取到 5 或 10 的整数刻度
    peak = max(abs(valsL).max(), abs(valsR).max())
    lim = math.ceil(peak / 5.0) * 5.0

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 7.2), dpi=150,
                                   gridspec_kw={"wspace": 0.08})
    ys = np.arange(10)
    axL.barh(ys, valsL, height=0.56, color=GREEN, zorder=3)
    axR.barh(ys, valsR, height=0.56, color=RED, zorder=3)

    for i in range(10):
        axL.text(-0.4, i + 0.40, f"{i + 1}. {tout['name'][i]}", ha="right",
                 va="bottom", fontsize=10.5, color=INK, fontweight="bold")
        axL.text(valsL[i] - 0.5, i - 0.02, f"{valsL[i]:+.1f}", ha="right",
                 va="center", fontsize=10.5, color=GREEN, fontweight="bold",
                 fontfamily=MONO)
        pct = tout["pct"][i]
        axL.text(valsL[i] - 0.5, i - 0.30, "—" if np.isnan(pct) else f"{pct:+.1f}%",
                 ha="right", va="center", fontsize=7.5, color=MUTED, fontfamily=MONO)

        axR.text(0.4, i + 0.40, f"{i + 1}. {tin['name'][i]}", ha="left",
                 va="bottom", fontsize=10.5, color=INK, fontweight="bold")
        axR.text(valsR[i] + 0.5, i - 0.02, f"{valsR[i]:+.1f}", ha="left",
                 va="center", fontsize=10.5, color=RED, fontweight="bold",
                 fontfamily=MONO)
        pct = tin["pct"][i]
        axR.text(valsR[i] + 0.5, i - 0.30, "—" if np.isnan(pct) else f"{pct:+.1f}%",
                 ha="left", va="center", fontsize=7.5, color=MUTED, fontfamily=MONO)

    for ax, xlim in ((axL, (-lim, 0)), (axR, (0, lim))):
        ax.set_xlim(*xlim)
        ax.set_ylim(9.75, -0.75)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
    axL.axvline(0, color=LINE, lw=1.0, zorder=1)
    axR.axvline(0, color=LINE, lw=1.0, zorder=1)

    sum_in = tin["main_net"].sum() / 1e8
    sum_out = tout["main_net"].sum() / 1e8
    axL.set_title(f"▼ 净流出 TOP10（合计 {sum_out:+.1f}亿）", color=GREEN,
                  fontsize=12.5, fontweight="bold", pad=14)
    axR.set_title(f"▲ 净流入 TOP10（合计 {sum_in:+.1f}亿）", color=RED,
                  fontsize=12.5, fontweight="bold", pad=14)

    fig.suptitle(f"A股主力资金净额 · 镜像双榜（{C.DATE} 收盘）", x=0.02,
                 ha="left", fontsize=15, fontweight="bold", color=INK)
    fig.text(0.02, 0.930,
             f"左右同刻度（±{lim:.0f}亿元）· 主力净额 = 超大单 + 大单 · 单位：亿元 · 数据：东方财富",
             fontsize=9, color=MUTED)
    fig.text(0.02, 0.015,
             "注：主力净额为当日买卖相抵后的净额，非成交量；大字为净额（亿元），小字为当日涨跌幅。",
             fontsize=8, color=MUTED)
    fig.subplots_adjust(top=0.86, bottom=0.07, left=0.03, right=0.97)
    out = os.path.join(C.OUT_DIR, "蝴蝶榜_净额TOP10.png")
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    print(f"[done] {out}  净流入TOP10合计 {sum_in:+.1f}亿  净流出TOP10合计 {sum_out:+.1f}亿")


if __name__ == "__main__":
    main()
