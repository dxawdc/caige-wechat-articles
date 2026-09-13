"""案例 13：阶梯图忠实表达规则生效的时间 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(13, "")
df = pd.DataFrame(
    {
        "日期": pd.to_datetime(
            [
                "2026-01-01",
                "2026-02-15",
                "2026-04-01",
                "2026-07-01",
                "2026-09-01",
            ]
        ),
        "免费额度": [100, 150, 150, 240, 240],
    }
)
ax.step(df.日期, df.免费额度, where="post", lw=2.5)
ax.scatter(df.日期, df.免费额度, s=60)
ax.set(
    ylabel="每日免费请求额度（次）",
    xlabel="日期",
    ylim=(0, 280),
)
fig.autofmt_xdate()
finish(13, "阶梯图忠实表达规则生效的时间", fig, df)
