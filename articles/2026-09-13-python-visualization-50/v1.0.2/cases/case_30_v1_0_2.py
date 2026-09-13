"""案例 30：蜂群图让小样本逐个露面 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(30, "")
df = pd.DataFrame(
    {
        "组别": np.repeat(["新手", "熟练", "资深"], 35),
        "耗时": np.r_[
            rng.normal(32, 5, 35),
            rng.normal(23, 4, 35),
            rng.normal(17, 3, 35),
        ],
    }
)
sns.swarmplot(
    data=df,
    x="组别",
    y="耗时",
    size=4.5,
    ax=ax,
    color=COLORS[0],
)
ax.set(
    ylabel="完成任务耗时（分钟）",
    xlabel="每点代表1位模拟参与者；每组35人",
)
finish(30, "蜂群图让小样本逐个露面", fig, df)
