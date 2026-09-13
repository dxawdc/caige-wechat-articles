"""案例 05：两个月之间，渠道排名如何互换 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(5, "")
df = pd.DataFrame(
    {
        "渠道": ["搜索", "社群", "视频", "推荐"],
        "一月": [36, 28, 18, 24],
        "六月": [30, 39, 34, 21],
    }
)
for i, row in enumerate(df.itertuples()):
    ax.plot(
        [0, 1],
        [row.一月, row.六月],
        "o-",
        color=COLORS[i],
        lw=2,
    )
    ax.text(
        -0.08,
        row.一月,
        f"{row.渠道} {row.一月}",
        ha="right",
        va="center",
    )
    ax.text(
        1.08, row.六月, f"{row.六月} {row.渠道}", va="center"
    )
ax.set(
    xticks=[0, 1],
    xticklabels=["一月", "六月"],
    xlim=(-0.6, 1.6),
    ylim=(14, 43),
    ylabel="新客户收入（万元）",
)
finish(5, "两个月之间，渠道排名如何互换", fig, df)
