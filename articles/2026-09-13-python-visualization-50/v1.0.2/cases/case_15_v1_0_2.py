"""案例 15：堆叠面积，看渠道总量与结构一起变化 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(15, "")
t = np.arange(1, 13)
df = pd.DataFrame(
    {
        "月份": t,
        "搜索": 90 + 5 * t,
        "社群": 30 + 7 * t,
        "视频": 10 + 2 * t**1.5,
    }
)
ax.stackplot(
    t,
    *[df[c] for c in ["搜索", "社群", "视频"]],
    labels=["搜索", "社群", "视频"],
    alpha=0.85
)
ax.set(
    xlabel="月份",
    ylabel="获客量（人）",
    xlim=(1, 12),
    ylim=(0, 430),
)
ax.legend(loc="upper left")
finish(15, "堆叠面积，看渠道总量与结构一起变化", fig, df)
