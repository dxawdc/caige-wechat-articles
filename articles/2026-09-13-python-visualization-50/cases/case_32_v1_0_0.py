"""案例 32：六边形分箱，把遮挡变成密度 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(32, "")
x = rng.gamma(3, 12, 7000)
y = 25 + 2.1 * x + rng.gamma(3, 9, 7000)
assert (y > 0).all()
df = pd.DataFrame({"请求数": x, "耗时": y})
h = ax.hexbin(
    df.请求数, df.耗时, gridsize=32, mincnt=1, cmap="YlGnBu"
)
fig.colorbar(h, ax=ax, label="每格观测数（条）")
assert h.get_array().sum() == len(df)
ax.set(
    xlabel="每分钟请求数（连续模拟强度）",
    ylabel="处理耗时（毫秒）",
)
finish(
    32,
    "六边形分箱，把遮挡变成密度",
    fig,
    df,
    {"分箱计数": h.get_array().sum()},
)
