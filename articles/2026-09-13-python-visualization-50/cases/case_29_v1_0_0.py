"""案例 29：小提琴图识别中位数背后的双峰 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(29, "")
df = pd.DataFrame(
    {
        "班级": np.repeat(["甲班", "乙班"], 240),
        "得分": np.r_[
            rng.normal(70, 8, 240),
            rng.normal(56, 4, 120),
            rng.normal(84, 4, 120),
        ],
    }
)
sns.violinplot(
    data=df,
    x="班级",
    y="得分",
    cut=0,
    inner="quart",
    density_norm="width",
    ax=ax,
    color=COLORS[1],
)
ax.set(ylabel="练习得分（分）")
finish(29, "小提琴图识别中位数背后的双峰", fig, df)
