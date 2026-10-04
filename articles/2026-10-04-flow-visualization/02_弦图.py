import numpy as np
import pandas as pd
from pycirclize import Circos
from 图表工具 import ROOT, COLORS, 保存静态图

matrix = pd.read_csv(ROOT / '数据/部门协作_矩阵.csv', index_col=0)

# 对称矩阵中的一对协作只画一次
upper = pd.DataFrame(np.triu(matrix.to_numpy(), k=1),
                     index=matrix.index, columns=matrix.columns)
palette = dict(zip(matrix.index, COLORS))
circos = Circos.chord_diagram(
    upper, space=6, r_lim=(93, 100), cmap=palette,
    label_kws=dict(size=20, r=113),
    link_kws=dict(direction=0, alpha=.5, ec='white', lw=.5),
)
fig = circos.plotfig(figsize=(8.8, 8.4))
保存静态图(fig, '02_弦图', '弦图：哪些部门之间协作更多',
          '无向关系 · 六对部门合计 470 次 · 每对协作只计一次')
