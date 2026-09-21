# -*- coding: utf-8 -*-
"""v3.2.0 | 2026-09-20 | 资金榜演变GIF · 匀速丝滑版。

丝滑（参考 2020 年《matplotlib也玩动态可视化》一文的经验：均匀节奏>高帧率）：
- 全片统一 70ms/帧：关键帧与过渡帧同速，无"停顿-快闪"交替，无中途长停留；
- 线性匀速插值：条形的值与槽位按时间匀速运动（传送带式），不逐段缓动归零；
- 仅有三处刻意停顿：片首 0.9s / 午休 11:30 0.8s / 片尾 2.5s；
- bar chart race：进榜股从下一行上浮淡入、出榜股下沉一行收缩淡出。

语义：
- ★ 标记各区榜首：流入区 = 净流入最多，流出区 = 净流出最多（取最小负值）。

质感：
- 圆角胶囊条 + 顶部高光 + 柔和投影 + 斑马行底纹 + 中轴分隔线；
- 暗色时间牌、等宽字体数字防抖动；
- 底部累计净流入曲线红色（语义统一），端点带光环。

体积：740×534、约161帧、全帧共享56色调色板、无抖动量化、实线网格，≤4.2MB。
"""
from __future__ import annotations
import json, argparse, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.lines import Line2D
from PIL import Image

import _common as C

for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
           "C:/Windows/Fonts/consola.ttf"]:
    try:
        font_manager.fontManager.addfont(fp)
    except Exception:
        pass
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
MONO = "Consolas"

RED, RED_L = "#C93A3C", "#EFB0AB"
GREEN, GREEN_L = "#12855E", "#9AD4BB"
INK, MUTED = "#26282B", "#9B9B97"
BG, ROW = "#FBFBF9", "#F1F1EC"
LINE = "#E7E7E2"
GOLD = "#C9A227"
BADGE_BG, BADGE_FG = "#26282B", "#FFFFFF"
SHADOW = "#DCDCD4"

FIG_W, FIG_H, DPI = 7.4, 5.34, 100  # -> 740x534
N_IN, N_OUT = 8, 6
SCALE = 30.0                        # 条形满宽对应 30 亿
TOTAL_ROWS = N_IN + 1 + N_OUT       # 15 槽：0-7流入 | 8中缝 | 9-14流出
ROW_H = 1.0 / TOTAL_ROWS
ASPECT = 1.0                        # FancyBboxPatch 视觉等比系数，初始化时计算
HERO_TIMES = ("11:30",)   # 仅午休锚点：作为关键帧并短暂停留（其余时刻一律匀速）


def load_candidates(path: str):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    stocks = {}
    for code, v in data.items():
        series = {}
        for row in v["series"]:
            series[row[0][11:16]] = float(row[1]) / 1e8   # 元 -> 亿元
        stocks[code] = {"name": v["name"].replace(" ", ""), "series": series}
    return stocks


def trading_minutes(stocks) -> list:
    mins = set()
    for s in stocks.values():
        mins.update(s["series"].keys())
    def ok(t):
        return ("09:31" <= t <= "11:30") or ("13:01" <= t <= "15:00")
    return sorted(t for t in mins if ok(t))


def top_bottom(stocks, t):
    vals = [(c, s["name"], s["series"].get(t)) for c, s in stocks.items()]
    vals = [v for v in vals if v[2] is not None]
    vals.sort(key=lambda x: x[2], reverse=True)
    top = [v for v in vals if v[2] > 0][:N_IN]
    bot = [v for v in vals if v[2] < 0][-N_OUT:]
    bot.reverse()  # 流出最多的在前
    return {"top": top, "bot": bot}


def key_state(sn):
    """快照 -> 可绘制状态：给每个条目附槽位号。"""
    return {"top": [(c, n, v, i) for i, (c, n, v) in enumerate(sn["top"])],
            "bot": [(c, n, v, N_IN + 1 + i) for i, (c, n, v) in enumerate(sn["bot"])]}


def smoother(t: float) -> float:
    return t  # v3.2：线性匀速。逐段缓动会让速度在每个关键帧归零，产生"脉动感"；匀速才是丝滑。


def blend_state(A, B, k):
    """A、B 为 key_state；k∈(0,1)。值与槽位都插值；出榜下沉淡出、进榜上浮淡入。"""
    out = {"top": [], "bot": []}
    for sec in ("top", "bot"):
        a, b = A[sec], B[sec]
        da = {c: (n, v, s) for (c, n, v, s) in a}
        db = {c: (n, v, s) for (c, n, v, s) in b}
        for c in dict.fromkeys([x[0] for x in a] + [x[0] for x in b]):
            if c in da and c in db:
                na, va, sa = da[c]
                _nb, vb, sb = db[c]
                slot = sa + (sb - sa) * k
                val = va + (vb - va) * k
            elif c in da:                      # 出榜：下沉一行，收缩到0
                na, va, sa = da[c]
                slot = sa + min(1.0, TOTAL_ROWS - 0.7 - sa) * k
                val = va * (1 - k)
            else:                              # 进榜：自下一行上浮，从0长出
                nb, vb, sb = db[c]
                s0 = min(sb + 1.0, TOTAL_ROWS - 0.8)
                slot = s0 + (sb - s0) * k
                na, val = nb, vb * k
            out[sec].append((c, na, val, slot))
    return out


def draw_section(ax, items):
    if not items:
        return
    items = sorted(items, key=lambda x: x[3])
    # ★ 榜首判定：流入区取最大正值；流出区（全负）取最小值 = 净流出最多
    if items and max(x[2] for x in items) > 0:
        leader = max(items, key=lambda x: x[2])[0]
    else:
        leader = min(items, key=lambda x: x[2])[0]
    h = ROW_H * 0.58
    for idx, (code, name, v, slot) in enumerate(items):
        # 换位交叉时两条目过近：隐藏靠下条目的名字/数值，避免文字糊成一团
        hide = idx > 0 and (slot - items[idx - 1][3]) < 0.7
        y = 1.0 - (slot + 0.5) * ROW_H
        bw = min(abs(v), SCALE) / SCALE * 0.84
        if bw < 0.004:
            continue
        if v >= 0:
            x0, c, cl = 0.0, RED, RED_L
        else:
            x0, c, cl = -bw, GREEN, GREEN_L
        r = min(h / (2.0 * ASPECT), bw / 2 * 0.98)
        if r > 0.002:
            # 投影
            ax.add_patch(FancyBboxPatch(
                (x0 + 0.005, y - h / 2 - 0.007), bw, h,
                boxstyle=f"round,pad=0,rounding_size={r:.4f}",
                mutation_aspect=ASPECT, fc=SHADOW, ec="none", zorder=2))
            # 本体
            ax.add_patch(FancyBboxPatch(
                (x0, y - h / 2), bw, h,
                boxstyle=f"round,pad=0,rounding_size={r:.4f}",
                mutation_aspect=ASPECT, fc=c, ec="none", zorder=3))
            # 顶部高光
            ax.add_patch(FancyBboxPatch(
                (x0 + 0.004, y + h * 0.08), max(bw - 0.008, 0.004), h * 0.36,
                boxstyle=f"round,pad=0,rounding_size={r * 0.6:.4f}",
                mutation_aspect=ASPECT, fc=cl, alpha=0.55, ec="none", zorder=4))
        # 数值（等宽字体，防数字抖动）
        if abs(v) >= 0.15 and not hide:
            txt = f"+{v:.1f}" if v >= 0 else f"{v:.1f}"
            if v >= 0:
                ax.text(bw + 0.012, y, txt, ha="left", va="center",
                        fontsize=9.5, color=c, fontweight="bold",
                        fontfamily=MONO, zorder=5)
            else:
                ax.text(-bw - 0.012, y, txt, ha="right", va="center",
                        fontsize=9.5, color=c, fontweight="bold",
                        fontfamily=MONO, zorder=5)
        # 名称跟随条形滑动；太短的条（过渡中）不画名字，避免挤成一团
        if abs(v) >= 0.3 and not hide:
            label = name + (" ★" if code == leader else "")
            color = GOLD if code == leader else INK
            if v >= 0:
                ax.text(-0.015, y, label, ha="right", va="center", fontsize=10.5,
                        fontweight="bold", color=color, zorder=5)
            else:
                ax.text(0.015, y, label, ha="left", va="center", fontsize=10.5,
                        fontweight="bold", color=color, zorder=5)


def draw_frame(ax1, ax2, state, frac_idx, ys_curve, ticks, tick_labels):
    ax1.clear()
    ax1.set_xlim(-1.06, 1.06)
    ax1.set_ylim(0, 1)
    ax1.set_xticks([])
    ax1.set_yticks([])
    ax1.set_facecolor(BG)
    for sp in ax1.spines.values():
        sp.set_visible(False)
    # 斑马行
    for s in range(TOTAL_ROWS):
        if s % 2 == 0:
            ax1.add_patch(Rectangle((-1.06, 1 - (s + 1) * ROW_H), 2.12, ROW_H,
                                    fc=ROW, ec="none", zorder=0))
    # 中轴线
    ax1.add_line(Line2D([0, 0], [0.015, 0.985], color=LINE, lw=1.1, zorder=1))
    # 中缝分隔 + 标签放两端（不被长条遮挡）
    y_div = 1 - (N_IN + 0.5) * ROW_H
    ax1.add_line(Line2D([-1.06, 1.06], [y_div, y_div], color=LINE, lw=1.0, zorder=1))
    ax1.text(-1.045, y_div, "▲ 净流入 TOP8", ha="left", va="center",
             fontsize=9.5, color=RED, fontweight="bold", zorder=5)
    ax1.text(1.045, y_div, "净流出 TOP6 ▼", ha="right", va="center",
             fontsize=9.5, color=GREEN, fontweight="bold", zorder=5)
    draw_section(ax1, state["top"])
    draw_section(ax1, state["bot"])

    # 底部累计曲线
    ax2.clear()
    xs = np.arange(len(ys_curve))
    ax2.plot(xs, ys_curve, color=RED, lw=1.7, solid_capstyle="round", zorder=3)
    ax2.fill_between(xs, ys_curve, 0, color=RED, alpha=0.08, zorder=2)
    ax2.axhline(0, color=LINE, lw=0.8, zorder=1)
    yv = float(np.interp(frac_idx, xs, ys_curve))
    ax2.scatter([frac_idx], [yv], s=150, color=RED, alpha=0.16, zorder=4)
    ax2.scatter([frac_idx], [yv], s=32, color=RED, edgecolor="white",
                linewidth=1.3, zorder=5)
    pad = (ys_curve.max() - min(ys_curve.min(), 0)) * 0.18 + 3
    ax2.set_xlim(0, len(xs) - 1)
    ax2.set_ylim(min(ys_curve.min() - pad, -2), ys_curve.max() + pad)
    near_right = frac_idx > len(xs) * 0.72
    near_top = yv > ys_curve.max() + pad * 0.25
    ax2.text(frac_idx + (-7 if near_right else 7),
             yv + (-pad * 0.06 if near_top else pad * 0.05),
             f"{yv:+.0f}", ha="right" if near_right else "left",
             va="top" if near_top else "bottom",
             fontsize=9, color=RED, fontweight="bold", fontfamily=MONO, zorder=6)
    step = 50
    lo = int(np.floor(min(ys_curve.min(), 0) / step))
    hi = int(np.ceil(ys_curve.max() / step))
    ax2.set_yticks([i * step for i in range(lo, hi + 1)])
    ax2.set_xticks(ticks)
    ax2.set_xticklabels(tick_labels, fontsize=7.5, color=MUTED)
    ax2.tick_params(axis="x", length=0)
    ax2.tick_params(axis="y", labelsize=7.5, colors=MUTED, length=0)
    ax2.grid(axis="y", linestyle="-", linewidth=0.5, color=LINE, alpha=0.6, zorder=0)
    ax2.set_ylabel("候选池累计净流入（亿元）", fontsize=8.5, color=MUTED)
    for sp in ("top", "right"):
        ax2.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax2.spines[sp].set_color(LINE)


def _mm(t):
    return int(t[:2]) * 60 + int(t[3:5])


def _fmt(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def build_gif(stocks, out_gif, every=8, sub=4, hold_last=3.0):
    global ASPECT
    minutes = trading_minutes(stocks)
    sum_curve = np.array([sum(s["series"].get(t, 0.0) for s in stocks.values())
                          for t in minutes])

    idx_of = {t: i for i, t in enumerate(minutes)}
    key_set = set(range(0, len(minutes), every))
    key_set.update(idx_of[t] for t in HERO_TIMES if t in idx_of)
    key_set.add(len(minutes) - 1)
    key_idx = sorted(key_set)
    snaps = [key_state(top_bottom(stocks, minutes[i])) for i in key_idx]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(FIG_W, FIG_H), dpi=DPI,
        gridspec_kw={"height_ratios": [5, 2]})
    fig.patch.set_facecolor(BG)
    fig.subplots_adjust(left=0.025, right=0.965, top=0.845, bottom=0.085,
                        hspace=0.36)

    # 头部静态元素（只建一次，跨帧复用）
    fig.text(0.045, 0.972, "A股主力资金流向 · 全天演变", fontsize=15,
             fontweight="bold", color=INK, ha="left", va="top")
    fig.add_artist(Rectangle((0.045, 0.949), 0.05, 0.006,
                             transform=fig.transFigure, color=RED, ec="none"))
    fig.text(0.045, 0.931, f"{C.DATE} · 沪深A股 · 主力净额 = 超大单 + 大单 · 单位：亿元",
             fontsize=8.8, color=MUTED, ha="left", va="top")
    badge = fig.text(0.965, 0.968, "09:31", ha="right", va="top",
                     fontsize=14.5, fontweight="bold", color=BADGE_FG,
                     fontfamily=MONO,
                     bbox=dict(boxstyle="round,pad=0.42", fc=BADGE_BG, ec="none"))
    fig.text(0.025, 0.010, "数据：东方财富 · 制图：可以叫我才哥", fontsize=7.2,
             color=MUTED, ha="left", va="bottom")

    fig.canvas.draw()
    bb = ax1.get_window_extent()
    ASPECT = (bb.width / 2.12) / (bb.height / 1.0)

    # 曲线时间刻度
    targets = ["09:31", "10:30", "11:30", "13:30", "14:30", "15:00"]
    ticks = [idx_of[t] for t in targets if t in idx_of]
    tick_labels = [t for t in targets if t in idx_of]

    def render(state, t_label, fi):
        badge.set_text(t_label)
        draw_frame(ax1, ax2, state, fi, sum_curve, ticks, tick_labels)
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())
        return Image.fromarray(np.ascontiguousarray(buf[:, :, :3]))

    # 全片匀速节奏：关键帧与过渡帧同为 FRAME_MS，仅三处刻意停顿
    FRAME_MS = 70
    HOLD = {"11:30": 800}           # 午休前停留，给读者一个"休市"信号
    frames, durs = [], []
    frames.append(render(snaps[0], minutes[key_idx[0]], float(key_idx[0])))
    durs.append(900)                # 片首停留
    for i in range(len(key_idx) - 1):
        ta, tb = minutes[key_idx[i]], minutes[key_idx[i + 1]]
        big_gap = _mm(tb) - _mm(ta) > 90  # 跨午休：无交易，榜单直接跳变
        for j in range(1, sub):
            if big_gap:
                break
            k = smoother(j / sub)
            tl = _fmt(round(_mm(ta) + (_mm(tb) - _mm(ta)) * k))
            fi = key_idx[i] + (key_idx[i + 1] - key_idx[i]) * k
            frames.append(render(blend_state(snaps[i], snaps[i + 1], k), tl, fi))
            durs.append(FRAME_MS)
        frames.append(render(snaps[i + 1], tb, float(key_idx[i + 1])))
        durs.append(HOLD.get(tb, FRAME_MS))
    durs[-1] = int(hold_last * 1000)

    # 全帧共享调色板：取多帧拼图构建，保证红绿金都在
    sample = [frames[0], frames[len(frames) // 4], frames[len(frames) // 2],
              frames[3 * len(frames) // 4], frames[-1]]
    mosaic = Image.new("RGB", (sample[0].width, sample[0].height * len(sample)))
    for i, f in enumerate(sample):
        mosaic.paste(f, (0, i * sample[0].height))
    ref = mosaic.quantize(colors=56, method=Image.MEDIANCUT)
    q_frames = [f.quantize(palette=ref, dither=Image.Dither.NONE) for f in frames]
    q_frames[0].save(out_gif, save_all=True, append_images=q_frames[1:],
                     duration=durs, loop=0, optimize=True, disposal=2)
    plt.close(fig)
    mb = os.path.getsize(out_gif) / 1048576
    print(f"[done] {out_gif}  帧数 {len(frames)}  时长 {sum(durs)/1000:.1f}s  大小 {mb:.2f} MB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=C.INTRADAY_JSON)
    ap.add_argument("--out", default=os.path.join(C.OUT_DIR, "资金榜演变_动图.gif"))
    ap.add_argument("--every", type=int, default=6)
    ap.add_argument("--sub", type=int, default=3)
    args = ap.parse_args()
    stocks = load_candidates(args.json)
    build_gif(stocks, args.out, every=args.every, sub=args.sub)
