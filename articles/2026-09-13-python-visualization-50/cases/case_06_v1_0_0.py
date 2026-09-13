"""案例 06：选工具时，把能力放在同一把尺子上 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

rng, fig, ax = start(6, "", subplot_kw={"projection": "polar"})
df = pd.DataFrame(
    {
        "维度": ["易用", "定制", "交互", "导出", "协作"],
        "方案A": [80, 90, 55, 92, 65],
        "方案B": [88, 65, 92, 78, 86],
    }
)
theta = np.linspace(0, 2 * np.pi, len(df), endpoint=False)
for name in ["方案A", "方案B"]:
    angles = np.r_[theta, theta[0]]
    values = np.r_[df[name], df[name].iloc[0]]
    ax.plot(angles, values, "o-", label=name)
    ax.fill(angles, values, alpha=0.08)
ax.set(
    theta_offset=np.pi / 2,
    theta_direction=-1,
    xticks=theta,
    xticklabels=df.维度,
    ylim=(0, 100),
)
ax.set_yticks([25, 50, 75, 100])
ax.legend(loc="upper right", bbox_to_anchor=(1.4, 1.1))
finish(6, "选工具时，把能力放在同一把尺子上", fig, df)
