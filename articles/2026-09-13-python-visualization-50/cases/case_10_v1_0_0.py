"""案例 10：单位点阵，让交付量变得可数 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(10, "")
df = pd.DataFrame(
    {
        "团队": ["数据", "设计", "研发", "运营"],
        "交付量": [24, 17, 32, 21],
    }
)
for i, row in enumerate(df.itertuples()):
    k = np.arange(row.交付量)
    ax.scatter(
        k % 8, i * 6 + k // 8, s=90, marker="s", color=COLORS[i]
    )
    ax.text(8.2, i * 6 + 1.5, f"{row.交付量} 项", va="center")
ax.set(
    yticks=np.arange(4) * 6 + 1.5,
    yticklabels=df.团队,
    xticks=[],
    xlim=(-1, 11),
    aspect="equal",
)
ax.invert_yaxis()
ax.grid(False)
ax.set_xlabel("每个方块 = 1 项验收交付")
finish(10, "单位点阵，让交付量变得可数", fig, df)
