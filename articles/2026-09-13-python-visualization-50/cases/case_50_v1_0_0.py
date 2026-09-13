"""案例 50：均值之外，补上不确定性的范围 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

from scipy.stats import t, sem

rng, fig, ax = start(50, "")
df = pd.DataFrame(
    {
        "组别": np.repeat(["甲", "乙", "丙", "丁"], 40),
        "耗时": np.r_[
            rng.normal(20, 4, 40),
            rng.normal(22, 7, 40),
            rng.normal(19, 3, 40),
            rng.normal(24, 5, 40),
        ],
    }
)
summary = df.groupby("组别", sort=False).耗时.agg(
    ["mean", "std", "count"]
)
summary["halfwidth"] = (
    t.ppf(0.975, summary["count"] - 1)
    * summary["std"]
    / np.sqrt(summary["count"])
)
for name, g in df.groupby("组别", sort=False):
    assert np.isclose(
        summary.loc[name, "halfwidth"],
        t.ppf(0.975, len(g) - 1) * sem(g.耗时),
    )
ax.errorbar(
    summary["mean"],
    np.arange(4),
    xerr=summary.halfwidth,
    fmt="o",
    capsize=6,
    ms=8,
    color=COLORS[0],
)
ax.set(
    yticks=np.arange(4),
    yticklabels=summary.index,
    xlabel="任务耗时均值及95% t置信区间（分钟）",
)
finish(
    50,
    "均值之外，补上不确定性的范围",
    fig,
    {"raw": df, "summary": summary.reset_index()},
    {
        "置信水平": 0.95,
        "区间对象": "总体均值",
        "每组独立样本": 40,
        "重复测量": False,
    },
)
