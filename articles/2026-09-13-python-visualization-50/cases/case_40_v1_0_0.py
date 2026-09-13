"""案例 40：旭日图从业务线逐层看到产品 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

import plotly.express as px

df = pd.DataFrame(
    {
        "业务": [
            "学习",
            "学习",
            "学习",
            "工具",
            "工具",
            "工具",
        ],
        "产品": [
            "Python",
            "SQL",
            "可视化",
            "清洗",
            "报表",
            "协作",
        ],
        "收入": [38, 27, 35, 42, 33, 25],
    }
)
fig = px.sunburst(
    df,
    path=["业务", "产品"],
    values="收入",
    color="业务",
    color_discrete_sequence=COLORS,
)
fig.update_traces(
    textinfo="label+value", insidetextorientation="horizontal"
)
finish(
    40,
    "旭日图从业务线逐层看到产品",
    fig,
    df,
    {"叶子合计": int(df.收入.sum())},
)
