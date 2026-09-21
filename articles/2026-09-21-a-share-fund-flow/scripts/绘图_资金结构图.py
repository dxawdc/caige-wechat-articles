# -*- coding: utf-8 -*-
"""v1.4.0 | 2026-09-21 | 资金流结构系列图。

五张图，围绕一个此前没用上的维度——**四档资金流**（超大单/大单/中单/小单）：
1. 四档总览：全市场四档净额 + 主力/中小额两档的零和关系
2. 个股四档结构：净额榜两头的头部个股，四档各自在买还是在卖
3. 全天资金节奏：每分钟增量 + 累计曲线，看钱在什么时候进场
4. 市值分层：按总市值分五档的资金流分化
5. 涨停股结构：当日涨停股的主力/超大单/小单结构

v1.4.0 重点：原先标题与注释里的统计值（分时段增额、涨停家数、微盘股数量、
代表性个股数值等）全部改为按当日数据动态计算——换一天数据直接可复用，
不会出现"图是新数据、标题还是旧数字"的问题。

配色约定：方向用红/绿（A股习惯），档位用色相区分。
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import _common as C

C.add_fonts(matplotlib)
RED, GREEN = "#C93A3C", "#12855E"
INK, MUTED = "#26282B", "#9B9B97"
GRID = "#EDEDE8"
DATE = C.DATE
# 2026-09-21：clist 接口被 IP 级限流，改用「数据中心报表 + 腾讯行情」拼装全市场数据，
# 其中「中单」「小单」无法分别取得（四档净额恒为零和，故 m_net 列承载两者合计）。
# 展示改为三档：超大单、大单、中小单合计——是精确推导值，不是近似。
TIER_COLOR = {"超大单": "#C0392B", "大单": "#E59866", "中小单": "#16A085"}
TIERS = ["超大单", "大单", "中小单"]
COL_OF = {"超大单": "xl_net", "大单": "l_net", "中小单": "m_net"}


def yi(v):
    return v / 1e8


def _out(name):
    return os.path.join(C.OUT_DIR, name)


# ---------------------------------------------------------------- 图1 四档总览
def tier_overview(df: pd.DataFrame):
    vals = [yi(df[COL_OF[t]].sum()) for t in TIERS]
    main_sum, ret_sum = vals[0] + vals[1], vals[2]
    vmax, vmin = max(vals), min(vals)
    pad = max((vmax - vmin) * 0.60, 20.0)

    fig, ax = plt.subplots(figsize=(10.8, 5.6), dpi=150)
    ys = np.arange(len(TIERS))[::-1]
    for y, t, v in zip(ys, TIERS, vals):
        c = TIER_COLOR[t]
        ax.barh(y, v, height=0.5, color=c, zorder=3)
        span = max(abs(x) for x in vals) or 1.0
        if v >= 0:
            ax.text(v + pad * 0.03, y, f"{v:+.1f} 亿", va="center", ha="left",
                    fontsize=13, fontweight="bold", color=c, zorder=6)
        elif abs(v) >= span * 0.20:            # 柱体够宽：白字压在柱内
            ax.text(v / 2, y, f"{v:+.1f} 亿", va="center", ha="center",
                    fontsize=13, fontweight="bold", color="white", zorder=6)
        else:                                   # 柱体过窄：文字移到柱外，避免被压住
            ax.text(v - pad * 0.03, y, f"{v:+.1f} 亿", va="center", ha="right",
                    fontsize=13, fontweight="bold", color=c, zorder=6)
    ax.axvline(0, color="#444", lw=1.0, zorder=2)

    def bracket(y0, y1, x, outward, label, color):
        ax.plot([x, x], [y0, y1], color=color, lw=2.0, zorder=5)
        for yy in (y0, y1):
            ax.plot([x, x + outward], [yy, yy], color=color, lw=2.0, zorder=5)
        ax.text(x + outward * 1.9, (y0 + y1) / 2, label, va="center",
                ha="left" if outward > 0 else "right",
                fontsize=12.5, fontweight="bold", color=color, zorder=5)

    x_right = vmax + pad * 0.42
    x_left = vmin - pad * 0.42
    bracket(ys[0] + 0.22, ys[1] - 0.22, x_right, pad * 0.06,
            f"超大单+大单\n{main_sum:+.1f} 亿", RED)
    bracket(ys[2] + 0.16, ys[2] - 0.16, x_left, -pad * 0.06,
            f"中小单合计\n{ret_sum:+.1f} 亿", GREEN)

    xlim = (x_left - pad * 0.60, x_right + pad * 0.95)
    ax.text(xlim[0] + pad * 0.02, len(TIERS) - 0.22, "净卖出 ←", fontsize=10.5,
            color=MUTED, va="center")
    ax.text(xlim[1] - pad * 0.02, len(TIERS) - 0.22, "→ 净买入", fontsize=10.5,
            color=MUTED, va="center", ha="right")
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.8, len(TIERS) - 0.02)
    ax.set_yticks(ys)
    ax.set_yticklabels(TIERS, fontsize=13.5, fontweight="bold", color=INK)
    ax.tick_params(axis="y", length=0)
    tick = round(abs(vmax) / 4, -int(np.floor(np.log10(max(abs(vmax), 1)))) + 1) or 50
    ax.set_xticks([-4 * tick, -2 * tick, 0, 2 * tick, 4 * tick])
    ax.set_xticklabels([f"{v:+.0f}".replace("+0", "0") if v == 0 else f"{v:.0f}"
                        for v in [-4 * tick, -2 * tick, 0, 2 * tick, 4 * tick]],
                       fontsize=10, color=MUTED)
    ax.set_xlabel("净额（亿元）", fontsize=11, color=MUTED)
    ax.grid(axis="x", linestyle="-", lw=0.5, color=GRID, zorder=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(f"资金流是一笔零和交易：超大单+大单 {main_sum:+.1f} 亿，"
                 f"中小单合计 {ret_sum:+.1f} 亿（{DATE}）",
                 fontsize=14, fontweight="bold", color=INK, loc="left", pad=18)
    fig.text(0.012, 0.015,
             "口径：超大单 + 大单记作主力，其余记作中小额；四档净额之和恒为 0。"
             "数据：东方财富数据中心 + 腾讯行情",
             fontsize=8.6, color=MUTED)
    fig.tight_layout(rect=[0, 0.035, 1, 1])
    fig.savefig(_out("四档总览_零和对手盘.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[done] 四档总览  超大+大 {main_sum:+.1f} / 中+小 {ret_sum:+.1f}")


# ------------------------------------------------------- 图2 个股四档结构指纹
def tier_fingerprint(df: pd.DataFrame, n=5):
    rows = pd.concat([df.nlargest(n, "main_net"), df.nsmallest(n, "main_net")])
    peak = max(abs(yi(r[COL_OF[t]])) for _, r in rows.iterrows() for t in TIERS)
    XMAX = float(np.ceil(peak / 10) * 10)
    XRES = XMAX * 1.16

    fig, ax = plt.subplots(figsize=(11.8, 7.4), dpi=150)
    names, ypos = [], []
    for i, (_, r) in enumerate(rows.iterrows()):
        y = len(rows) - 1 - i
        names.append(r["name"])
        ypos.append(y)
        pos_c = neg_c = 0.0
        for t in TIERS:
            v = yi(r[COL_OF[t]])
            if abs(v) < 1e-9:
                continue
            if v >= 0:
                ax.barh(y, v, left=pos_c, height=0.54, color=TIER_COLOR[t], zorder=3)
                pos_c += v
            else:
                ax.barh(y, v, left=neg_c, height=0.54, color=TIER_COLOR[t], zorder=3)
                neg_c += v
        m = yi(r["main_net"])
        ax.text(XRES, y, f"{m:+.1f} 亿", va="center", ha="left", fontsize=10.8,
                fontweight="bold", color=RED if m >= 0 else GREEN, zorder=5)
        ax.text(XRES + XMAX * 0.36, y, f"{r['pct']:+.1f}%", va="center", ha="left",
                fontsize=10.2, color=MUTED, zorder=5)

    ax.axvline(0, color="#444", lw=1.0, zorder=4)
    ax.plot([-XMAX - XMAX * 0.19, XRES + XMAX * 0.60], [n - 0.5, n - 0.5],
            color="#D8D8D4", lw=1.0, ls=(0, (5, 4)), zorder=2)
    ax.text(XRES, len(rows) - 0.28, "主力净额", ha="left", va="center",
            fontsize=10, color=MUTED)
    ax.text(XRES + XMAX * 0.36, len(rows) - 0.28, "涨跌幅", ha="left", va="center",
            fontsize=10, color=MUTED)

    handles = [Rectangle((0, 0), 1, 1, color=TIER_COLOR[t]) for t in TIERS]
    ax.legend(handles, TIERS, loc="upper center", bbox_to_anchor=(0.38, -0.135),
              ncol=3, fontsize=10.5, frameon=False)
    ax.set_xlim(-XMAX * 1.19, XRES + XMAX * 0.60)
    ax.set_ylim(-0.75, len(rows) + 0.15)
    ax.set_yticks(ypos)
    ax.set_yticklabels(names, fontsize=11.8, fontweight="bold", color=INK)
    for lab, y in zip(ax.get_yticklabels(), ypos):
        lab.set_color(RED if y >= n else GREEN)
    step = XMAX / 2 if XMAX <= 30 else XMAX / 3
    ticks = [v for v in np.arange(-XMAX, XMAX + 1, step)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{v:+.0f}" if v else "0" for v in ticks],
                       fontsize=10, color=MUTED)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("各档净额（亿元）· 左侧 = 该档净卖出，右侧 = 净买入；四档之和恒为 0",
                  fontsize=10.6, color=MUTED, labelpad=8)
    ax.grid(axis="x", linestyle="-", lw=0.5, color=GRID, zorder=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(f"同一只票，大额与小额资金的方向正好相反（{DATE}）",
                 fontsize=14, fontweight="bold", color=INK, loc="left", pad=16)

    top1 = rows.iloc[0]
    bot1 = rows.iloc[-1]
    fig.text(0.012, 0.012,
             f"名称红色为净流入 TOP{n}、绿色为净流出 TOP{n}；颜色代表档位，位置代表方向。"
             f"{top1['name']} 超大单 {yi(top1['xl_net']):+.1f} 亿、中小单 "
             f"{yi(top1['m_net']):+.1f} 亿；"
             f"{bot1['name']} 中小单 {yi(bot1['m_net']):+.1f} 亿。数据：东方财富 + 腾讯行情",
             fontsize=8.6, color=MUTED)
    fig.tight_layout(rect=[0, 0.075, 1, 1])
    fig.savefig(_out("四档结构_谁卖给谁.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[done] 四档结构")


# ------------------------------------------------------------ 图3 全天资金节奏
def rhythm():
    # 优先用"全市场分时"（沪市+深市指数聚合）；没有则回退到头部候选池。
    mkt_path = os.path.join(C.DATA_DIR, "分时资金流_全市场.json")
    if os.path.exists(mkt_path):
        with open(mkt_path, encoding="utf-8") as f:
            mkt = json.load(f)
        times = [t[11:16] for t in mkt["times"]]
        pool = np.array(mkt["main"]) / 1e8
        idx_name = mkt.get("meta", {}).get("name", "指数")
        scope = f"{idx_name}（沪市指数口径）"
    else:
        data = C.load_intraday()
        codes = list(data)
        times = [r[0][11:16] for r in data[codes[0]]["series"]]
        pool = np.zeros(len(times))
        for c in codes:
            pool += np.array([float(r[1]) for r in data[c]["series"]])
        pool /= 1e8
        scope = f"头部候选池（{len(codes)} 只）"
    inc = np.diff(np.concatenate([[0.0], pool]))

    fig = plt.figure(figsize=(11.2, 6.4), dpi=150)
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 2], hspace=0.18)
    ax1, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    xs = np.arange(len(times))

    ax1.fill_between(xs, pool, 0, color=RED, alpha=0.09, zorder=2)
    ax1.plot(xs, pool, color=RED, lw=2.4, solid_capstyle="round", zorder=3)
    ax1.axhline(0, color="#CCCCCC", lw=0.9, zorder=1)
    li = times.index("13:01") if "13:01" in times else len(times) // 2
    for ax in (ax1, ax2):
        ax.axvline(li, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=1)
        ax.set_xlim(-2, len(times) + 1)
    ax1.text(li - 1.5, 0, "午休", ha="right", va="bottom", fontsize=9.5, color=MUTED)

    # 分段：时间窗固定，数值 = 段内每分钟增量之和（不重不漏，按当日数据动态求）
    seg_def = [("开盘 30 分钟", "09:31", "10:00"),
               ("上午中段", "10:01", "11:30"),
               ("午后开盘 30 分钟", "13:01", "13:30"),
               ("之后一小时", "13:31", "14:30"),
               ("尾盘 30 分钟", "14:31", "15:00")]
    segs = []
    for lab, a, b in seg_def:
        if a not in times or b not in times:
            continue
        v = float(inc[times.index(a): times.index(b) + 1].sum())
        segs.append((lab, a, b, v))

    ymin, ymax = pool.min(), pool.max()
    yb = ymax + (ymax - ymin) * 0.42
    for lab, a, b, v in segs:
        ia, ib = times.index(a), times.index(b)
        col = RED if v > 0 else GREEN
        ax1.plot([ia, ib], [yb, yb], color=col, lw=2.2, zorder=5)
        for xx in (ia, ib):
            ax1.plot([xx, xx], [yb - (ymax - ymin) * 0.06, yb], color=col, lw=2.2, zorder=5)
        ax1.text((ia + ib) / 2, yb + (ymax - ymin) * 0.08, f"{lab}\n{v:+.1f} 亿",
                 ha="center", va="bottom", fontsize=9.6, fontweight="bold",
                 color=col, zorder=5)
    ax1.set_ylim(ymin - (ymax - ymin) * 0.18, ymax + (ymax - ymin) * 1.05)
    ax1.set_ylabel("累计主力净流入（亿元）", fontsize=10.5, color=MUTED)
    ax1.tick_params(axis="x", labelbottom=False, length=0)
    ax1.grid(axis="y", linestyle="-", lw=0.5, color=GRID, zorder=0)
    for sp in ("top", "right"):
        ax1.spines[sp].set_visible(False)
    ax1.spines["left"].set_color("#DDDDDD")
    ax1.set_title("全天资金节奏：上面是累计净额，下面是每分钟增量",
                  fontsize=14, fontweight="bold", color=INK, loc="left", pad=14)

    colors = [RED if v >= 0 else GREEN for v in inc]
    ax2.bar(xs, inc, color=colors, width=0.85, zorder=3)
    ax2.axhline(0, color="#999999", lw=0.9, zorder=2)
    k = int(np.argmax(inc))
    kmin = int(np.argmin(inc))
    if abs(inc[k]) >= abs(inc[kmin]):
        kk, sign = k, "+"
    else:
        kk, sign = kmin, ""
    note = "（午后开盘第一分钟）" if times[kk] == "13:01" else ""
    ax2.annotate(f"{times[kk]} 单分钟峰值{note}\n净额 {sign}{inc[kk]:.1f} 亿",
                 (kk, inc[kk]), textcoords="offset points", xytext=(9, -6),
                 ha="left", va="top", fontsize=9.5, fontweight="bold",
                 color=RED if inc[kk] >= 0 else GREEN,
                 arrowprops=dict(arrowstyle="-",
                                 color=RED if inc[kk] >= 0 else GREEN, lw=0.9))
    ax2.set_ylim(min(inc.min() * 1.15, -1.5), inc.max() * 1.32 + 0.5)
    ax2.set_ylabel("每分钟净额增量（亿元）", fontsize=10.5, color=MUTED)
    ax2.grid(axis="y", linestyle="-", lw=0.5, color=GRID, zorder=0)
    for sp in ("top", "right"):
        ax2.spines[sp].set_visible(False)
    ax2.spines["left"].set_color("#DDDDDD")
    ax2.spines["bottom"].set_color("#DDDDDD")
    targets = ["09:31", "10:00", "10:30", "11:00", "11:30", "13:30", "14:00", "14:30", "15:00"]
    ticks = [times.index(t) for t in targets if t in times]
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([t for t in targets if t in times], fontsize=9.5, color=MUTED)
    ax2.tick_params(axis="y", labelsize=9, colors=MUTED)

    fig.text(0.012, 0.012,
             f"口径：{scope}，分段时间按分钟增量求和计算。数据：东方财富 fflow/kline 单指数分时",
             fontsize=8.6, color=MUTED)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.925, bottom=0.12)
    fig.savefig(_out("资金节奏_全天.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[done] 资金节奏  " + "  ".join(f"{l}{v:+.1f}" for l, _, _, v in segs))


# ---------------------------------------------------------------- 图4 市值分层
def mktcap_layer():
    df = C.load_ext()
    df["cap_yi"] = df["mktcap"] / 1e8
    bins = [0, 50, 100, 300, 1000, 1e9]
    names = ["微盘", "小盘", "中盘", "大盘", "超大盘"]
    ranges = ["<50亿", "50-100亿", "100-300亿", "300-1000亿", ">1000亿"]
    df["layer"] = pd.cut(df["cap_yi"], bins=bins, labels=names)

    agg = df.groupby("layer", observed=True).agg(
        net=("main_net", "sum"), cnt=("main_net", "size"), pct=("pct", "mean"))
    agg["net"] /= 1e8
    vals = agg["net"].values
    cnts = agg["cnt"].values
    pcts = agg["pct"].values
    top = float(vals.max())

    fig, ax = plt.subplots(figsize=(10.8, 6.0), dpi=150)
    xs = np.arange(len(agg))
    ax.bar(xs, vals, width=0.54,
           color=[RED if v >= 0 else GREEN for v in vals], zorder=3)
    for x, v, cnt, p in zip(xs, vals, cnts, pcts):
        inside = v > top * 0.25
        ax.text(x, v + top * (0.025 if v >= 0 else -0.055), f"{v:+.1f} 亿",
                ha="center", va="bottom" if v >= 0 else "top",
                fontsize=12.5, fontweight="bold",
                color=RED if v >= 0 else GREEN, zorder=5)
        if inside:
            ax.text(x, v * 0.07, f"均涨 {p:+.1f}%", ha="center", va="bottom",
                    fontsize=9.4, color="white", zorder=5)
        else:
            ax.text(x, v + top * (0.105 if v >= 0 else -0.135), f"均涨 {p:+.1f}%",
                    ha="center", va="bottom" if v >= 0 else "top",
                    fontsize=9.4, color=MUTED, zorder=5)
    ax.axhline(0, color="#444", lw=1.0, zorder=2)
    ax.set_ylim(min(vals.min(), 0) - abs(top) * 0.20, top * 1.26)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{n}\n{r}\n{c} 只" for n, r, c in zip(names, ranges, cnts)],
                       fontsize=10.2, color=INK)
    ax.set_ylabel("主力净额合计（亿元）", fontsize=11, color=MUTED)
    ax.grid(axis="y", linestyle="-", lw=0.5, color=GRID, zorder=0)
    for sp in ax.spines.values():
        sp.set_visible(False)

    big = int(cnts[names.index("大盘")] + cnts[names.index("超大盘")])
    big_net = float(vals[names.index("大盘")] + vals[names.index("超大盘")])
    total = float(vals.sum())
    share = big_net / total * 100 if total else 0
    micro = int(cnts[names.index("微盘")])
    micro_net = float(vals[names.index("微盘")])
    ax.set_title(f"按总市值分组的主力净额：大盘+超大盘 {big} 只占 {share:.0f}%，"
                 f"{micro} 只微盘股合计 {micro_net:+.1f} 亿（{DATE}）",
                 fontsize=14, fontweight="bold", color=INK, loc="left", pad=16)
    fig.text(0.012, 0.015, "按当日总市值分组；「只」为该层股票数量。数据：东方财富",
             fontsize=8.6, color=MUTED)
    fig.tight_layout(rect=[0, 0.035, 1, 1])
    fig.savefig(_out("市值分层_钱去哪.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(agg.round(1).to_string())


def limit_up_mask(df: pd.DataFrame) -> pd.Series:
    """按板块判定涨停：主板 10%（ST 5%）、创业板/科创板 20%、北交所 30%。

    不能简单用「涨幅 >= 9.8%」——创业板、科创板是 20cm 涨停板，
    该阈值会把大量 10%~20% 的非涨停股误判为涨停（2026-09-21 实测误收 33 家，
    其中福立旺 +13.2%、成都先导 +13.8% 都不是涨停）。
    """
    code = df["code"].astype(str).str.zfill(6)
    st = (df["name"].astype(str).str.upper()
          .str.replace(" ", "", regex=False).str.contains("ST"))
    base = pd.Series(10.0, index=df.index)                    # 主板 10%
    base[st] = 5.0                                            # 主板 ST 5%
    base[code.str.startswith(("300", "301", "688"))] = 20.0   # 创业板/科创板 20cm
    base[code.str.startswith(("8", "4"))] = 30.0              # 北交所 30cm
    # 用「涨幅落在阈值附近」而非「涨幅 >= 阈值」判定：ST 股当天若不再受 5% 限制
    # （如撤销风险警示等情况），涨幅会超过 5% 却并非涨停，单边阈值会把它误收。
    return (df["pct"] >= base - 0.35) & (df["pct"] <= base + 0.6)


# ------------------------------------------------------------ 图5 涨停股解剖
def limitup_anatomy(df: pd.DataFrame):
    z = df[limit_up_mask(df)].copy()
    n_all = len(z)
    if n_all == 0:
        print("[skip] 当日无涨停样本")
        return
    n_in = int((z["main_net"] > 0).sum())
    tot, small, xl = yi(z["main_net"].sum()), yi(z["m_net"].sum()), yi(z["xl_net"].sum())
    mkt = yi(df["main_net"].sum())
    rows = pd.concat([z.nlargest(8, "main_net"), z.nsmallest(6, "main_net")])
    labels = [r["name"] for _, r in rows.iterrows()]
    ys = np.arange(len(rows))[::-1]
    n_head = min(8, n_all)

    XMAX = float(np.ceil(max(abs(yi(r["main_net"])) for _, r in rows.iterrows()) / 5) * 5)
    XRES = XMAX * 1.14
    fig, ax = plt.subplots(figsize=(11.4, 7.0), dpi=150)
    ax.plot([-XMAX * 1.13, XRES + XMAX * 0.85], [len(rows) - n_head + 0.5] * 2,
            color="#D8D8D4", lw=1.0, ls=(0, (5, 4)), zorder=2)
    for y, (_, r) in zip(ys, rows.iterrows()):
        m = yi(r["main_net"])
        c = RED if m >= 0 else GREEN
        ax.barh(y, m, height=0.54, color=c, zorder=3)
        ax.text(m + (XMAX * 0.02 if m >= 0 else -XMAX * 0.02), y, f"{m:+.2f} 亿",
                va="center", ha="left" if m >= 0 else "right", fontsize=10.6,
                fontweight="bold", color=c, zorder=5)
        ax.text(XRES, y, f"{yi(r['xl_net']):+.2f}", va="center", ha="left",
                fontsize=10, color=INK, zorder=5)
        ax.text(XRES + XMAX * 0.36, y, f"{yi(r['m_net']):+.2f}", va="center",
                ha="left", fontsize=10, color=MUTED, zorder=5)
    ax.axvline(0, color="#444", lw=1.0, zorder=4)
    ax.text(XRES, len(rows) - 0.35, "超大单", ha="left", va="center",
            fontsize=10, color=MUTED)
    ax.text(XRES + XMAX * 0.36, len(rows) - 0.35, "中小单", ha="left", va="center",
            fontsize=10, color=MUTED)
    ax.text(-XMAX * 1.13, len(rows) - 0.35,
            f"当日涨停 {n_all} 家：主力净流入 {n_in} 家（{n_in / n_all * 100:.0f}%），"
            f"合计 {tot:+.1f} 亿，占全市场净额 {tot / mkt * 100:.0f}%",
            ha="left", va="center", fontsize=11.5, fontweight="bold", color=INK)

    ax.set_xlim(-XMAX * 1.13, XRES + XMAX * 0.85)
    ax.set_ylim(-0.75, len(rows) + 0.15)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=11.5, fontweight="bold", color=INK)
    ax.tick_params(axis="y", length=0)
    ticks = [v for v in np.arange(-XMAX, XMAX + 1, XMAX / 3 if XMAX > 10 else XMAX / 2)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{v:+.0f}" if v else "0" for v in ticks],
                       fontsize=10, color=MUTED)
    ax.set_xlabel("主力净额（亿元）", fontsize=10.6, color=MUTED, labelpad=8)
    ax.grid(axis="x", linestyle="-", lw=0.5, color=GRID, zorder=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(f"涨停股的资金结构：{n_all} 家合计占全市场净额 {tot / mkt * 100:.0f}%（{DATE}）",
                 fontsize=14, fontweight="bold", color=INK, loc="left", pad=16)
    n_neg = n_all - n_in
    fig.text(0.012, 0.012,
             f"涨停股整体：主力 {tot:+.1f} 亿、超大单 {xl:+.1f} 亿、中小单 {small:+.1f} 亿。"
             f"下方 {min(6, n_neg)} 家为涨停但主力净额为负的例子。数据：东方财富",
             fontsize=8.6, color=MUTED)
    fig.tight_layout(rect=[0, 0.045, 1, 1])
    fig.savefig(_out("涨停股解剖_两种钱.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[done] 涨停股解剖 {n_all} 家 主力净额 {tot:+.1f}亿 占 {tot / mkt * 100:.0f}%")


if __name__ == "__main__":
    market = C.load_market()
    tier_overview(market)
    tier_fingerprint(market)
    rhythm()
    limitup_anatomy(market)
    if os.path.exists(C.EXT_CSV):
        mktcap_layer()
    else:
        print("[skip] 扩展字段尚未采集完成")
