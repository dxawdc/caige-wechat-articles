import pandas as pd
import plotly.graph_objects as go
from 图表工具 import ROOT, COLORS, 保存交互图

# 每行是一条完整路径，value 是这条路径的人数
paths = pd.read_csv(ROOT / '数据/冲积图_完整路径.csv')
columns = [('cohort', '进入批次'), ('month1', '第1月'), ('month2', '第2月')]
orders = [['新用户', '回流用户'], ['轻度', '重度'], ['轻度', '重度', '流失']]
dimensions = [
    dict(label=label, values=paths[column],
         categoryorder='array', categoryarray=order)
    for (column, label), order in zip(columns, orders)
]
color = paths['cohort'].map({'新用户': 0, '回流用户': 1})
fig = go.Figure(go.Parcats(
    dimensions=dimensions, counts=paths['value'],
    line=dict(color=color, colorscale=[[0, COLORS[0]], [1, COLORS[1]]],
              cmin=0, cmax=1, shape='hspline'),
    labelfont=dict(size=23), tickfont=dict(size=22),
    arrangement='fixed', bundlecolors=True, hoveron='color',
))
保存交互图(fig, '03_冲积图', '冲积图：同一批用户如何改变状态',
          '500 位用户 · 蓝色为新用户，橙色为回流用户 · 流带宽度表示人数')
