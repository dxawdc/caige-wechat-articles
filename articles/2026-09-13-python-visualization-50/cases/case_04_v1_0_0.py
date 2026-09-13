"""案例 04：一次改版，谁的等待时间下降最多 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(4, "")
df = pd.DataFrame(
    {
        "流程": ["注册", "审核", "结算", "退款", "导出"],
        "改版前": [18, 45, 32, 60, 25],
        "改版后": [12, 28, 24, 38, 22],
    }
)
df["减少分钟"] = df.改版前 - df.改版后
df = df.sort_values("减少分钟")
y = np.arange(len(df))
ax.hlines(y, df.改版后, df.改版前, color="#B9C5C0", linewidth=3)
ax.scatter(df.改版前, y, s=95, label="改版前")
ax.scatter(df.改版后, y, s=95, label="改版后")
for i, row in enumerate(df.itertuples()):
    ax.text(
        row.改版前 + 2,
        i,
        f"减少 {row.减少分钟} 分钟",
        va="center",
        fontsize=10,
    )
ax.set(
    yticks=y,
    yticklabels=df.流程,
    xlabel="平均等待时间（分钟）",
    xlim=(0, 88),
)
ax.legend()
finish(4, "一次改版，谁的等待时间下降最多", fig, df)
