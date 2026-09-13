"""案例 28：箱线图保留异常点，不替数据做决定 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(28, "")
df = pd.DataFrame(
    {
        "版本": np.repeat(["A", "B", "C"], 101),
        "响应": np.r_[
            rng.lognormal(5.2, 0.25, 100),
            800,
            rng.lognormal(5.0, 0.22, 100),
            720,
            rng.lognormal(4.9, 0.2, 100),
            690,
        ],
    }
)
sns.boxplot(
    data=df,
    x="版本",
    y="响应",
    ax=ax,
    color=COLORS[0],
    width=0.5,
    whis=1.5,
    showfliers=True,
)
flags = []
for name, g in df.groupby("版本"):
    q1, q3 = g.响应.quantile([0.25, 0.75])
    iqr = q3 - q1
    flags.extend(
        (
            (g.响应 < q1 - 1.5 * iqr)
            | (g.响应 > q3 + 1.5 * iqr)
        ).tolist()
    )
df["IQR候选异常"] = flags
ax.set(xlabel="版本", ylabel="请求响应时间（毫秒）")
finish(
    28,
    "箱线图保留异常点，不替数据做决定",
    fig,
    df,
    {
        "原始行数": len(df),
        "删除行数": 0,
        "候选异常数": sum(flags),
    },
)
