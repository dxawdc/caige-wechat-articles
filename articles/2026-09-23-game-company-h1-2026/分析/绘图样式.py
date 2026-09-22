# -*- coding: utf-8 -*-
"""统一可视化设计系统：配色、字体、卡片式画布、导出。

约定：
    - 涨/增长用暖红（中国财经惯例），跌/下滑用冷绿。
    - 所有图表留出顶部标题区与底部来源注，画布纯白。
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

# ---------- 路径 ----------
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "数据")
ANA = os.path.join(BASE, "分析")
CH = os.path.join(BASE, "图表")
os.makedirs(CH, exist_ok=True)

# ---------- 配色 ----------
INK = "#16202E"        # 主文字
SUB = "#5B6776"        # 次要文字
FAINT = "#96A1AE"      # 来源注
GRID = "#EAEEF3"       # 网格
PANEL = "#F7F9FC"      # 浅底
CARD = "#FFFFFF"

BLUE = "#2F5CBF"       # 主色·深蓝
BLUE_L = "#7FA3F0"     # 主色·浅
ACCENT = "#F08A24"     # 强调·橙
UP = "#CE3B32"         # 增长（红）
UP_L = "#F0A49D"
DOWN = "#2E8B6E"       # 下滑（绿）
DOWN_L = "#9CCDBF"
PURPLE = "#7B61C9"
TEAL = "#2E9CA8"
GOLD = "#D9A422"
PINK = "#D96A9C"
NEUTRAL = "#B9C2CD"

TIER_CORE = BLUE       # 核心（游戏收入占比高）
TIER_IMP = ACCENT      # 重要
TIER_EDGE = NEUTRAL    # 边缘

FONT = "Microsoft YaHei"


def setup():
    plt.rcParams.update({
        "font.sans-serif": [FONT, "Noto Sans SC", "SimHei", "DejaVu Sans"],
        "font.family": "sans-serif",
        "axes.unicode_minus": False,
        "figure.facecolor": CARD,
        "axes.facecolor": CARD,
        "savefig.facecolor": CARD,
        "axes.edgecolor": GRID,
        "text.color": INK,
        "axes.labelcolor": SUB,
        "xtick.color": SUB,
        "ytick.color": SUB,
        "axes.titlesize": 12,
        "font.size": 10,
        "figure.dpi": 160,
    })


def canvas(w, h, title, subtitle="", source="", dpi=160, top=None, bottom=0.115,
           left=0.085, width=0.885):
    """创建带标题区/来源注的卡片画布，返回 (fig, ax) 供主图使用。"""
    fig = plt.figure(figsize=(w, h), dpi=dpi)
    if top is None:
        top = 0.90 if subtitle else 0.93
    ax = fig.add_axes([left, bottom, width, top - bottom])
    fig.text(0.045, 0.962, title, fontsize=17.5, fontweight="bold", color=INK,
             ha="left", va="top")
    if subtitle:
        fig.text(0.045, 0.912, subtitle, fontsize=10.2, color=SUB, ha="left", va="top")
    if source:
        fig.text(0.955, 0.028, source, fontsize=8, color=FAINT, ha="right", va="bottom")
    return fig, ax


def _rgb(c):
    c = matplotlib.colors.to_rgb(c)
    return c


def text_color(face):
    """按背景亮度返回可读的文字色。"""
    r, g, b = _rgb(face)
    return INK if (0.299 * r + 0.587 * g + 0.114 * b) > 0.58 else "white"


def diverging(t, neutral=(0.94, 0.955, 0.97)):
    """t∈[-1,1] → 颜色：负→绿、0→中性浅灰、正→红。"""
    import colorsys
    a = _rgb(DOWN)
    b = neutral
    c = _rgb(UP)
    if t >= 0:
        k = min(1.0, t)
        return tuple(b[i] + (c[i] - b[i]) * k for i in range(3))
    k = min(1.0, -t)
    return tuple(b[i] + (a[i] - b[i]) * k for i in range(3))


def color_band(fig, x, y, w, h, n=140, label="", lo="", mid="", hi=""):
    """在 fig 上画一条 diverging 渐变色带作为图例。x/y/w/h 为 fig 归一化坐标。"""
    from matplotlib.patches import Rectangle as _R
    for i in range(n):
        t = i / (n - 1) * 2 - 1
        fig.patches.append(_R((x + w * i / n, y), w / n * 1.02, h,
                              transform=fig.transFigure, facecolor=diverging(t),
                              edgecolor="none"))
    if label:
        fig.text(x, y + h + 0.012, label, fontsize=8.6, color=SUB, ha="left",
                 va="bottom")
    if lo:
        fig.text(x, y - 0.008, lo, fontsize=8.2, color=FAINT, ha="left", va="top")
    if mid:
        fig.text(x + w / 2, y - 0.008, mid, fontsize=8.2, color=FAINT, ha="center",
                 va="top")
    if hi:
        fig.text(x + w, y - 0.008, hi, fontsize=8.2, color=FAINT, ha="right", va="top")


def strip(ax, left=False):
    """去掉多余轴脊与刻度线，只保留极淡网格。"""
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(GRID)
    ax.tick_params(length=0, labelsize=9.5)


def grid(ax, axis="y", alpha=0.9):
    ax.grid(axis=axis, color=GRID, linewidth=1.0, alpha=alpha, zorder=0)
    ax.set_axisbelow(True)


def badge(ax, x, y, text, xytext, color=INK, fontsize=9.5, ha="left", va="center",
          arrow=True, weight="normal", bg=None):
    """带可选背景的标注。"""
    ax.annotate(
        text, xy=(x, y), xytext=xytext, textcoords="offset points",
        fontsize=fontsize, color=color, ha=ha, va=va, fontweight=weight, zorder=6,
        bbox=dict(boxstyle="round,pad=0.32", fc=bg, ec="none") if bg else None,
        arrowprops=dict(arrowstyle="-", color=color, lw=0.7, alpha=0.5,
                        shrinkA=0, shrinkB=2) if arrow else None,
    )


def save(fig, name):
    p = os.path.join(CH, name)
    fig.savefig(p, dpi=fig.dpi, facecolor=CARD)
    plt.close(fig)
    return p


# ---------- 数据读取 ----------
def rd(path):
    if not os.path.exists(path):
        print("缺文件", path)
        return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return None if v in (None, "", "-", "nan") else float(v)
    except (TypeError, ValueError):
        return None


def total(rows, k):
    return sum(num(r.get(k)) or 0 for r in rows)


def load_all():
    """一次载入所有分析所需数据。"""
    d = {}
    d["a"] = rd(os.path.join(ANA, "公司指标汇总.csv"))          # A股公司指标（宽表）
    d["tier"] = {r["代码"]: r for r in rd(os.path.join(DATA, "游戏公司_A股_分层.csv"))}
    d["hk"] = rd(os.path.join(ANA, "全口径汇总_港股.csv"))
    d["hki"] = rd(os.path.join(ANA, "港股指标汇总.csv"))
    d["gbiz"] = rd(os.path.join(DATA, "港股_游戏业务收入_手工整理.csv"))
    d["mainop"] = rd(os.path.join(DATA, "游戏公司_A股_主营构成_多期.csv"))
    d["contract"] = rd(os.path.join(DATA, "游戏公司_A股_合同负债_多期.csv"))
    d["exp"] = rd(os.path.join(DATA, "游戏公司_A股_费用明细_多期.csv"))
    core = [r for r in d["a"] if d["tier"].get(r["代码"], {}).get("层级") == "核心"]
    imp = [r for r in d["a"] if d["tier"].get(r["代码"], {}).get("层级") == "重要"]
    d["core"], d["imp"], d["main"] = core, imp, core + imp
    return d


def tier_of(d, code):
    return d["tier"].get(code, {}).get("层级", "")


def region_split(d, code, period="2026-06-30"):
    """从主营构成（MAINOP_TYPE=3 的地区口径）拆境外/合计收入，单位元。"""
    ov = tt = 0.0
    for r in d["mainop"]:
        if r.get("SECURITY_CODE") != code or r.get("MAINOP_TYPE") != "3":
            continue
        if not str(r.get("REPORT_DATE", "")).startswith(period):
            continue
        v = num(r.get("MAIN_BUSINESS_INCOME")) or 0.0
        tt += v
        nm = r.get("ITEM_NAME") or ""
        if any(k in nm for k in ("境外", "海外", "国外", "国际", "其他国家", "中国大陆以外")):
            ov += v
    return (ov, tt) if tt else (None, None)


def game_income(d, code, period="2026-06-30"):
    """主营构成中游戏相关收入合计（元），按主营类型1/2两种口径取较大者。"""
    best = 0.0
    for r in d["mainop"]:
        if r.get("SECURITY_CODE") != code:
            continue
        if not str(r.get("REPORT_DATE", "")).startswith(period):
            continue
        if r.get("MAINOP_TYPE") not in ("1", "2"):
            continue
        nm = r.get("ITEM_NAME") or ""
        if any(k in nm for k in ("游戏", "手游", "页游", "端游", "电竞")):
            best = max(best, num(r.get("MAIN_BUSINESS_INCOME")) or 0.0)
    return best or None
