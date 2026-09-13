"""案例 12：面积图强调规模，不用渐变伪装增长 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(12, "")
df = pd.DataFrame(
    {
        "月份": np.arange(1, 13),
        "存储量": np.round(
            30 + np.cumsum(rng.uniform(2, 8, 12)), 1
        ),
    }
)
ax.fill_between(df.月份, df.存储量, alpha=0.22, color=COLORS[0])
ax.plot(df.月份, df.存储量, "o-", color=COLORS[0])
ax.set(
    xlabel="月份",
    ylabel="月末已使用存储量（TB）",
    ylim=(0, 110),
    xticks=df.月份,
)
finish(12, "面积图强调规模，不用渐变伪装增长", fig, df)
