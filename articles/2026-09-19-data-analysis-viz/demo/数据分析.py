# -*- coding: utf-8 -*-
"""数据分析 —— 用 data-analysis-viz skill 跑完整流程。

流程（对应 skill 的七步工作流）：
  1 接收与对齐 -> 2 数据概览与清洗 -> 3 统计特征提取
  -> 4 关键指标识别 -> 5 图表匹配 -> 6 可视化设计 -> 7 洞察摘要

输出：
  data/clean/*.csv      清洗后数据
  配图/*.png|svg        图表
  输出/统计特征.json    统计特征与关键指标
  输出/洞察摘要.md      决策报告

用法：
    python 数据分析.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SKILL = Path(__file__).resolve().parent.parent / "skill" / "scripts"
if not SKILL.exists():  # 已按 WorkBuddy 目录安装 skill 时使用安装位置
    SKILL = Path.home() / ".workbuddy" / "skills" / "data-analysis-viz" / "scripts"
sys.path.insert(0, str(SKILL))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from viz_style import (  # noqa: E402
    COLORS, DOWN_COLOR, UP_COLOR, add_leader_line, annotate_extremes,
    diverging_cmap, finish, sequential_cmap, setup_style,
)

BASE = Path(__file__).resolve().parent
RAW = BASE / "data" / "raw"
CLEAN = BASE / "data" / "clean"
FIG = BASE / "配图"
OUT = BASE / "输出"
for d in (CLEAN, FIG, OUT):
    d.mkdir(parents=True, exist_ok=True)

FONT = setup_style()
FACTS: dict = {"font": FONT, "cleaning": {}, "stats": {}, "metrics": {}}


def note(key: str, value) -> None:
    FACTS["cleaning"].setdefault(key, []).append(value)


# ==================================================================== 清洗

def clean_channel() -> pd.DataFrame:
    """渠道月度：去重、统一写法、修正单位、插补缺失。"""
    df = pd.read_csv(RAW / "01_渠道月度.csv")
    n0 = len(df)

    dup = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    note("01 渠道月度", f"删除完全重复行 {dup} 行（{n0} → {len(df)}）")

    alias = {"信息流": "信息流广告"}
    hit = df["渠道"].isin(alias)
    df.loc[hit, "渠道"] = df.loc[hit, "渠道"].replace(alias)
    note("01 渠道月度", f"统一渠道写法 {int(hit.sum())} 行：信息流 → 信息流广告")

    # 单位混用：异业合作两行收入被写成万元，量级只有中位数的千分之一
    med = df.loc[df["渠道"] == "异业合作", "收入"].median()
    bad = (df["渠道"] == "异业合作") & (df["收入"] < med / 100)
    df.loc[bad, "收入"] = (df.loc[bad, "收入"] * 10000).round(2)
    note("01 渠道月度", f"修正单位混用 {int(bad.sum())} 行：收入由万元还原为元")

    miss = int(df["曝光量"].isna().sum())
    df["曝光量_是否插补"] = df["曝光量"].isna()
    df["曝光量"] = df["曝光量"].fillna(
        df.groupby("渠道")["曝光量"].transform("median")
    ).round()
    note("01 渠道月度", f"插补缺失曝光量 {miss} 行（按同渠道中位数），并新增插补标记列")

    df.to_csv(CLEAN / "01_渠道月度.csv", index=False, encoding="utf-8-sig")
    return df


def clean_sessions() -> pd.DataFrame:
    """用户使用时长：把误记为毫秒的行还原为秒（真实长尾保留）。"""
    df = pd.read_csv(RAW / "02_用户使用时长.csv")
    err = (df["单次使用时长秒"] > 46800) & (df["单次使用时长秒"] % 1000 == 0)
    n_err = int(err.sum())
    df["单位修正"] = err
    df.loc[err, "单次使用时长秒"] = (df.loc[err, "单次使用时长秒"] // 1000)
    note("02 用户使用时长", f"修正单位错误 {n_err} 行（毫秒误记为秒，除以 1000）")
    note("02 用户使用时长",
         f"保留 {int((df['单次使用时长秒'] > 3600).sum())} 行超过 1 小时的真实长尾，不做剔除")
    df.to_csv(CLEAN / "02_用户使用时长.csv", index=False, encoding="utf-8-sig")
    return df


def passthrough(name: str, src: str) -> pd.DataFrame:
    df = pd.read_csv(RAW / src)
    df.to_csv(CLEAN / src, index=False, encoding="utf-8-sig")
    note(name, "结构完整、未发现需要修正的质量问题，仅导出清洗层")
    return df


# ==================================================================== 统计特征

def describe_skew(s: pd.Series) -> dict:
    s = pd.to_numeric(s, errors="coerce").dropna()
    return {
        "count": int(len(s)),
        "mean": round(float(s.mean()), 2),
        "median": round(float(s.median()), 2),
        "p90": round(float(s.quantile(0.9)), 2),
        "p95": round(float(s.quantile(0.95)), 2),
        "p99": round(float(s.quantile(0.99)), 2),
        "skew": round(float(s.skew()), 2),
        "mean_over_median": round(float(s.mean() / s.median()), 2),
    }


# ==================================================================== 图

def fig01_channel(df: pd.DataFrame) -> None:
    """图1（比较）：各渠道新增用户排序条形图。"""
    agg = (
        df.groupby("渠道", as_index=False)
        .agg(新增用户=("新增用户", "sum"), 曝光量=("曝光量", "sum"))
        .sort_values("新增用户")
    )
    agg["每万次曝光新增"] = (agg["新增用户"] / agg["曝光量"] * 10000).round(2)
    FACTS["stats"]["渠道汇总"] = agg.to_dict("records")

    fig, ax = plt.subplots(figsize=(9, 5.4))
    bars = ax.barh(agg["渠道"], agg["新增用户"], color=COLORS[0], height=0.66)
    top = agg.iloc[-1]
    for b, v in zip(bars, agg["新增用户"]):
        ax.text(v + max(agg["新增用户"]) * 0.012, b.get_y() + b.get_height() / 2,
                f"{v:,}", va="center", fontsize=10, color="#3D4A44")
    bars[-1].set_color(COLORS[2])           # 只突出最大值，其余同色
    ax.set_xlabel("新增用户数（人，12 个月合计）")
    ax.set_xlim(0, max(agg["新增用户"]) * 1.18)
    ax.grid(axis="y", visible=False)
    finish(fig, f"头部渠道贡献超四分之一新增：{top['渠道']} 12 个月累计 {top['新增用户']:,} 人（占 {top['新增用户']/agg['新增用户'].sum():.1%}）",
           agg, out_dir=FIG, stem="图01_渠道新增用户排序",
           metrics={"最高渠道": top["渠道"], "最高新增": int(top["新增用户"])})


def fig02_duration(df: pd.DataFrame) -> None:
    """图2（分布）：单次使用时长分布 —— 均值被长尾拉高的证据。"""
    v = df["单次使用时长秒"]
    st = describe_skew(v)
    FACTS["stats"]["单次使用时长"] = st

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    bins = np.logspace(np.log10(max(v.min(), 1)), np.log10(v.max()), 46)
    ax.hist(v, bins=bins, color=COLORS[0], alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.set_xscale("log")
    ax.axvline(st["mean"], color=COLORS[2], lw=1.8, ls="--", label=f"均值 {st['mean']:.0f} 秒")
    ax.axvline(st["median"], color=UP_COLOR, lw=1.8, ls="-", label=f"中位数 {st['median']:.0f} 秒")
    ax.set_xlabel("单次使用时长（秒，对数轴）")
    ax.set_ylabel("用户数")
    ax.set_title(
        f"分布严重右偏：均值 {st['mean']:.0f} 秒是中位数 {st['median']:.0f} 秒的 "
        f"{st['mean_over_median']:.1f} 倍",
        loc="left", fontsize=12, color="#1C493A")
    ax.legend(loc="upper right", frameon=False)

    ax = axes[1]
    q = [0.5, 0.75, 0.9, 0.95, 0.99]
    vals = [v.quantile(x) for x in q]
    ax.bar([f"P{int(x*100)}" for x in q], vals, color=[COLORS[3]] * 4 + [UP_COLOR], width=0.6)
    for i, val in enumerate(vals):
        ax.text(i, val * 1.02, f"{val:,.0f}", ha="center", fontsize=9.5, color="#3D4A44")
    ax.set_ylabel("单次使用时长（秒）")
    ax.set_ylim(0, max(vals) * 1.15)
    ax.grid(axis="x", visible=False)
    ax.set_title("分位数视角：P99 是 P50 的 %.0f 倍（最高单次时长 %.0f 秒）"
                 % (vals[-1] / vals[0], v.max()), loc="left", fontsize=12, color="#1C493A")

    finish(fig, "12000 名用户的单次使用时长分布", df[["平台", "设备档位", "单次使用时长秒"]],
           out_dir=FIG, stem="图02_使用时长分布",
           metrics={"均值": st["mean"], "中位数": st["median"], "P95": st["p95"],
                    "P99": st["p99"], "偏度": st["skew"]})


def fig03_platform_box(df: pd.DataFrame) -> None:
    """图3（分布的分组对比）：按平台与设备档位看分布差异。"""
    order = ["低端", "中端", "高端"]
    groups = [
        (f"{p}\n{t}", df.loc[(df["平台"] == p) & (df["设备档位"] == t), "单次使用时长秒"].values)
        for p in ["安卓", "iOS"]
        for t in order
    ]
    labels = [g[0] for g in groups]
    data = [g[1] for g in groups]
    FACTS["stats"]["分组中位数"] = {
        lab: round(float(np.median(d)), 1) for lab, d in zip(labels, data)
    }

    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    bp = ax.boxplot(data, orientation="vertical", patch_artist=True, showfliers=False,
                    widths=0.58,
                    medianprops=dict(color="#1C493A", lw=1.6),
                    whiskerprops=dict(color="#8A9691"),
                    capprops=dict(color="#8A9691"),
                    boxprops=dict(edgecolor="#8A9691", lw=0.9))
    for i, patch in enumerate(bp["boxes"]):
        patch.set_facecolor(COLORS[0] if i < 3 else COLORS[1])
        patch.set_alpha(0.85)
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("单次使用时长（秒）")
    ax.set_yscale("log")
    ax.grid(axis="x", visible=False)
    ax.legend(handles=[Patch(facecolor=COLORS[0], label="安卓"),
                       Patch(facecolor=COLORS[1], label="iOS")],
              loc="upper left", frameon=False, ncol=2)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, p: f"{v:,.0f}"))
    md_ios = np.median(np.concatenate([d for lab, d in zip(labels, data) if lab.startswith("iOS")]))
    md_and = np.median(np.concatenate([d for lab, d in zip(labels, data) if lab.startswith("安卓")]))
    ax.set_title(f"同一档位下 iOS 中位时长都更高（整体中位 {md_ios:.0f} 秒 vs 安卓 {md_and:.0f} 秒，"
                 f"高 {md_ios/md_and - 1:+.0%}）；两种系统内部都是高端机略高于低端机",
                 loc="left", fontsize=11.5, color="#1C493A", pad=10)

    out = df.groupby(["平台", "设备档位"])["单次使用时长秒"].agg(
        ["count", "median", lambda s: s.quantile(0.95)]).reset_index()
    out.columns = ["平台", "设备档位", "用户数", "中位数", "P95"]
    finish(fig, "不同平台与设备档位的使用时长分布（箱线图，已排除离群点显示）", out,
           out_dir=FIG, stem="图03_平台设备时长分布")


def fig04_trend(df: pd.DataFrame) -> None:
    """图4（趋势）：月度订单量折线 + 环比增速下降的拐点。"""
    df = df.copy()
    df["dt"] = pd.to_datetime(df["月份"])
    y = df["订单量"].values.astype(float)
    n = len(y)
    mom = np.diff(y) / y[:-1]                       # 环比增速
    mom_s = pd.Series(mom).rolling(3, center=True).mean()
    g1 = float(mom[:23].mean())
    g2 = float(mom[23:].mean())
    m1 = df.loc[:11, "订单量"].mean()
    m2 = df.loc[24:, "订单量"].mean()
    FACTS["stats"]["月度订单"] = {
        "总增长倍数": round(float(y[-1] / y[0]), 2),
        "前24月平均环比": round(g1 * 100, 2),
        "后12月平均环比": round(g2 * 100, 2),
        "前12月月均订单": round(float(m1)),
        "后12月月均订单": round(float(m2)),
    }

    fig, axes = plt.subplots(2, 1, figsize=(10, 6.6), sharex=True,
                             gridspec_kw={"height_ratios": [2.1, 1]})
    ax = axes[0]
    ax.plot(df["dt"], y, color=COLORS[1], lw=1.9, marker="o", ms=3.2,
            markerfacecolor="white", markeredgewidth=1.1)
    change = df["dt"].iloc[24]
    ax.axvline(change, color="#9AA5A0", lw=1.0, ls=":")
    add_leader_line(ax, (change, y[24]),
                    f"第 25 个月起增速换挡\n平均环比由 +{g1:.1%} 降至 +{g2:.1%}",
                    xytext=(-172, 46), color=UP_COLOR)
    ax.set_ylabel("订单量（单）")
    ax.yaxis.set_major_formatter(lambda v, p: f"{v/1000:,.0f}k")
    ax.grid(axis="x", visible=False)
    ax.set_title(f"36 个月订单量涨到最初的 {y[-1]/y[0]:.1f} 倍，但增量集中在前两年",
                 loc="left", fontsize=12, color="#1C493A", pad=10)

    ax = axes[1]
    ax.bar(df["dt"][1:], mom * 100, width=22, color="#C9D8D3", label="当月环比")
    ax.plot(df["dt"][1:], mom_s * 100, color=COLORS[0], lw=1.8, label="3 个月移动平均")
    ax.axhline(g1 * 100, color=COLORS[3], lw=1.2, ls="--", label=f"前 24 月均值 {g1:.1%}")
    ax.axvline(change, color="#9AA5A0", lw=1.0, ls=":")
    ax.axhline(g2 * 100, color=UP_COLOR, lw=1.2, ls="--", label=f"后 12 月均值 {g2:.1%}")
    ax.set_ylabel("环比增速（%）")
    ax.legend(loc="upper right", frameon=False, fontsize=9.5, ncol=2)
    ax.grid(axis="x", visible=False)

    finish(fig, "月度订单量趋势与环比增速（上下对齐双子图，共享时间轴）",
           df[["月份", "订单量"]], out_dir=FIG, stem="图04_月度订单趋势",
           metrics=FACTS["stats"]["月度订单"])


def fig05_simpson(df: pd.DataFrame) -> None:
    """图5（相关性）：总体回归与分组回归方向不一致 —— 辛普森悖论。"""
    x_, y_ = df["人均可支配收入万元"].values, df["人均线上消费额万元"].values
    r_all = float(np.corrcoef(x_, y_)[0, 1])
    k_all = float(np.polyfit(x_, y_, 1)[0])
    per = {}
    for reg, g in df.groupby("区域"):
        per[reg] = {
            "n": int(len(g)),
            "r": round(float(np.corrcoef(g["人均可支配收入万元"], g["人均线上消费额万元"])[0, 1]), 3),
            "k": round(float(np.polyfit(g["人均可支配收入万元"], g["人均线上消费额万元"], 1)[0]), 3),
        }
    FACTS["stats"]["城市相关性"] = {"总体": {"n": len(df), "r": round(r_all, 3), "斜率": round(k_all, 3)},
                                    "分组": per}

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.0), sharey=True)
    ax = axes[0]
    ax.scatter(x_, y_, s=22, color="#9AA5A0", alpha=0.75, edgecolors="white", linewidths=0.3)
    xs = np.linspace(x_.min(), x_.max(), 50)
    ax.plot(xs, np.polyval(np.polyfit(x_, y_, 1), xs), color=UP_COLOR, lw=2)
    ax.set_title(f"（a）不分组：r = {r_all:.2f}，斜率 {k_all:.2f}\n"
                 f"斜率被明显压平，看起来“收入涨一点，消费只涨一点点”",
                 loc="left", fontsize=11, color="#1C493A")
    ax.set_xlabel("人均可支配收入（万元）")
    ax.set_ylabel("人均线上消费额（万元）")

    ax = axes[1]
    ks = []
    for i, (reg, g) in enumerate(df.groupby("区域")):
        ax.scatter(g["人均可支配收入万元"], g["人均线上消费额万元"], s=22,
                   color=COLORS[i], alpha=0.8, edgecolors="white", linewidths=0.3, label=reg)
        xs = np.linspace(g["人均可支配收入万元"].min(), g["人均可支配收入万元"].max(), 30)
        k = float(np.polyfit(g["人均可支配收入万元"], g["人均线上消费额万元"], 1)[0])
        ks.append(k)
        ax.plot(xs, np.polyval(np.polyfit(g["人均可支配收入万元"], g["人均线上消费额万元"], 1), xs),
                color=COLORS[i], lw=2, ls="--")
    ax.legend(loc="lower right", frameon=False)
    ax.set_title(f"（b）按区域拆开：组内斜率 {ks[0]:.2f} / {ks[1]:.2f} / {ks[2]:.2f}\n"
                 f"每一组内部都比总体更陡 —— 典型的辛普森悖论",
                 loc="left", fontsize=11, color="#1C493A")
    ax.set_xlabel("人均可支配收入（万元）")

    finish(fig, "300 个城市的收入与线上消费：同一份数据，两种结论", df,
           out_dir=FIG, stem="图05_城市收入与消费",
           metrics=FACTS["stats"]["城市相关性"])


def fig06_pareto(df: pd.DataFrame) -> None:
    """图6（集中度）：用户消费帕累托图。"""
    user = df.groupby("用户ID", as_index=False)["订单金额"].sum().sort_values(
        "订单金额", ascending=False).reset_index(drop=True)
    user["累计占比"] = user["订单金额"].cumsum() / user["订单金额"].sum()
    n = len(user)
    k10 = int(round(n * 0.10))
    share10 = float(user["累计占比"].iloc[k10 - 1])
    k1 = int(round(n * 0.01))
    share1 = float(user["累计占比"].iloc[k1 - 1])
    FACTS["stats"]["订单集中度"] = {
        "用户数": n, "订单数": int(len(df)),
        "前1%用户金额占比": round(share1 * 100, 1),
        "前10%用户金额占比": round(share10 * 100, 1),
        "金额中位数": round(float(df["订单金额"].median()), 2),
        "金额P95": round(float(df["订单金额"].quantile(0.95)), 2),
    }

    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    step = max(1, n // 600)
    idx = np.arange(n)[::step]
    ax.bar(idx, user["订单金额"].values[::step], width=step * 0.92,
           color="#C9D8D3", edgecolor="none")
    ax.set_xlabel("用户（按消费额降序排列）")
    ax.set_ylabel("消费额（元，对数轴）")
    ax.set_yscale("log")
    ax.set_xlim(-n * 0.01, n * 1.02)
    ax2 = ax.twinx()
    ax2.plot(np.arange(n), user["累计占比"].values * 100, color=COLORS[0], lw=2)
    ax2.axvline(k10, color=UP_COLOR, lw=1.2, ls=":")
    ax2.annotate(f"前 10% 用户（{k10:,} 人）\n贡献 {share10*100:.1f}% 金额",
                 xy=(x100 := k10, share10 * 100), xytext=(x100 + n * 0.17, 40),
                 fontsize=10, color=UP_COLOR,
                 arrowprops=dict(arrowstyle="->", color=UP_COLOR, lw=1.2))
    # 直接在图形旁标注，不用图例（图例离数据越近越好）
    ax2.text(n * 0.99, 96, "累计金额占比", color=COLORS[0], fontsize=10,
             ha="right", va="center", fontweight="bold")
    ax.text(n * 0.55, 9e4, "单个用户消费额", color="#8FA39C", fontsize=10,
            ha="center", va="center")
    ax2.set_ylabel("累计金额占比（%）")
    ax2.set_ylim(0, 108)
    ax2.grid(False)
    ax.set_title(f"消费高度集中：前 10% 用户（{k10:,} 人）贡献了 {share10*100:.0f}% 的流水",
                 loc="left", fontsize=12, color="#1C493A", pad=10)
    finish(fig, "20 万笔订单的用户消费分布（帕累托图）",
           pd.DataFrame({"用户排名": np.arange(1, n + 1),
                         "消费额": user["订单金额"].values,
                         "累计占比": user["累计占比"].values}),
           out_dir=FIG, stem="图06_用户消费帕累托",
           metrics=FACTS["stats"]["订单集中度"])


def fig07_heatmap(df: pd.DataFrame) -> None:
    """图7（分类×分类）：星期 × 小时的活跃分布热力图。"""
    pivot = df.pivot_table(index="星期", columns="小时", values="活跃用户数", aggfunc="sum")
    order = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    pivot = pivot.reindex(order)
    mat = pivot.values
    wk = pivot.iloc[:5].mean(axis=0)
    we = pivot.iloc[5:].mean(axis=0)
    peak_wk, peak_we = int(wk.idxmax()), int(we.idxmax())
    # 工作日午间峰：上午 10 点到下午 3 点之间的局部最高
    noon = int(wk.loc[10:15].idxmax())
    FACTS["stats"]["活跃时段"] = {
        "工作日晚间峰值小时": peak_wk,
        "工作日午间峰值小时": noon,
        "周末峰值小时": peak_we,
        "单位": "人（周合计）",
    }

    fig, ax = plt.subplots(figsize=(11.5, 4.2))
    im = ax.imshow(mat, aspect="auto", cmap=sequential_cmap(), interpolation="nearest")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h:02d}" for h in range(0, 24, 2)])
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order)
    ax.set_xlabel("小时")
    ax.grid(False)
    # 每天峰值用白圈标出；结论写在标题里，不在图上重复标注
    for i, wd in enumerate(order):
        j = int(np.argmax(mat[i]))
        ax.scatter([j], [i], s=70, facecolor="none", edgecolor="white", linewidth=1.6)
    cb = fig.colorbar(im, ax=ax, pad=0.012)
    cb.set_label("活跃用户数（周合计）", fontsize=10)
    ax.set_title(f"工作日双峰（{noon} 时、{peak_wk} 时），周末合并成一个峰并整体后移到 {peak_we} 时",
                 loc="left", fontsize=12, color="#1C493A", pad=10)
    finish(fig, "一周内各小时的活跃用户分布", pivot.reset_index(),
           out_dir=FIG, stem="图07_活跃时段热力图",
           metrics=FACTS["stats"]["活跃时段"])


def fig08_mix(df: pd.DataFrame) -> None:
    """图8（复合目的）：品类构成的 100% 堆叠面积图。"""
    df = df.copy()
    df["dt"] = pd.to_datetime(df["月份"])
    pivot = df.pivot_table(index="dt", columns="品类", values="销售额", aggfunc="sum")
    share = pivot.div(pivot.sum(axis=1), axis=0) * 100
    first, last = share.iloc[0], share.iloc[-1]
    delta = (last - first).sort_values()
    FACTS["stats"]["品类构成"] = {
        "起始月": share.index[0].strftime("%Y-%m"),
        "结束月": share.index[-1].strftime("%Y-%m"),
        "升幅最大": f"{delta.index[-1]} +{delta.iloc[-1]:.1f}pct",
        "降幅最大": f"{delta.index[0]} {delta.iloc[0]:.1f}pct",
    }

    fig, ax = plt.subplots(figsize=(10.2, 5.2))
    ax.stackplot(share.index, *[share[c].values for c in share.columns],
                 labels=list(share.columns), colors=COLORS, alpha=0.92)
    for c, col in zip(share.columns, COLORS):
        mid = share[c].iloc[-1] / 2 + share[list(share.columns)[:list(share.columns).index(c)]].iloc[-1].sum()
        ax.text(share.index[-1], mid, f"{share[c].iloc[-1]:.0f}%", fontsize=9.5,
                color="white", ha="right", va="center")
    ax.set_ylim(0, 100)
    ax.set_ylabel("销售额占比（%）")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=6, frameon=False, fontsize=9.5)
    ax.set_title(f"日用百货占比从 {first['日用百货']:.0f}% 降到 {last['日用百货']:.0f}%，"
                 f"数码家电从 {first['数码家电']:.0f}% 升到 {last['数码家电']:.0f}%",
                 loc="left", fontsize=12, color="#1C493A", pad=10)
    finish(fig, "六个品类的销售额构成变化（100% 堆叠面积图）", share.reset_index(),
           out_dir=FIG, stem="图08_品类构成变化",
           metrics=FACTS["stats"]["品类构成"])


# ==================================================================== 主流程

def main() -> None:
    print("[1] 接收与对齐：7 套数据，覆盖 比较/分布/趋势/相关性/集中度/分类×分类/复合")
    print("[2] 数据概览与清洗")
    ch = clean_channel()
    se = clean_sessions()
    mo = passthrough("03 月度经营", "03_月度经营.csv")
    ci = passthrough("04 城市指标", "04_城市指标.csv")
    od = passthrough("05 订单流水", "05_订单流水.csv")
    hr = passthrough("06 活跃时段", "06_活跃时段.csv")
    cm = passthrough("07 品类构成", "07_品类构成.csv")

    print("[3][4] 统计特征与关键指标")
    print("[5][6] 图表匹配与生成")
    fig01_channel(ch)
    fig02_duration(se)
    fig03_platform_box(se)
    fig04_trend(mo)
    fig05_simpson(ci)
    fig06_pareto(od)
    fig07_heatmap(hr)
    fig08_mix(cm)

    (OUT / "统计特征.json").write_text(
        json.dumps(FACTS, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("[7] 输出 ->", OUT / "统计特征.json")


if __name__ == "__main__":
    main()
