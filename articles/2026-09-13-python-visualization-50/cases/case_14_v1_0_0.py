"""案例 14：环形时间轴，比较一天中的访问节奏 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(14, "", subplot_kw={"projection": "polar"})
h = np.arange(24)
v = (
    20
    + 100 * np.exp(-(((h - 10) / 3) ** 2))
    + 130 * np.exp(-(((h - 20) / 2.5) ** 2))
)
df = pd.DataFrame(
    {"小时": h, "访问量": np.round(v + rng.uniform(0, 8, 24))}
)
theta = h / 24 * 2 * np.pi
ax.plot(
    np.r_[theta, 2 * np.pi],
    np.r_[df.访问量, df.访问量.iloc[0]],
    lw=2,
)
ax.set(
    theta_offset=np.pi / 2,
    theta_direction=-1,
    xticks=np.arange(0, 24, 3) / 24 * 2 * np.pi,
    xticklabels=[f"{x:02d}:00" for x in range(0, 24, 3)],
    ylim=(0, 180),
)
ax.set_ylabel("访问量（次）", labelpad=30)
finish(14, "环形时间轴，比较一天中的访问节奏", fig, df)
