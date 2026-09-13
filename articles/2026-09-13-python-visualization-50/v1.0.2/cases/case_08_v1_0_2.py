"""案例 08：圆面积编码，数值翻倍不能把半径翻倍 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

from matplotlib.patches import Circle

rng, fig, ax = start(8, "", size=(8, 4))
df = pd.DataFrame(
    {
        "项目": ["甲", "乙", "丙", "丁"],
        "调用量": [100, 200, 400, 800],
    }
)
df["半径"] = np.sqrt(df.调用量 / 800) * 0.85
for i, row in enumerate(df.itertuples()):
    ax.add_patch(
        Circle((i * 2, 0), row.半径, color=COLORS[i], alpha=0.8)
    )
    ax.text(
        i * 2, -1.08, f"{row.项目}：{row.调用量}", ha="center"
    )
assert np.allclose(
    np.pi * df.半径**2 / df.调用量, np.pi * 0.85**2 / 800
)
ax.set(xlim=(-1.2, 7.2), ylim=(-1.5, 1.2), aspect="equal")
ax.axis("off")
finish(
    8,
    "圆面积编码，数值翻倍不能把半径翻倍",
    fig,
    df,
    {"面积比例": "1:2:4:8", "半径比例": "1:√2:2:√8"},
)
