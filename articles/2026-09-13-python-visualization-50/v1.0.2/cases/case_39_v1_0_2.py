"""案例 39：辛普森悖论，合并后关系为什么反转 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, axes = start(39, "", size=(10, 4.8), ncols=2)
x1 = rng.uniform(1, 4, 100)
x2 = rng.uniform(6, 9, 100)
df = pd.DataFrame(
    {
        "投入": np.r_[x1, x2],
        "得分": np.r_[
            75 + 2 * x1 + rng.normal(0, 1, 100),
            42 + 2 * x2 + rng.normal(0, 1, 100),
        ],
        "任务": np.repeat(["简单", "困难"], 100),
    }
)
rs = {}
for ax, split in zip(axes, [False, True]):
    groups = df.groupby("任务") if split else [("合并", df)]
    for name, g in groups:
        ax.scatter(g.投入, g.得分, s=15, alpha=0.6, label=name)
        m, b = np.polyfit(g.投入, g.得分, 1)
        xx = np.array([g.投入.min(), g.投入.max()])
        ax.plot(xx, m * xx + b)
        rs[name] = g.投入.corr(g.得分)
    ax.set(
        xlabel="投入时间（小时）",
        ylabel="得分（分）",
        title="按难度拆分" if split else "直接合并",
        ylim=(45, 88),
    )
    ax.legend()
assert rs["合并"] < 0 and rs["简单"] > 0 and rs["困难"] > 0
finish(39, "辛普森悖论，合并后关系为什么反转", fig, df, rs)
