"""案例 38：相关热力图保留正负方向 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(38, "", size=(7, 5.5))
x = rng.normal(size=240)
df = pd.DataFrame(
    {
        "流量": x,
        "收入": 0.8 * x + rng.normal(0, 0.5, 240),
        "等待": -0.7 * x + rng.normal(0, 0.6, 240),
        "评分": rng.normal(size=240),
    }
)
corr = df.corr(method="pearson")
sns.heatmap(
    corr,
    ax=ax,
    annot=True,
    fmt=".2f",
    vmin=-1,
    vmax=1,
    center=0,
    cmap="vlag",
    square=True,
    cbar_kws={"label": "Pearson r"},
)
assert np.allclose(corr, corr.T) and np.allclose(
    np.diag(corr), 1
)
finish(
    38,
    "相关热力图保留正负方向",
    fig,
    {"raw": df, "correlation": corr.reset_index()},
)
