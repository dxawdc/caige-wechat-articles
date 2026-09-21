"""v1.3.0 | 2026-09-21 | 行业资金流图 + 榜首分时对比 + 全市场散点（+ 资料库用 plotly 瀑布图）。

产出（文章用PNG + 资料库用交互HTML）：
1. 细分行业资金流榜：PNG
2. 当日净额榜首 vs 榜尾 分时累计主力净额对比：PNG
3. 全市场 涨跌幅 x 主力净额占比 散点：PNG
4. plotly瀑布图：PNG + HTML（已不在文章中使用，作为资料库附加产出保留）

v1.3.0：日期、样本数、标注个股、坐标范围全部改为按当日数据动态生成，
避免换一天数据后标题仍印着上一天的个股名与统计值。
"""
from __future__ import annotations
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import _common as C

C.add_fonts(matplotlib)
RED, GREEN, INK, MUTED = C.RED, C.GREEN, C.INK, C.MUTED
BLUE = "#2F6FED"

# 东方财富一级行业（31个标准分类）：从板块全量中过滤，避免父子层级同框
L1 = {"农林牧渔", "基础化工", "钢铁", "有色金属", "电子", "家用电器", "食品饮料",
      "纺织服饰", "轻工制造", "医药生物", "公用事业", "交通运输", "房地产",
      "商贸零售", "社会服务", "综合", "建筑材料", "建筑装饰", "电力设备",
      "机械设备", "国防军工", "汽车", "计算机", "传媒", "通信", "银行", "非银金融",
      "环保", "煤炭", "石油石化", "美容护理"}


# --------------------------------------------------------------- 行业资金流
def industry_chart():
    if not os.path.exists(C.INDUSTRY_CSV):
        print("[skip] 行业数据未采集")
        return
    ind = pd.read_csv(C.INDUSTRY_CSV)
    ind["name"] = ind["name"].str.rstrip("－-— ")
    for c in ["main_net", "main_pct"]:
        ind[c] = pd.to_numeric(ind[c].replace("-", None), errors="coerce")
    ind = ind[ind["name"].isin(L1)].dropna(subset=["main_net"]).copy()
    ind["yi"] = ind["main_net"] / 1e8
    print(f"[行业] 一级行业匹配 {len(ind)} 个")
    ind = ind.sort_values("yi", ascending=False)
    top = ind.head(12)
    bot = ind.tail(8).iloc[::-1]
    rows = pd.concat([top, bot]).iloc[::-1]

    fig, ax = plt.subplots(figsize=(10, 7.4), dpi=150)
    colors = [RED if v > 0 else GREEN for v in rows["yi"]]
    ax.barh(rows["name"], rows["yi"], color=colors, height=0.62, zorder=3)
    span = max(abs(rows["yi"].max()), abs(rows["yi"].min()))
    for i, (name, v) in enumerate(zip(rows["name"], rows["yi"])):
        ax.text(v + (span * 0.012 if v > 0 else -span * 0.012), i, f"{v:+.1f}",
                va="center", ha="left" if v > 0 else "right",
                fontsize=9.5, color=colors[i], fontweight="bold")
    ax.axvline(0, color="#444", linewidth=0.8)
    ax.set_title(f"一级行业主力净额：{len(L1 & set(ind['name']))} 个行业聚合（{C.DATE}，亿元）",
                 fontsize=13, fontweight="bold", color=INK, loc="left", pad=12)
    ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}")
    ax.tick_params(axis="y", labelsize=10.5)
    ax.grid(axis="x", linestyle="--", alpha=0.35, zorder=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_xlim(min(rows["yi"]) * 1.3 - 2, max(rows["yi"]) * 1.12 + 2)
    fig.tight_layout()
    out = os.path.join(C.OUT_DIR, "行业资金流.png")
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[done] {out}  头名 {rows['name'].iloc[-1]} {rows['yi'].iloc[-1]:+.1f}亿")
    return ind


# ------------------------------------------------------------ 榜首分时对比
def intraday_compare(market: pd.DataFrame):
    data = C.load_intraday()
    top = market.nlargest(1, "main_net").iloc[0]
    bot = market.nsmallest(1, "main_net").iloc[0]
    pairs = []
    for r, side in ((top, "in"), (bot, "out")):
        if r["code"] in data:
            pairs.append((r["code"], r["name"], side))
    if len(pairs) < 2:
        print("[skip] 榜首不在候选池内，跳过分时对比")
        return
    print(f"[榜首] 流入 {top['name']}({top['code']}) / 流出 {bot['name']}({bot['code']})")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), dpi=150)
    for (code, name, side), ax in zip(pairs, axes):
        v = data[code]
        t = [r[0][11:16] for r in v["series"]]
        y = np.array([float(r[1]) for r in v["series"]]) / 1e8
        x = range(len(y))
        color = RED if side == "in" else GREEN
        ax.plot(x, y, color=color, linewidth=1.8)
        ax.fill_between(x, y, 0, color=color, alpha=0.12)
        ax.axhline(0, color="#DDD", linewidth=0.8)
        ax.annotate(f"收盘 {y[-1]:+.1f}亿", (len(y) - 1, y[-1]),
                    textcoords="offset points", xytext=(-6, 12), ha="right",
                    fontsize=11, color=color, fontweight="bold")
        n = len(y)
        ticks = list(range(0, n, 48)) + [n - 1]
        ax.set_xticks(ticks)
        ax.set_xticklabels([t[i] for i in ticks], fontsize=9)
        ax.set_title(("流入榜首：" if side == "in" else "流出榜首：") + name,
                     fontsize=12.5, fontweight="bold", color=INK, loc="left")
        ax.set_ylabel("当日累计主力净额（亿元）", fontsize=9.5)
        ax.tick_params(labelsize=9)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle(f"榜首的一天：分时累计主力净额（{C.DATE}）", fontsize=14,
                 fontweight="bold", color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(C.OUT_DIR, "榜首分时对比.png")
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[done] {out}")


# --------------------------------------------------------------- 全市场散点
def scatter_all(df: pd.DataFrame):
    d = df.dropna(subset=["pct", "main_pct"]).copy()
    fig, ax = plt.subplots(figsize=(10.5, 7), dpi=150)
    colors = [RED if v > 0 else GREEN for v in d["main_net"]]
    sizes = np.clip(np.abs(d["main_net"]) / 1e8 * 6 + 2, 2, 60)
    ax.scatter(d["pct"], d["main_pct"], s=sizes, c=colors, alpha=0.45,
               edgecolors="none", zorder=3)
    ax.axhline(0, color="#CCC", linewidth=0.8)
    ax.axvline(0, color="#CCC", linewidth=0.8)

    # 坐标范围：按当日分布自动定，极端值（多为新股首日）排除在外并注明
    xlo, xhi = np.percentile(d["pct"], [0.5, 99.5])
    ylo, yhi = np.percentile(d["main_pct"], [0.3, 99.7])
    xlim = (int(min(np.floor(xlo) - 1, -8)), int(max(np.ceil(xhi) + 1, 8)))
    ylim = (int(min(np.floor(ylo / 5) * 5 - 3, -25)),
            int(max(np.ceil(yhi / 5) * 5 + 3, 25)))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)

    # 动态挑选要标注的个股：净额榜首/榜尾 + 占比两端，且每只都落在可见范围内
    picks: list[tuple[str, str]] = []
    def add(code, name, tag):
        if not any(p[0] == code for p in picks):
            picks.append((code, name, tag))

    for _, r in d.nlargest(3, "main_net").iterrows():
        add(r["code"], r["name"], "in")
    for _, r in d.nsmallest(2, "main_net").iterrows():
        add(r["code"], r["name"], "out")
    add(d.loc[d["main_pct"].idxmax(), "code"], d.loc[d["main_pct"].idxmax(), "name"], "in")
    add(d.loc[d["main_pct"].idxmin(), "code"], d.loc[d["main_pct"].idxmin(), "name"], "out")

    shown = 0
    for code, name, tag in picks:
        row = d[d["code"] == code]
        if not len(row):
            continue
        r = row.iloc[0]
        if not (xlim[0] <= r["pct"] <= xlim[1] and ylim[0] <= r["main_pct"] <= ylim[1]):
            continue
        off = (9, 6) if r["main_pct"] >= 0 else (9, -14)
        ax.annotate(name, (r["pct"], r["main_pct"]), fontsize=9.5,
                    color=INK, fontweight="bold",
                    textcoords="offset points", xytext=off,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
        shown += 1

    extreme = d[d["pct"] > 20]
    if len(extreme):
        ex_names = "、".join(extreme.nlargest(2, "pct")["name"].tolist())
        ax.text(0.99, 0.02,
                f"另有 {len(extreme)} 只涨幅超 20%（{ex_names} 等），未在图中显示",
                transform=ax.transAxes, ha="right", fontsize=8.5, color=MUTED)

    ax.set_xlabel("当日涨跌幅（%）", fontsize=11)
    ax.set_ylabel("主力净流入占比（%，净额÷成交额）", fontsize=11)
    ax.set_title(f"{len(d)} 只个股的资金坐标：涨跌幅 × 主力净额占比"
                 f"（{C.DATE}，气泡大小 = 净额绝对值）",
                 fontsize=13, fontweight="bold", color=INK, loc="left", pad=12)
    ax.grid(linestyle="--", alpha=0.3, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.98, 0.97, "涨 · 净流入为正", transform=ax.transAxes, ha="right",
            fontsize=11, color=RED, fontweight="bold")
    ax.text(0.02, 0.97, "跌 · 净流入为正", transform=ax.transAxes, ha="left",
            fontsize=11, color=MUTED, fontweight="bold")
    ax.text(0.98, 0.06, "涨 · 净流入为负", transform=ax.transAxes, ha="right",
            fontsize=11, color=MUTED, fontweight="bold")
    ax.text(0.02, 0.03, "跌 · 净流入为负", transform=ax.transAxes, ha="left",
            fontsize=11, color=GREEN, fontweight="bold")
    fig.tight_layout()
    out = os.path.join(C.OUT_DIR, "全市场资金坐标.png")
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[done] {out}  标注 {shown} 只  坐标 x{xlim} y{ylim}")


# --------------------------------------------------- 瀑布图（资料库附加产出）
def waterfall_plotly(df: pd.DataFrame, top_n=10):
    import plotly.graph_objects as go
    top_in = df.nlargest(top_n, "main_net")
    top_out = df.nsmallest(top_n, "main_net")
    total = df["main_net"].sum() / 1e8
    top20 = (top_in["main_net"].sum() + top_out["main_net"].sum()) / 1e8
    rest = total - top20

    xs = (list(top_in["name"]) + list(top_out["name"])
          + [f"其余{len(df) - 2 * top_n}只合计", "全市场合计"])
    vals = (list(top_in["main_net"] / 1e8) + list(top_out["main_net"] / 1e8)
            + [rest, total])
    colors = ([RED] * top_n + [GREEN] * top_n + ["#BDBDBD", "#6E6E6E"])

    bases, running = [], 0.0
    for v in vals[:-1]:
        bases.append(running if v >= 0 else running + v)
        running += v
    bases.append(0.0)
    heights = [abs(v) for v in vals[:-1]] + [total]

    fig = go.Figure(go.Bar(
        x=xs, y=heights, base=bases, marker_color=colors,
        customdata=vals, text=[f"{v:+.1f}" for v in vals],
        textposition="outside", textfont=dict(size=11),
        hovertemplate="%{x}<br>主力净额 %{customdata:+.2f} 亿元<extra></extra>",
        width=0.62,
    ))
    fig.update_layout(
        title=dict(text=f"A股主力资金流向瀑布图（{C.DATE}，净额Top{top_n}流入/流出，单位：亿元）",
                   font=dict(size=17, color=INK), x=0.01),
        font=dict(family="Microsoft YaHei", size=12, color=INK),
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(title="主力净流入额（亿元）", gridcolor="#EFEFEF"),
        xaxis=dict(tickangle=-40, tickfont=dict(size=11)),
        showlegend=False, margin=dict(l=60, r=30, t=70, b=90),
        width=1180, height=640, bargap=0.3,
    )
    fig.write_image(os.path.join(C.OUT_DIR, "瀑布图_plotly.png"), scale=2)
    fig.write_html(os.path.join(C.OUT_DIR, "瀑布图_交互.html"), include_plotlyjs="cdn")
    print("[done] plotly瀑布图 PNG+HTML（资料库附加，文章未使用）")


if __name__ == "__main__":
    df = C.load_market()
    industry_chart()
    intraday_compare(df)
    scatter_all(df)
    try:
        waterfall_plotly(df)
    except Exception as e:  # noqa: BLE001
        print(f"[skip] 瀑布图未生成（{type(e).__name__}: {e}）")
