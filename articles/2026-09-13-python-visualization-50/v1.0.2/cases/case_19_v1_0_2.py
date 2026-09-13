"""案例 19：瀑布图解释余额如何一步步变化 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(19, "")
df = pd.DataFrame(
    {
        "项目": [
            "期初",
            "回款",
            "采购",
            "工资",
            "租金",
            "期末",
        ],
        "变动": [100, 85, -32, -28, -12, 0],
    }
)
balance = 100
endpoints = [balance]
ax.bar(0, balance, color=COLORS[1])
for i in range(1, 5):
    delta = df.变动.iloc[i]
    new = balance + delta
    ax.bar(
        i,
        abs(delta),
        bottom=min(balance, new),
        color=COLORS[0] if delta > 0 else COLORS[4],
    )
    ax.plot(
        [i - 1 + 0.4, i - 0.4],
        [balance, balance],
        color="#AAB8B0",
        ls="--",
    )
    balance = new
    endpoints.append(balance)
ax.bar(5, balance, color=COLORS[1])
endpoints.append(balance)
for i, v in enumerate(df.变动):
    ax.text(
        i,
        max(endpoints[i], endpoints[max(0, i - 1)]) + 6,
        str(balance if i == 5 else v),
        ha="center",
    )
assert balance == df.变动.iloc[:5].sum()
ax.set(
    xticks=range(6),
    xticklabels=df.项目,
    ylabel="现金余额/变动（万元）",
    ylim=(0, 220),
)
finish(
    19,
    "瀑布图解释余额如何一步步变化",
    fig,
    df,
    {"期末余额": balance},
)
