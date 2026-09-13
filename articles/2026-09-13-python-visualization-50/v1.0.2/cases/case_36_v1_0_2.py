"""案例 36：气泡图同时看成本、质量和使用规模 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

import plotly.express as px

rng = np.random.default_rng(20260949)
df = pd.DataFrame(
    {
        "方案": [f"方案{i}" for i in range(1, 13)],
        "月成本": rng.uniform(1, 12, 12),
        "质量": rng.uniform(65, 96, 12),
        "用户数": rng.integers(100, 3000, 12),
        "类型": np.repeat(["轻量", "通用", "专业"], 4),
    }
)
fig = px.scatter(
    df,
    x="月成本",
    y="质量",
    size="用户数",
    color="类型",
    hover_name="方案",
    size_max=65,
    labels={
        "月成本": "月成本（万元）",
        "质量": "质量评分（分）",
    },
    color_discrete_sequence=COLORS,
)
fig.update_traces(marker_sizemode="area", marker_opacity=0.72)
finish(36, "气泡图同时看成本、质量和使用规模", fig, df)
