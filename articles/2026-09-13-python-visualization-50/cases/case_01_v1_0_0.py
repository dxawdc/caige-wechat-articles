"""案例 01：先找出贡献最大的渠道 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(1, "")
df = pd.DataFrame(
    {
        "渠道": [
            "搜索",
            "社群",
            "视频",
            "推荐",
            "直播",
            "自然访问",
        ],
        "订单数": rng.integers(450, 1800, 6),
    }
).sort_values("订单数")
bars = ax.barh(
    df.渠道, df.订单数, color=[COLORS[1]] * 5 + [COLORS[0]]
)
ax.bar_label(bars, padding=4)
ax.set(
    xlabel="已支付订单数（笔）",
    xlim=(0, df.订单数.max() * 1.17),
)
finish(
    1,
    "先找出贡献最大的渠道",
    fig,
    df,
    {
        "最大渠道": df.iloc[-1].渠道,
        "订单总数": int(df.订单数.sum()),
    },
)
