"""案例 17：排名曲线，只回答位次问题 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(17, "")
df = pd.DataFrame(
    {
        "月份": np.arange(1, 7),
        "甲": [100, 98, 95, 92, 96, 105],
        "乙": [90, 99, 101, 110, 115, 120],
        "丙": [80, 83, 90, 100, 101, 110],
        "丁": [70, 75, 88, 89, 93, 98],
    }
)
rank = df.set_index("月份").rank(
    axis=1, ascending=False, method="min"
)
for i, c in enumerate(rank):
    ax.plot(
        rank.index,
        rank[c],
        "o-",
        lw=2,
        label=c,
        color=COLORS[i],
    )
ax.set(
    yticks=[1, 2, 3, 4],
    xticks=df.月份,
    xlabel="月份",
    ylabel="月收入排名（1为最高）",
    ylim=(4.4, 0.6),
)
ax.legend(ncol=4)
finish(
    17,
    "排名曲线，只回答位次问题",
    fig,
    {"raw": df, "ranks": rank.reset_index()},
)
