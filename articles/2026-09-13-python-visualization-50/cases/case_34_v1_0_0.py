"""案例 34：三维曲面只用于真实的第三个数值维度 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

import plotly.graph_objects as go

x = np.linspace(-3, 3, 55)
y = np.linspace(-3, 3, 55)
X, Y = np.meshgrid(x, y)
Z = 80 * np.exp(
    -((X - 1) ** 2 + (Y - 0.5) ** 2) / 2
) + 40 * np.exp(-((X + 1.4) ** 2 + (Y + 1) ** 2))
df = pd.DataFrame(
    {"X": X.ravel(), "Y": Y.ravel(), "温升": Z.ravel()}
)
fig = go.Figure(
    go.Surface(
        x=X,
        y=Y,
        z=Z,
        colorscale="Viridis",
        colorbar=dict(title="温升"),
    )
)
fig.update_layout(
    scene=dict(
        xaxis_title="X（米）",
        yaxis_title="Y（米）",
        zaxis_title="温升（℃）",
        camera=dict(eye=dict(x=1.6, y=-1.7, z=1.2)),
    )
)
finish(34, "三维曲面只用于真实的第三个数值维度", fig, df)
