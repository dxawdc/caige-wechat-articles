"""案例 16：河流图观察主题热度如何消长 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(16, "")
t = np.arange(24)
df = pd.DataFrame(
    {
        "周": t + 1,
        "入门": 60 * np.exp(-(((t - 4) / 5) ** 2)) + 10,
        "实战": 75 * np.exp(-(((t - 12) / 6) ** 2)) + 10,
        "部署": 80 * np.exp(-(((t - 20) / 5) ** 2)) + 10,
    }
)
ax.stackplot(
    df.周,
    df.入门,
    df.实战,
    df.部署,
    baseline="wiggle",
    labels=["入门", "实战", "部署"],
    alpha=0.85,
)
ax.set(
    xlabel="周次",
    ylabel="带宽代表讨论量；纵向位置无数值含义",
    yticks=[],
)
ax.legend(ncol=3, loc="upper left")
finish(16, "河流图观察主题热度如何消长", fig, df)
