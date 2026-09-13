"""案例 22：百分比堆叠，规模不同也能比较结构 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(22, "")
df = pd.DataFrame(
    {
        "月份": ["四月", "五月", "六月"],
        "新客": [240, 360, 480],
        "老客": [360, 440, 720],
    }
)
shares = (
    df[["新客", "老客"]].div(
        df[["新客", "老客"]].sum(axis=1), axis=0
    )
    * 100
)
left = np.zeros(len(df))
for c in shares:
    bars = ax.barh(df.月份, shares[c], left=left, label=c)
    ax.bar_label(
        bars,
        labels=[f"{v:.1f}%" for v in shares[c]],
        label_type="center",
        color="white",
    )
    left += shares[c]
assert np.allclose(left, 100)
ax.set(
    xlim=(0, 100),
    xlabel="订单结构（%）；各月分母分别为600、800、1200笔",
)
ax.legend(
    ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.14)
)
finish(22, "百分比堆叠，规模不同也能比较结构", fig, df)
