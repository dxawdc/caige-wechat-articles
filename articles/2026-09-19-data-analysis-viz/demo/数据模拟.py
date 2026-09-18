# -*- coding: utf-8 -*-
"""数据模拟 —— 为《数据分析与可视化 Skill》一文构造多套演示数据。

设计意图：覆盖不同数据规模、不同分布形态、不同分析意图，
用来实测 skill 的"数据体检 → 统计特征 → 关键指标 → 图表匹配"流程。

所有数据均为程序生成的模拟数据，不含任何真实业务信息。

用法：
    python 数据模拟.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

SEED = 20260919


def _rng(offset: int) -> np.random.Generator:
    return np.random.default_rng(SEED + offset)


def _save(df: pd.DataFrame, name: str, summary: dict) -> None:
    path = RAW / f"{name}.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[OK] {name}.csv  {df.shape[0]} 行 × {df.shape[1]} 列  {summary.get('intent', '')}")


# ------------------------------------------------------------------ D1 渠道月度
# 场景：小规模、干净、用于"比较"。但故意埋入一个单位混用与一个空值，
# 让数据体检有实际发现。
def make_channels() -> pd.DataFrame:
    rng = _rng(1)
    months = pd.date_range("2025-10-01", periods=12, freq="MS").strftime("%Y-%m")
    channels = ["应用商店", "信息流广告", "短视频达人", "老客推荐", "搜索品牌词", "内容社区", "线下活动", "异业合作"]
    # 各渠道的曝光基数与转化能力不同：有的量大质差，有的量小质优
    exposure_base = [480000, 320000, 760000, 42000, 96000, 58000, 22000, 15000]
    ctr_base = [0.031, 0.024, 0.011, 0.082, 0.061, 0.048, 0.071, 0.055]
    cvr_base = [0.042, 0.020, 0.038, 0.115, 0.088, 0.062, 0.045, 0.052]
    arpu_base = [42, 61, 33, 128, 96, 74, 68, 80]

    rows = []
    for mi, month in enumerate(months):
        season = 1 + 0.18 * np.sin((mi + 2) / 12 * 2 * np.pi)   # 年末走高
        for ci, ch in enumerate(channels):
            exposure = int(exposure_base[ci] * season * rng.normal(1, 0.06))
            clicks = int(exposure * ctr_base[ci] * rng.normal(1, 0.09))
            new_users = int(clicks * cvr_base[ci] * rng.normal(1, 0.12))
            revenue = round(new_users * arpu_base[ci] * rng.normal(1, 0.10), 2)
            rows.append(
                {
                    "月份": month,
                    "渠道": ch,
                    "曝光量": exposure,
                    "点击量": clicks,
                    "新增用户": new_users,
                    "收入": revenue,
                }
            )
    df = pd.DataFrame(rows)

    # ---- 刻意埋入的质量问题（模拟真实数据常态）
    # 1) 单位混用：把"异业合作"两行的收入写成"万元"，少两个数量级
    bad = (df["渠道"] == "异业合作") & (df["月份"].isin(["2026-01", "2026-02"]))
    df.loc[bad, "收入"] = (df.loc[bad, "收入"] / 10000).round(2)
    # 2) 缺失：三行曝光量缺失
    df.loc[[5, 33, 71], "曝光量"] = np.nan
    # 3) 重复：整行重复 6 行
    df = pd.concat([df, df.sample(6, random_state=SEED)], ignore_index=True)
    # 4) 渠道名写法不一：把部分"信息流广告"写成"信息流"
    df.loc[df.index % 7 == 0, "渠道"] = df.loc[df.index % 7 == 0, "渠道"].replace(
        {"信息流广告": "信息流"}
    )
    return df


# ------------------------------------------------------------------ D2 用户使用时长
# 场景：中等规模、严重右偏长尾，且两平台分布形态不同（多峰的近亲）。
def make_sessions() -> pd.DataFrame:
    rng = _rng(2)
    n = 12000
    platform = rng.choice(["安卓", "iOS"], size=n, p=[0.66, 0.34])
    tier = np.where(
        platform == "安卓",
        rng.choice(["低端", "中端", "高端"], n, p=[0.42, 0.44, 0.14]),
        rng.choice(["低端", "中端", "高端"], n, p=[0.12, 0.58, 0.30]),
    )

    # 安卓：长尾更长；iOS：整体更高且更集中
    base = np.where(
        platform == "安卓",
        rng.lognormal(mean=5.40, sigma=1.20, size=n),
        rng.lognormal(mean=5.72, sigma=0.92, size=n),
    )
    tier_factor = np.select(
        [tier == "低端", tier == "中端", tier == "高端"], [0.86, 1.0, 1.20], default=1.0
    )
    seconds = base * tier_factor

    # 少量极端重度用户（真实长尾，不是脏数据）
    heavy = rng.random(n) < 0.010
    seconds = np.where(heavy, seconds * rng.uniform(5, 16, size=n), seconds)
    seconds = np.clip(seconds, 5, 43200).round().astype(int)

    sessions = np.where(platform == "安卓", rng.poisson(4.6, n), rng.poisson(6.4, n)) + 1
    paid = (rng.random(n) < np.where(platform == "安卓", 0.041, 0.072)).astype(int)

    # 混入输入错误：少量"秒"写成"毫秒"
    err = rng.random(n) < 0.003
    seconds = np.where(err, seconds * 1000, seconds)

    return pd.DataFrame(
        {
            "用户ID": [f"U{i:06d}" for i in range(n)],
            "平台": platform,
            "设备档位": tier,
            "单次使用时长秒": seconds,
            "周会话次数": sessions,
            "是否付费": paid,
        }
    )


# ------------------------------------------------------------------ D3 月度经营
# 场景：时序数据，有季节性，第 25 个月起出现增速拐点。
def make_monthly() -> pd.DataFrame:
    rng = _rng(3)
    months = pd.date_range("2023-10-01", periods=36, freq="MS")
    rows = []
    log_orders = float(np.log(82000))
    for i, m in enumerate(months):
        growth = 0.028 if i < 24 else 0.006          # 第 25 个月起增速骤降
        log_orders += float(np.log(1 + growth))
        seasonal = 1 + 0.13 * np.sin((m.month - 3) / 12 * 2 * np.pi)
        orders = np.exp(log_orders) * seasonal * rng.normal(1, 0.035)
        freq = rng.normal(3.05, 0.06)                # 人均月下单次数
        rows.append(
            {
                "月份": m.strftime("%Y-%m"),
                "订单量": int(orders),
                "活跃用户": int(orders / freq),
                "客单价": round(rng.normal(126, 4.2) * (1 + 0.02 * (i > 24)), 2),
            }
        )
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ D4 城市指标
# 场景：多变量。刻意构造"分层导致的辛普森悖论"：
# 每个区域内部人均收入与线上消费额都是正相关，
# 但把三个区域混在一起看，斜率会明显变平（甚至变负）。
def make_cities() -> pd.DataFrame:
    rng = _rng(4)
    regions = {
        # 区域: (城市数, 人均收入均值, 收入离散, 组内截距, 组内斜率)
        # 截距与收入水平反向设置：收入越低的区域，同样收入下线上消费越高，
        # 于是把三个区域混在一起做回归时，斜率会被"压平"，形成辛普森悖论。
        "东部": (120, 7.6, 1.9, 0.35, 0.95),
        "中部": (100, 4.8, 1.3, 2.10, 0.86),
        "西部": (80, 3.9, 1.2, 3.30, 0.78),
    }
    rows = []
    for region, (cnt, mu, sd, intercept, slope) in regions.items():
        income = np.clip(rng.normal(mu, sd, cnt), 1.6, 15.0)
        spend = intercept + slope * income + rng.normal(0, 0.28, cnt)
        population = np.clip(rng.lognormal(4.6, 0.62, cnt), 18, 2200).round()
        logistics = np.clip(3.4 - 0.11 * income + rng.normal(0, 0.35, cnt), 0.8, 4.5)
        online_rate = np.clip(0.30 + 0.052 * income + rng.normal(0, 0.035, cnt), 0.05, 0.95)
        rows.append(
            pd.DataFrame(
                {
                    "区域": region,
                    "人均可支配收入万元": income.round(3),
                    "人均线上消费额万元": np.clip(spend, 0.2, None).round(3),
                    "常住人口万人": population,
                    "物流成本指数": logistics.round(3),
                    "线上渗透率": online_rate.round(4),
                }
            )
        )
    df = pd.concat(rows, ignore_index=True)
    df.insert(0, "城市ID", [f"C{i:04d}" for i in range(len(df))])
    return df


# ------------------------------------------------------------------ D5 订单流水
# 场景：大规模、高基数。金额高度集中：前 10% 用户贡献大部分流水。
def make_orders() -> pd.DataFrame:
    rng = _rng(5)
    n_users = 50000
    # 用户下单倾向服从重尾分布：前 10% 用户约贡献五成流水
    user_scale = rng.pareto(2.0, n_users) + 1.0
    weights = user_scale / user_scale.sum()
    n_orders = 200000

    user_idx = rng.choice(n_users, size=n_orders, p=weights)
    ts = pd.to_datetime("2026-01-01") + pd.to_timedelta(
        rng.integers(0, 181 * 24 * 3600, n_orders), unit="s"
    )
    amount = np.clip(
        rng.lognormal(4.45, 0.95, n_orders) * user_scale[user_idx] ** 0.22, 5, 60000
    )
    cats = rng.choice(
        ["日用百货", "数码家电", "服饰鞋包", "食品生鲜", "美妆个护", "家居建材", "图书文娱"],
        n_orders, p=[0.26, 0.14, 0.18, 0.21, 0.10, 0.06, 0.05],
    )
    channel = rng.choice(["自然流量", "搜索", "推荐", "活动"], n_orders, p=[0.34, 0.22, 0.29, 0.15])
    return pd.DataFrame(
        {
            "订单号": [f"O{i:08d}" for i in range(n_orders)],
            "用户ID": [f"U{j:06d}" for j in user_idx],
            "下单时间": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "订单金额": amount.round(2),
            "品类": cats,
            "来源渠道": channel,
        }
    )


# ------------------------------------------------------------------ D6 活跃时段
# 场景：分类 × 分类，用于热力图。工作日双峰，周末单峰且后移。
def make_hourly() -> pd.DataFrame:
    rng = _rng(6)
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    rows = []
    for wi, wd in enumerate(weekdays):
        weekend = wi >= 5
        for h in range(24):
            if weekend:
                # 周末：一个更晚、更宽的单峰，午后只有轻微抬升
                base = 33000 * (
                    0.40
                    + 2.05 * np.exp(-((h - 21.9) ** 2) / 24.0)
                    + 0.28 * np.exp(-((h - 13.2) ** 2) / 18.0)
                )
            else:
                # 工作日：午间 + 晚间双峰
                base = 34000 * (
                    0.36
                    + 1.15 * np.exp(-((h - 12.4) ** 2) / 4.6)
                    + 1.85 * np.exp(-((h - 21.1) ** 2) / 7.2)
                )
            rows.append(
                {
                    "星期": wd,
                    "小时": h,
                    "活跃用户数": int(base * rng.normal(1, 0.035)),
                }
            )
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ D7 品类构成
# 场景：复合目的（趋势 + 构成）。某品类占比持续上升，另一个持续下降。
def make_category_mix() -> pd.DataFrame:
    rng = _rng(7)
    months = pd.date_range("2024-10-01", periods=24, freq="MS").strftime("%Y-%m")
    # (起始份额, 每月份额变化)
    plan = {
        "日用百货": (0.31, -0.0034),
        "食品生鲜": (0.22, 0.0012),
        "服饰鞋包": (0.19, -0.0009),
        "数码家电": (0.14, 0.0021),
        "美妆个护": (0.09, 0.0006),
        "图书文娱": (0.05, 0.0004),
    }
    total = 1_350_000.0
    rows = []
    for mi, month in enumerate(months):
        total *= 1 + 0.021
        season = 1 + 0.10 * np.sin((mi % 12 + 3) / 12 * 2 * np.pi)
        shares = {k: v[0] + v[1] * mi for k, v in plan.items()}
        s = sum(shares.values())
        for cat, share in shares.items():
            rows.append(
                {
                    "月份": month,
                    "品类": cat,
                    "销售额": round(total * season * share / s * rng.normal(1, 0.03), 2),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    print("生成模拟数据（seed=%d）..." % SEED)
    _save(make_channels(), "01_渠道月度", {"intent": "比较 / 占比"})
    _save(make_sessions(), "02_用户使用时长", {"intent": "分布"})
    _save(make_monthly(), "03_月度经营", {"intent": "趋势"})
    _save(make_cities(), "04_城市指标", {"intent": "相关性"})
    _save(make_orders(), "05_订单流水", {"intent": "集中度"})
    _save(make_hourly(), "06_活跃时段", {"intent": "分类×分类"})
    _save(make_category_mix(), "07_品类构成", {"intent": "趋势+构成"})
    print("完成 ->", RAW)


if __name__ == "__main__":
    main()
