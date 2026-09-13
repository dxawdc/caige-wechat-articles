"""案例 25：漏斗图先确定同一批用户与观察窗口 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

import plotly.graph_objects as go

df = pd.DataFrame(
    {
        "阶段": ["访问", "注册", "激活", "付费"],
        "人数": [10000, 4200, 2600, 780],
    }
)
assert (df.人数.diff().dropna() <= 0).all()
fig = go.Figure(
    go.Funnel(
        y=df.阶段,
        x=df.人数,
        texttemplate="%{value:,.0f}<br>%{percentInitial:.1%}",
        marker=dict(
            color=["#188568", "#389B81", "#66B19C", "#A0D3C4"]
        ),
    )
)
fig.update_layout(
    xaxis_title="人数：同一批访问用户，7天转化窗口"
)
finish(
    25,
    "漏斗图先确定同一批用户与观察窗口",
    fig,
    df,
    {
        "总转化率": 0.078,
        "注册到激活": 2600 / 4200,
        "激活到付费": 0.3,
    },
)
