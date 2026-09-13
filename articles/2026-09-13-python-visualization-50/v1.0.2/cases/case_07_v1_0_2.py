"""案例 07：平行坐标，寻找多指标的折中方案 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

import plotly.graph_objects as go

rng = np.random.default_rng(20260920)
df = pd.DataFrame(
    {
        "方案": np.arange(1, 13),
        "质量": rng.uniform(70, 96, 12),
        "成本": rng.uniform(10, 30, 12),
        "延迟": rng.uniform(100, 800, 12),
    }
)
scaled = pd.DataFrame(
    {
        "质量↑": (df.质量 - 70) / 26,
        "成本优势↑": (30 - df.成本) / 20,
        "速度优势↑": (800 - df.延迟) / 700,
    }
)
fig = go.Figure(
    go.Parcoords(
        line=dict(
            color=df.方案,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="方案编号"),
        ),
        labelfont=dict(size=20),
        dimensions=[
            dict(
                label=c,
                values=scaled[c],
                range=[0, 1],
                tickvals=[0, 0.25, 0.5, 0.75, 1],
                ticktext=["0", "0.25", "0.50", "0.75", "1"],
            )
            for c in scaled
        ],
    )
)
finish(
    7,
    "平行坐标，寻找多指标的折中方案",
    fig,
    {"raw": df, "scaled": scaled},
)
