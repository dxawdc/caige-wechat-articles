"""案例 26：直方图，先看长尾再谈平均值 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(26, "")
df = pd.DataFrame({"时长": rng.lognormal(2.3, 0.65, 800)})
counts, bins, _ = ax.hist(
    df.时长, bins=24, color=COLORS[0], edgecolor="white"
)
ax.axvline(
    df.时长.median(),
    color=COLORS[2],
    ls="--",
    label=f"中位数 {df.时长.median():.1f} 分钟",
)
assert counts.sum() == len(df)
ax.set(xlabel="单次学习时长（分钟）", ylabel="会话数（次）")
ax.legend()
finish(
    26,
    "直方图，先看长尾再谈平均值",
    fig,
    df,
    {
        "均值": df.时长.mean(),
        "中位数": df.时长.median(),
        "直方图计数": counts.sum(),
    },
)
