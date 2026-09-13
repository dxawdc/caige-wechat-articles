"""案例 48：四象限图定位长篇负向反馈 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(48, "")
df = pd.DataFrame(
    {
        "反馈编号": range(1, 181),
        "字数": rng.integers(20, 450, 180),
        "情绪指数": np.clip(rng.normal(0.1, 0.4, 180), -1, 1),
    }
)
threshold = 200
df["优先复核"] = (df.字数 >= threshold) & (df.情绪指数 < 0)
ax.axvspan(
    threshold,
    470,
    ymin=0,
    ymax=0.5,
    color=COLORS[4],
    alpha=0.08,
)
ax.scatter(
    df.字数,
    df.情绪指数,
    c=np.where(df.优先复核, COLORS[4], COLORS[1]),
    s=22,
    alpha=0.7,
)
ax.axvline(threshold, color="#AAB6B0", ls="--")
ax.axhline(0, color="#AAB6B0", ls="--")
ax.set(
    xlabel="反馈字数（字）",
    ylabel="模拟情绪指数（-1至1）",
    xlim=(0, 470),
    ylim=(-1, 1),
)
ax.text(
    300,
    -0.88,
    "长篇负向：优先人工复核",
    fontsize=10,
    color=COLORS[4],
)
finish(
    48,
    "四象限图定位长篇负向反馈",
    fig,
    df,
    {
        "人工设定长度阈值": threshold,
        "优先复核条数": int(df.优先复核.sum()),
        "指数来源": "直接模拟，未调用情感模型",
    },
)
