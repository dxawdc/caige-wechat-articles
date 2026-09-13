"""案例 23：马赛克图同时看分组规模与组内占比 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

from matplotlib.patches import Rectangle

rng, fig, ax = start(23, "")
df = pd.DataFrame(
    {
        "渠道": ["搜索", "社群", "视频"],
        "付费": [180, 160, 60],
        "未付费": [420, 240, 440],
    }
)
grand = df[["付费", "未付费"]].to_numpy().sum()
x = 0
area = 0
for row in df.itertuples():
    total = row.付费 + row.未付费
    width = total / grand
    y = 0
    for k, col in enumerate(["付费", "未付费"]):
        value = getattr(row, col)
        height = value / total
        ax.add_patch(
            Rectangle(
                (x, y),
                width,
                height,
                facecolor=COLORS[k],
                edgecolor="white",
                lw=3,
            )
        )
        ax.text(
            x + width / 2,
            y + height / 2,
            f"{col} {height:.0%}",
            ha="center",
            va="center",
            color="white",
        )
        y += height
        area += width * height
    ax.text(
        x + width / 2,
        -0.08,
        f"{row.渠道}（{total}人）",
        ha="center",
    )
    x += width
assert np.isclose(area, 1)
ax.set(
    xlim=(0, 1), ylim=(-0.15, 1), xticks=[], ylabel="组内比例"
)
ax.grid(False)
finish(
    23,
    "马赛克图同时看分组规模与组内占比",
    fig,
    df,
    {"总样本": int(grand)},
)
