"""案例 09：日历热力图，周末和工作日有何区别 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(9, "", size=(8, 4.5))
dates = pd.date_range("2026-08-01", "2026-08-31")
df = pd.DataFrame(
    {
        "日期": dates,
        "访问量": rng.poisson(350, 31)
        + (dates.dayofweek >= 5) * 120,
    }
)
grid = np.full((6, 7), np.nan)
labels = np.full((6, 7), "", dtype=object)
for row in df.itertuples():
    pos = row.日期.day - 1 + dates[0].dayofweek
    r, c = divmod(pos, 7)
    grid[r, c] = row.访问量
    labels[r, c] = f"{row.日期.day}日\n{row.访问量}"
sns.heatmap(
    grid,
    annot=labels,
    fmt="",
    cmap="YlGnBu",
    mask=np.isnan(grid),
    ax=ax,
    linewidths=3,
    cbar_kws={"label": "访问量（次）"},
    xticklabels=list("一二三四五六日"),
    yticklabels=False,
)
ax.set(xlabel="星期", ylabel="2026年8月")
finish(9, "日历热力图，周末和工作日有何区别", fig, df)
