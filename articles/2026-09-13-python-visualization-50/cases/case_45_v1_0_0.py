"""案例 45：桑基图，流入流出必须对得上 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

import plotly.graph_objects as go

labels = ["搜索", "社群", "注册", "未注册", "付费", "未付费"]
df = pd.DataFrame(
    {
        "source": [0, 0, 1, 1, 2, 2],
        "target": [2, 3, 2, 3, 4, 5],
        "value": [360, 240, 280, 120, 192, 448],
    }
)
assert (
    df.loc[df.target == 2, "value"].sum()
    == df.loc[df.source == 2, "value"].sum()
)
assert df.loc[df.source.isin([0, 1]), "value"].sum() == 1000
fig = go.Figure(
    go.Sankey(
        node=dict(
            label=labels, pad=25, thickness=22, color=COLORS
        ),
        link=dict(
            source=df.source,
            target=df.target,
            value=df.value,
            color="rgba(24,133,104,0.25)",
        ),
    )
)
finish(
    45,
    "桑基图，流入流出必须对得上",
    fig,
    {
        "edges": df,
        "nodes": pd.DataFrame(
            {"id": range(6), "label": labels}
        ),
    },
    {
        "源头人数": 1000,
        "注册人数": 640,
        "最终付费": 192,
        "守恒": True,
    },
)
