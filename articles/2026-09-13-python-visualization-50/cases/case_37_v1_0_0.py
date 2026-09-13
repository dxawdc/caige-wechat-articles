"""案例 37：散点矩阵快速筛查多变量关系 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng = np.random.default_rng(20260950)
n = 160
x = rng.normal(50, 10, n)
df = pd.DataFrame(
    {
        "投入": x,
        "产出": 1.4 * x + rng.normal(0, 8, n),
        "等待": 90 - 0.7 * x + rng.normal(0, 7, n),
        "经验": rng.uniform(1, 10, n),
    }
)
g = sns.pairplot(
    df,
    corner=True,
    diag_kind="hist",
    height=2.1,
    plot_kws={"s": 12, "alpha": 0.5, "color": COLORS[0]},
    diag_kws={"bins": 15, "color": COLORS[1]},
)
finish(37, "散点矩阵快速筛查多变量关系", g.fig, df)
