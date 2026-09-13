"""案例 27：核密度曲线，带宽决定细节尺度 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(27, "")
df = pd.DataFrame(
    {
        "成绩": np.r_[
            rng.normal(58, 7, 220), rng.normal(82, 5, 180)
        ]
    }
)
for bw, color in zip([0.5, 1, 2], COLORS):
    sns.kdeplot(
        data=df,
        x="成绩",
        bw_adjust=bw,
        cut=0,
        ax=ax,
        label=f"带宽倍率 {bw}",
        color=color,
    )
ax.set(xlabel="模拟测试成绩（分）", ylabel="概率密度（每分）")
ax.legend()
finish(27, "核密度曲线，带宽决定细节尺度", fig, df)
