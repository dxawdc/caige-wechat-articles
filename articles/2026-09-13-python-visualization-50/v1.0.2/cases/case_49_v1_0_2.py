"""案例 49：日数据汇总为月均值，缺测不能当零 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, axes = start(
    49,
    "",
    size=(9, 6),
    nrows=2,
    gridspec_kw={"height_ratios": [2, 1]},
)
dates = pd.date_range("2025-01-01", "2025-12-31")
n = len(dates)
df = pd.DataFrame(
    {
        "日期": dates,
        "读数": 50
        + 18 * np.cos(np.arange(n) / 365 * 2 * np.pi)
        + rng.normal(0, 6, n),
    }
)
df.loc[df.日期.dt.month == 6, "读数"] = np.nan
df.loc[
    (df.日期.dt.month == 9) & (df.日期.dt.day < 17), "读数"
] = np.nan
monthly = (
    df.set_index("日期")
    .resample("MS")
    .读数.agg(["mean", "count", "size"])
)
monthly["coverage"] = monthly["count"] / monthly["size"]
monthly["shown"] = monthly["mean"].where(
    monthly.coverage >= 0.8
)
assert monthly.loc["2025-06-01", "count"] == 0 and pd.isna(
    monthly.loc["2025-06-01", "shown"]
)
axes[0].plot(monthly.index, monthly.shown, "o-", lw=2)
axes[0].set_ylabel("传感器月均读数（单位）")
axes[1].bar(
    monthly.index,
    monthly.coverage * 100,
    width=20,
    color=np.where(
        monthly.coverage >= 0.8, COLORS[0], COLORS[4]
    ),
)
axes[1].axhline(80, ls="--", color="#777777")
axes[1].set(
    ylabel="覆盖率（%）",
    ylim=(0, 110),
    xlabel="月份；低于80%不展示月均值",
)
fig.autofmt_xdate()
finish(
    49,
    "日数据汇总为月均值，缺测不能当零",
    fig,
    {"daily": df, "monthly": monthly.reset_index()},
)
