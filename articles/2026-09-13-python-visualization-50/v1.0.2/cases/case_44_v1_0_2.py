"""案例 44：邻接矩阵还原谁向谁发起协作 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(44, "")
names = ["产品", "研发", "测试", "运营", "客服"]
matrix = rng.integers(0, 26, (5, 5))
np.fill_diagonal(matrix, 0)
df = pd.DataFrame(matrix, columns=names, index=names)
sns.heatmap(
    df,
    annot=True,
    fmt="d",
    cmap="YlGnBu",
    ax=ax,
    cbar_kws={"label": "协作请求数（次）"},
    square=True,
)
ax.set(xlabel="接收团队（列）", ylabel="发起团队（行）")
finish(
    44,
    "邻接矩阵还原谁向谁发起协作",
    fig,
    df.rename_axis("发起团队").reset_index(),
    {"总请求": int(matrix.sum()), "有向": True},
)
