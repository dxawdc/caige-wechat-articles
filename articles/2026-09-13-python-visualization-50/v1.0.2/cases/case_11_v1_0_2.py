"""案例 11：趋势线先处理日期，再连接观测 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(11, "")
df = pd.DataFrame(
    {"日期": pd.date_range("2026-01-01", periods=60)}
)
df["订单"] = np.round(
    160
    + np.arange(60) * 1.2
    + 20 * np.sin(np.arange(60) * 2 * np.pi / 7)
    + rng.normal(0, 8, 60)
)
df["7日均值"] = df.订单.rolling(7, min_periods=7).mean()
ax.plot(
    df.日期, df.订单, color="#B6C5BC", lw=1, label="每日订单"
)
ax.plot(df.日期, df["7日均值"], lw=2.5, label="后向7日均值")
ax.set(ylabel="订单数（笔）", xlabel="日期")
ax.legend()
fig.autofmt_xdate()
finish(
    11,
    "趋势线先处理日期，再连接观测",
    fig,
    df,
    {"窗口": "包含当日及前6日；前6日均值留空"},
)
