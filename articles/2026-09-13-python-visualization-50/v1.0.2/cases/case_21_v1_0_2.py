"""案例 21：环形图只放少量互斥类别 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(21, "")
df = pd.DataFrame(
    {
        "来源": ["订阅", "课程", "咨询", "其他"],
        "收入": [52, 27, 16, 5],
    }
)
ax.pie(
    df.收入,
    labels=df.来源,
    autopct="%1.0f%%",
    startangle=90,
    wedgeprops={"width": 0.38, "edgecolor": "white"},
    pctdistance=0.81,
)
ax.text(
    0,
    0,
    "总收入\n100 万元",
    ha="center",
    va="center",
    fontsize=16,
)
ax.axis("equal")
finish(21, "环形图只放少量互斥类别", fig, df)
