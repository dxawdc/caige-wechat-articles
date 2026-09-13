"""案例 02：计划和实际，必须并排看 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(2, "")
df = pd.DataFrame(
    {
        "团队": ["内容", "社群", "产品", "销售"],
        "计划": [120, 100, 90, 140],
        "实际": [132, 86, 108, 129],
    }
)
x = np.arange(len(df))
width = 0.34
for i, col in enumerate(["计划", "实际"]):
    bars = ax.bar(
        x + (i - 0.5) * width, df[col], width, label=col
    )
    ax.bar_label(bars, padding=3)
ax.set(
    xticks=x,
    xticklabels=df.团队,
    ylabel="验收交付量（项）",
    ylim=(0, 165),
)
ax.legend(ncol=2)
finish(
    2,
    "计划和实际，必须并排看",
    fig,
    df,
    {
        "完成率": dict(
            zip(df.团队, (df.实际 / df.计划).round(3))
        )
    },
)
