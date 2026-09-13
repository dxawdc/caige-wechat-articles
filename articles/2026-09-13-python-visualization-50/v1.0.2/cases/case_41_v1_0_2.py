"""案例 41：矩形树图展示空间占用的长尾 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

import squarify

rng, fig, ax = start(41, "")
df = pd.DataFrame(
    {
        "目录": [
            "日志",
            "图片",
            "视频",
            "模型",
            "备份",
            "缓存",
            "文档",
            "其他",
        ],
        "容量": [360, 240, 180, 120, 80, 50, 40, 30],
    }
).sort_values("容量", ascending=False)
squarify.plot(
    sizes=df.容量,
    label=[f"{r.目录}\n{r.容量} GB" for r in df.itertuples()],
    color=[COLORS[i % 6] for i in range(len(df))],
    ax=ax,
    pad=True,
    text_kwargs={"color": "white", "fontsize": 12},
)
ax.axis("off")
finish(
    41,
    "矩形树图展示空间占用的长尾",
    fig,
    df,
    {
        "总容量GB": int(df.容量.sum()),
        "最大占比": float(df.容量.max() / df.容量.sum()),
    },
)
