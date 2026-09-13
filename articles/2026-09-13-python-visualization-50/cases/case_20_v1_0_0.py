"""案例 20：蜡烛图展示同一周期的四个价格 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

import plotly.graph_objects as go

rng = np.random.default_rng(20260933)
n = 25
opens = 100 + np.cumsum(rng.normal(0, 1, n))
closes = opens + rng.normal(0, 1.4, n)
df = pd.DataFrame(
    {
        "日期": pd.bdate_range("2026-08-03", periods=n),
        "开盘": opens,
        "收盘": closes,
        "最高": np.maximum(opens, closes)
        + rng.uniform(0.2, 2, n),
        "最低": np.minimum(opens, closes)
        - rng.uniform(0.2, 2, n),
    }
)
assert (df.最高 >= df[["开盘", "收盘"]].max(axis=1)).all()
assert (df.最低 <= df[["开盘", "收盘"]].min(axis=1)).all()
fig = go.Figure(
    go.Candlestick(
        x=df.日期,
        open=df.开盘,
        high=df.最高,
        low=df.最低,
        close=df.收盘,
        increasing_line_color="#188568",
        decreasing_line_color="#CB6677",
    )
)
fig.update_layout(
    xaxis_rangeslider_visible=False,
    yaxis_title="虚构资产价格（元）",
)
finish(20, "蜡烛图展示同一周期的四个价格", fig, df)
