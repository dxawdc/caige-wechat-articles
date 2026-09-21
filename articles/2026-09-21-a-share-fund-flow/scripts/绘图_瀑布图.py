"""v1.0.0 | 2026-09-20 | 瀑布图：全市场主力净额 Top10 流入 + Top10 流出 + 合计。

红涨绿跌配色（A股习惯：净流入=红，净流出=绿）。
"""
from __future__ import annotations
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 中文字体
for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
           "C:/Windows/Fonts/simhei.ttf"]:
    try:
        font_manager.fontManager.addfont(fp)
    except Exception:
        pass
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

RED = "#D81E06"   # 流入（涨）
GREEN = "#0A9A6A"  # 流出（跌）
GRAY = "#8A8A8A"


def load_clean(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=str)
    for c in ["main_net", "main_pct", "xl_net", "l_net", "m_net", "s_net", "pct"]:
        df[c] = pd.to_numeric(df[c].replace("-", None), errors="coerce")
    df = df.dropna(subset=["main_net"])
    return df


def waterfall(df: pd.DataFrame, out_png: str, top_n: int = 10, date_label: str = "2026-09-18"):
    top_in = df.nlargest(top_n, "main_net")[["name", "main_net"]]
    top_out = df.nsmallest(top_n, "main_net")[["name", "main_net"]]

    # 组装瀑布图序列：流入(正) + 流出(负) + 其余个股桥接 + 合计
    labels = []
    values = []  # 原始值（用于颜色判断）
    kinds = []   # in / out / rest / total
    for _, r in top_in.iterrows():
        labels.append(r["name"]); values.append(r["main_net"]); kinds.append("in")
    for _, r in top_out.iterrows():
        labels.append(r["name"]); values.append(r["main_net"]); kinds.append("out")
    top20_net = sum(values)
    total = df["main_net"].sum()
    rest = total - top20_net
    labels.append(f"其余{len(df)-2*top_n}只合计"); values.append(rest); kinds.append("rest")
    labels.append("全市场净额合计"); values.append(total); kinds.append("total")

    # 计算瀑布图各柱的底部与高度
    y_bottom = []
    y_height = []
    running = 0.0
    for v in values:
        if v >= 0:
            y_bottom.append(running)
            y_height.append(v)
            running += v
        else:
            y_bottom.append(running + v)
            y_height.append(-v)
            running += v
    # 合计柱单独：底部0，高度=total
    y_bottom[-1] = 0.0
    y_height[-1] = total

    x = range(len(labels))
    cmap = {"in": RED, "out": GREEN, "rest": "#B8B8B8", "total": GRAY}
    colors = [cmap[k] for k in kinds]

    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=200)
    ax.bar(x, y_height, bottom=y_bottom, color=colors, width=0.62, zorder=3)

    # 数值标注（亿元）；最后两根大柱标签错开避免碰撞
    for i, (b, h, v) in enumerate(zip(y_bottom, y_height, values)):
        yy = b + h
        txt = f"{v/1e8:+.1f}亿"
        va = "bottom" if v >= 0 else "top"
        off = 0.15 if v >= 0 else -0.15
        if kinds[i] == "rest":
            ax.text(i - 0.38, yy + off, txt, ha="right", va=va, fontsize=7.5,
                    color=colors[i], fontweight="bold")
        elif kinds[i] == "total":
            ax.text(i + 0.38, yy + off, txt, ha="left", va=va, fontsize=7.5,
                    color=colors[i], fontweight="bold")
        else:
            ax.text(i, yy + off, txt, ha="center", va=va, fontsize=7.5,
                    color=colors[i], fontweight="bold")

    ax.axhline(0, color="#333", linewidth=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_title(f"A股主力资金流向瀑布图（{date_label}，主力净额 Top {top_n} 流入 / 流出）",
                 fontsize=13, fontweight="bold")
    ax.yaxis.set_major_formatter(lambda v, p: f"{v/1e8:.0f}亿")
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)

    # 图例
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color=RED, label="主力净流入"),
        Patch(color=GREEN, label="主力净流出"),
        Patch(color="#B8B8B8", label="其余个股合计"),
        Patch(color=GRAY, label="全市场净额合计"),
    ], loc="upper left", fontsize=9, frameon=False)

    fig.tight_layout()
    fig.savefig(out_png, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[done] 瀑布图 -> {out_png}")


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "资金流向_全市场.csv"
    out_png = sys.argv[2] if len(sys.argv) > 2 else "瀑布图_主力资金流.png"
    df = load_clean(csv_path)
    total = df["main_net"].sum()
    print(f"[data] 有效股票数 {len(df)}，主力净额合计 {total/1e8:.2f} 亿元")
    print(f"[stats] 净流入家数 {(df['main_net']>0).sum()}，净流出家数 {(df['main_net']<0).sum()}")
    print(f"[stats] 流入Top10合计 {df.nlargest(10,'main_net')['main_net'].sum()/1e8:.1f} 亿，"
          f"流出Top10合计 {df.nsmallest(10,'main_net')['main_net'].sum()/1e8:.1f} 亿")
    print(f"[stats] 中位数净额 {df['main_net'].median()/1e4:.1f} 万元")
    waterfall(df, out_png)
