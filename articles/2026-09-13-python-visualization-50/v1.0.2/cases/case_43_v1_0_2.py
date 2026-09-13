"""案例 43：关系网络寻找跨团队的连接点 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

import networkx as nx

rng, fig, ax = start(43, "", size=(8, 6))
edges = [
    ("A1", "A2"),
    ("A2", "A3"),
    ("A3", "A1"),
    ("B1", "B2"),
    ("B2", "B3"),
    ("B3", "B1"),
    ("A2", "协调"),
    ("协调", "B2"),
    ("协调", "C1"),
    ("C1", "C2"),
]
df = pd.DataFrame(edges, columns=["成员1", "成员2"])
G = nx.Graph(edges)
centrality = nx.betweenness_centrality(G)
pos = nx.spring_layout(G, seed=43)
nx.draw_networkx(
    G,
    pos,
    ax=ax,
    node_size=[600 + 3500 * centrality[n] for n in G],
    node_color=[
        COLORS[0] if n == "协调" else "#A9CBE2" for n in G
    ],
    font_family=FONT_NAME,
    font_size=11,
    edge_color="#BAC8C0",
)
ax.axis("off")
finish(
    43,
    "关系网络寻找跨团队的连接点",
    fig,
    {
        "edges": df,
        "nodes": pd.DataFrame(
            {
                "成员": list(G),
                "中介中心性": list(centrality.values()),
            }
        ),
    },
)
