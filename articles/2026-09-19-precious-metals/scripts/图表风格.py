# -*- coding: utf-8 -*-
"""贵金属价格趋势配图：统一风格工具。"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
CHARTS = ROOT / "配图"
CHARTS.mkdir(exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT = r"C:\Windows\Fonts\msyh.ttc"

GOLD = "#C8961E"
GOLD_LIGHT = "#E8C583"
SILVER = "#8B97A6"
SILVER_LIGHT = "#C9D2DC"
RED = "#D6453D"
GREEN = "#2E9E5B"
INK = "#1F2A37"
GREY = "#78858F"
GRID = "#E4E8EC"
BG = "#FFFFFF"
ACCENT = "#177F82"
BRAND = "可以叫我才哥"

BRAND_COLORS = {
    "周大福": "#C8961E",
    "老凤祥": "#D6453D",
    "周生生": "#177F82",
    "老庙黄金": "#7A5AF8",
    "周六福": "#2E9E5B",
    "菜百": "#8B97A6",
}


def setup() -> None:
    for path in (FONT, FONT_BOLD):
        font_manager.fontManager.addfont(path)
    plt.rcParams.update({
        "font.family": "Microsoft YaHei",
        "font.sans-serif": ["Microsoft YaHei"],
        "axes.unicode_minus": False,
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": GREY,
        "ytick.color": GREY,
        "axes.titlesize": 17,
        "axes.titleweight": "bold",
        "font.size": 11.5,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.9,
        "legend.frameon": False,
        "figure.dpi": 110,
    })


def titles(ax, title: str, subtitle: str = "") -> None:
    ax.set_title(title, loc="left", pad=34 if subtitle else 8, color=INK)
    if subtitle:
        ax.text(0, 1.025, subtitle, transform=ax.transAxes, fontsize=10.5,
                color=GREY, va="bottom")


def finish(fig, ax_list, filename: str, source: str) -> Path:
    fig.text(0.012, 0.012, source, fontsize=9.5, color=GREY, ha="left")
    fig.text(0.988, 0.012, BRAND, fontsize=10.5, color=GREY, ha="right",
             fontweight="bold")
    for ax in ax_list:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(length=0)
    path = CHARTS / filename
    fig.savefig(path, bbox_inches="tight", pad_inches=0.28)
    plt.close(fig)
    print(f"已生成 {path.name}", flush=True)
    return path
