import pandas as pd
import matplotlib.pyplot as plt
from 图表工具 import ROOT, 保存静态图

matrix = pd.read_csv(ROOT / '数据/部门协作_矩阵.csv', index_col=0)
fig, ax = plt.subplots(figsize=(8.8, 7.5))
ax.imshow(matrix, cmap='Blues', vmin=0, vmax=120)
ax.set_xticks(range(len(matrix.columns)), matrix.columns, fontsize=19)
ax.set_yticks(range(len(matrix.index)), matrix.index, fontsize=19)
ax.xaxis.tick_top()
ax.tick_params(length=0)
for i in range(len(matrix.index)):
    for j in range(len(matrix.columns)):
        value = matrix.iloc[i, j]
        text = '—' if i == j else str(value)
        color = 'white' if value >= 80 else '#24364B'
        ax.text(j, i, text, ha='center', va='center',
                fontsize=25, color=color)
for spine in ax.spines.values():
    spine.set_visible(False)
保存静态图(fig, '04_关系矩阵', '关系矩阵：每一对部门协作了多少',
          '与弦图使用同一份数据 · 对称格子代表同一条无向关系')
