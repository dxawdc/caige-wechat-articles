"""案例 31：镜像条形图比较两类用户年龄结构 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

from matplotlib.ticker import FuncFormatter

rng, fig, ax = start(31, "")
df = pd.DataFrame(
    {
        "年龄": ["18–24", "25–34", "35–44", "45–54", "55+"],
        "新客": [280, 520, 410, 260, 130],
        "老客": [150, 390, 460, 310, 190],
    }
)
ax.barh(df.年龄, -df.新客, label="新客")
ax.barh(df.年龄, df.老客, label="老客")
ax.axvline(0, color="#708078", lw=1)
ax.set_xlim(-600, 600)
ax.xaxis.set_major_formatter(
    FuncFormatter(lambda x, pos: f"{abs(x):.0f}")
)
ax.set(
    xlabel="人数（左侧为镜像显示，并非负人数）",
    ylabel="年龄（岁）",
)
ax.legend()
finish(31, "镜像条形图比较两类用户年龄结构", fig, df)
