"""案例 24：华夫图把百分数还原成一百个格子 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

from matplotlib.patches import Patch

rng, fig, ax = start(24, "", size=(6, 5))
df = pd.DataFrame(
    {
        "状态": ["完成", "进行中", "未开始"],
        "百分比": [63, 22, 15],
    }
)
classes = np.repeat(np.arange(3), df.百分比)
k = np.arange(100)
ax.scatter(
    k % 10,
    k // 10,
    c=[COLORS[i] for i in classes],
    s=145,
    marker="s",
)
ax.set(aspect="equal", xlim=(-1, 10), ylim=(-1, 10))
ax.invert_yaxis()
ax.axis("off")
ax.legend(
    handles=[
        Patch(color=COLORS[i], label=f"{r.状态} {r.百分比}%")
        for i, r in enumerate(df.itertuples())
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.02),
    ncol=3,
    fontsize=10,
)
assert len(classes) == 100
finish(24, "华夫图把百分数还原成一百个格子", fig, df)
