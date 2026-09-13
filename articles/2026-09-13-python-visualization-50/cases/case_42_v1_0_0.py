"""案例 42：树图表达唯一上级的组织关系 | v1.0.0 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_0 import *

import networkx as nx

rng, fig, ax = start(42, "", size=(9, 5))
edges = [
    ("负责人", "产品组"),
    ("负责人", "技术组"),
    ("负责人", "运营组"),
    ("产品组", "研究"),
    ("产品组", "设计"),
    ("技术组", "前端"),
    ("技术组", "后端"),
    ("运营组", "内容"),
    ("运营组", "社群"),
]
df = pd.DataFrame(edges, columns=["上级", "下级"])
G = nx.DiGraph(edges)
pos = {
    "负责人": (0, 0),
    "产品组": (-3, -1),
    "技术组": (0, -1),
    "运营组": (3, -1),
    "研究": (-4, -2),
    "设计": (-2.4, -2),
    "前端": (-0.8, -2),
    "后端": (0.8, -2),
    "内容": (2.4, -2),
    "社群": (4, -2),
}
assert nx.is_arborescence(G)
nx.draw_networkx(
    G,
    pos,
    ax=ax,
    node_color="#D6ECE3",
    node_size=2100,
    font_family=FONT_NAME,
    font_size=11,
    arrows=True,
    arrowstyle="-|>",
    arrowsize=16,
    edge_color="#729B89",
)
ax.margins(0.18)
ax.axis("off")
finish(42, "树图表达唯一上级的组织关系", fig, df)
