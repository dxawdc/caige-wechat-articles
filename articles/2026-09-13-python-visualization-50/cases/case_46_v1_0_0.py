"""案例 46：词云适合发现主题，不适合精确排名 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

from collections import Counter
from wordcloud import WordCloud

rng, fig, ax = start(46, "")
words = [
    "代码",
    "案例",
    "图表",
    "清晰",
    "数据",
    "实践",
    "讲解",
    "复现",
    "学习",
    "工具",
    "好用",
    "步骤",
]
weights = np.array(
    [14, 13, 12, 11, 10, 9, 8, 7, 6, 4, 3, 3], dtype=float
)
tokens = rng.choice(words, 700, p=weights / weights.sum())
counts = Counter(tokens)
df = pd.DataFrame(
    counts.items(), columns=["词", "频次"]
).sort_values("频次", ascending=False)
wc = WordCloud(
    font_path=FONT,
    width=1200,
    height=650,
    background_color="white",
    colormap="viridis",
    random_state=46,
    collocations=False,
).generate_from_frequencies(counts)
ax.imshow(wc)
ax.axis("off")
finish(
    46,
    "词云适合发现主题，不适合精确排名",
    fig,
    {
        "tokens": pd.DataFrame({"分词结果": tokens}),
        "frequency": df,
    },
    {"总词数": len(tokens)},
)
