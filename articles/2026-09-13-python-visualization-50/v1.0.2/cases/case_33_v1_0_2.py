"""案例 33：二维密度等高线，寻找两群样本 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(33, "")
a = rng.multivariate_normal(
    [2, 3], [[0.6, 0.3], [0.3, 0.6]], 450
)
b = rng.multivariate_normal(
    [5, 6], [[0.6, -0.2], [-0.2, 0.6]], 350
)
df = pd.DataFrame(np.vstack([a, b]), columns=["投入", "产出"])
sns.kdeplot(
    data=df,
    x="投入",
    y="产出",
    fill=True,
    levels=7,
    thresh=0.05,
    cmap="YlGnBu",
    ax=ax,
)
ax.scatter(df.投入, df.产出, s=3, c="#243E35", alpha=0.13)
ax.set(xlabel="标准化投入指数", ylabel="标准化产出指数")
finish(33, "二维密度等高线，寻找两群样本", fig, df)
