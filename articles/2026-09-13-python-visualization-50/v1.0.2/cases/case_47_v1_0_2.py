"""案例 47：比较文本偏好，先消除篇幅差异 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

rng, fig, ax = start(47, "")
df = pd.DataFrame(
    {
        "语料": ["入门反馈", "进阶反馈", "实战反馈"],
        "总词数": [2000, 8000, 5000],
        "代码": [120, 560, 500],
        "原理": [40, 640, 250],
        "步骤": [180, 240, 200],
        "报错": [100, 160, 400],
    }
)
words = ["代码", "原理", "步骤", "报错"]
norm = df[words].div(df.总词数, axis=0) * 1000
for i, row in norm.iterrows():
    ax.plot(words, row, "o-", label=df.语料.iloc[i], lw=2)
ax.set(
    ylabel="每千词出现次数",
    xlabel="关键词（位置只用于排布，无连续距离含义）",
    ylim=(0, 110),
)
ax.legend()
finish(
    47,
    "比较文本偏好，先消除篇幅差异",
    fig,
    {"counts": df, "per_1000": norm.assign(语料=df.语料)},
)
