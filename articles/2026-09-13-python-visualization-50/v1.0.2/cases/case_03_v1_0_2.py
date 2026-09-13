"""案例 03：收入总量由谁贡献 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(3, "")
df = pd.DataFrame(
    {
        "季度": ["Q1", "Q2", "Q3", "Q4"],
        "订阅": [60, 72, 81, 96],
        "课程": [32, 28, 40, 45],
        "咨询": [18, 24, 22, 30],
    }
)
bottom = np.zeros(len(df))
for col in ["订阅", "课程", "咨询"]:
    bars = ax.bar(df.季度, df[col], bottom=bottom, label=col)
    ax.bar_label(bars, label_type="center", color="white")
    bottom += df[col].to_numpy()
assert np.array_equal(bottom, df.iloc[:, 1:].sum(axis=1))
for x, total in enumerate(bottom):
    ax.text(x, total + 3, f"{total:g}", ha="center")
ax.set(ylabel="收入（万元）", ylim=(0, 210))
ax.legend(ncol=3)
finish(
    3,
    "收入总量由谁贡献",
    fig,
    df,
    {"季度合计": bottom.tolist()},
)
