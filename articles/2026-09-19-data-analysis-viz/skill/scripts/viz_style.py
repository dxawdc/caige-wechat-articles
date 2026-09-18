# -*- coding: utf-8 -*-
"""vis_style —— 统一的中文可视化样式与导出工具。

用法：
    from viz_style import setup_style, COLORS, finish, diverging

    setup_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, y)
    finish(fig, "结论式标题", df, metrics={"峰值": 123})

约定（可见 references/05-可视化设计原则.md 第 5 节）：
- 中文字体显式设置，避免方框；
- 去掉上、右轴线，保留浅色横向网格；
- 分类数据用不同色相，连续数据用单一色相明度渐变，正负值用背离配色；
- 导出 PNG + SVG，并把支撑数据导出为 CSV；
- 图下角标注数据来源与品牌。
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------- 基础配置

#: 分类型数据主色板（不同色相，区分度优先）
COLORS = [
    "#188568",
    "#4878B7",
    "#E59B42",
    "#9566AA",
    "#CB6677",
    "#5D9FAD",
]

#: 序列型配色（单一色相明度渐变，深 = 大值）
SEQUENTIAL = ["#E8F3EF", "#B6DACE", "#7FBDA9", "#4C9B82", "#188568", "#0B4E3C"]

#: 背离型配色（正负值：蓝 — 白 — 红）
DIVERGING = ["#2F6DB5", "#8FB4DC", "#F2F2F2", "#E39A96", "#C0392B"]

#: 中国习惯：涨红跌绿
UP_COLOR = "#C0392B"
DOWN_COLOR = "#188568"

_FALLBACK_FONTS = [
    "Microsoft YaHei",
    "Noto Sans CJK SC",
    "Source Han Sans SC",
    "SimHei",
    "PingFang SC",
    "WenQuanYi Zen Hei",
]


def find_cjk_font() -> str | None:
    """按优先级寻找可用的中文字体，返回字体名。"""
    for name in _FALLBACK_FONTS:
        try:
            path = font_manager.findfont(name, fallback_to_default=False)
        except Exception:  # noqa: BLE001
            continue
        if path:
            return font_manager.FontProperties(fname=path).get_name()
    return None


def setup_style(font_size: int = 12, figsize: tuple[float, float] = (8.0, 5.0)):
    """设置全局样式。返回选中的中文字体名（可能为 None，此时需自备字体）。"""
    font_name = find_cjk_font()
    params = {
        "axes.unicode_minus": False,   # 负号不要渲染成方框
        "figure.dpi": 150,
        "savefig.dpi": 170,
        "svg.fonttype": "path",        # SVG 中把文字转路径，避免缺字体
        "axes.titlesize": 15,
        "axes.labelsize": font_size,
        "xtick.labelsize": font_size - 1,
        "ytick.labelsize": font_size - 1,
        "legend.fontsize": font_size - 1,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.7,
        "grid.linestyle": "-",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "font.size": font_size,
    }
    if font_name:
        params["font.sans-serif"] = [font_name]
        params["font.family"] = "sans-serif"
    plt.rcParams.update(params)
    return font_name


def diverging_cmap(name: str = "viz_diverging") -> LinearSegmentedColormap:
    """正负值用背离配色。"""
    return LinearSegmentedColormap.from_list(name, DIVERGING)


def sequential_cmap(name: str = "viz_sequential") -> LinearSegmentedColormap:
    """连续数值用单一色相明度渐变。"""
    return LinearSegmentedColormap.from_list(name, SEQUENTIAL)


def color_by_change(value: float) -> str:
    """按中国习惯给涨跌上色。"""
    return UP_COLOR if value >= 0 else DOWN_COLOR


# ---------------------------------------------------------------- 导出


def finish(
    fig,
    title: str,
    df: pd.DataFrame | dict[str, pd.DataFrame] | None = None,
    *,
    out_dir: str | Path = "outputs",
    stem: str | None = None,
    metrics: dict | None = None,
    source_note: str = "模拟数据 · 可以叫我才哥",
    formats: tuple[str, ...] = ("png", "svg"),
):
    """统一收尾：加结论式标题、数据来源署名、导出图片与支撑数据。

    参数
    ----
    title : 结论式标题（写结论，不要只写字段名）
    df    : 支撑该图的明细或汇总表；可传单个 DataFrame 或 {名称: DataFrame}
    stem  : 输出文件名主干，默认 `图_<序号>` 形式需自行传入
    metrics : 需要随图保存的关键读数，写入同名 json
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = stem or "figure"

    # 标题：写在图上方，左对齐，代表"这张图在说什么结论"
    fig.suptitle(title, x=0.06, ha="left", fontsize=14, fontweight="bold", color="#1C493A")
    fig.text(0.06, 0.012, source_note, fontsize=9, color="#78858F")
    try:
        fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    except Exception:  # noqa: BLE001
        pass

    written = []
    for fmt in formats:
        path = out / f"{stem}.{fmt}"
        fig.savefig(path, format=fmt, bbox_inches="tight")
        written.append(str(path))
    plt.close(fig)

    if df is not None:
        tables = df if isinstance(df, dict) else {"data": df}
        for key, table in tables.items():
            path = out / f"{stem}_{key}.csv"
            table.to_csv(path, index=False, encoding="utf-8-sig")
            written.append(str(path))

    if metrics:
        path = out / f"{stem}_metrics.json"
        path.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2, default=_jsonable),
            encoding="utf-8",
        )
        written.append(str(path))

    return written


def _jsonable(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return str(value)


def annotate_extremes(ax, x, y, *, top_n: int = 1, color: str = "#C0392B", fmt: str = "{:.0f}"):
    """标注极值点，帮助读者快速定位重点（有效性：突出层次）。"""
    y = np.asarray(y, dtype=float)
    x = list(x)
    order = np.argsort(y)[::-1][:top_n]
    for rank, idx in enumerate(order):
        ax.annotate(
            fmt.format(y[idx]),
            xy=(x[idx], y[idx]),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=10,
            color=color,
            fontweight="bold" if rank == 0 else "normal",
        )


def add_leader_line(ax, xy, text, *, xytext=None, color: str = "#C0392B"):
    """引线标注关键点。"""
    ax.annotate(
        text,
        xy=xy,
        xytext=xytext or xy,
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color=color, lw=1.2, shrinkA=2, shrinkB=2),
        fontsize=10,
        color=color,
        ha="left",
    )


if __name__ == "__main__":
    name = setup_style()
    print("selected CJK font:", name)
    print("colors:", COLORS)
