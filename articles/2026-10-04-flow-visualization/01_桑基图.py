import pandas as pd
import plotly.graph_objects as go
from 图表工具 import ROOT, COLORS, 保存交互图

# 每一行是一条“起点—终点—数量”连接
edges = pd.read_csv(ROOT / '数据/桑基图_边表.csv')
names = ['广告', '自然搜索', '好友分享', '注册',
         '付费', '注册未付费', '未注册']
ids = {name: i for i, name in enumerate(names)}

# Plotly 的 source 和 target 使用节点索引
source = edges['source'].map(ids).tolist()
target = edges['target'].map(ids).tolist()
value = edges['value'].tolist()
incoming = edges.groupby('target')['value'].sum()
outgoing = edges.groupby('source')['value'].sum()
labels = [f'{name} {max(incoming.get(name, 0), outgoing.get(name, 0))}'
          for name in names]

fig = go.Figure(go.Sankey(
    arrangement='snap', valuesuffix='人',
    node=dict(label=labels, pad=35, thickness=22,
              color=[*COLORS[:3], COLORS[3], '#CB6A7D', '#7FA4CC', '#A0ADB8']),
    link=dict(source=source, target=target, value=value,
              color=['rgba(50,117,187,.40)'] * 2
                    + ['rgba(238,157,58,.40)'] * 2
                    + ['rgba(40,165,156,.40)'] * 2
                    + ['rgba(144,107,195,.40)'] * 2),
))
保存交互图(fig, '01_桑基图', '桑基图：访客从哪里来，又去了哪里',
          '1000 位访客 · 600 位注册 · 180 位付费 · 固定 7 日观察窗')
