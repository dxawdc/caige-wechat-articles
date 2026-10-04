"""执行文章中的四份独立源码，并生成开头效果总览。"""
import json
import runpy
import numpy as np
import pandas as pd
from 图表工具 import ROOT, OUT, plt, INK

if __name__ == '__main__':
    for filename in ['01_桑基图.py', '02_弦图.py', '03_冲积图.py', '04_关系矩阵.py']:
        runpy.run_path(str(ROOT / filename), run_name='__main__')
        print('完成：' + filename)
    labels = ['桑基图｜看分流与汇流', '弦图｜看群体间往来',
              '冲积图｜看状态如何变化', '矩阵图｜看每一对的数量']
    stems = ['01_桑基图', '02_弦图', '03_冲积图', '04_关系矩阵']
    fig, axes = plt.subplots(2, 2, figsize=(10, 9.8), facecolor='#F7FAFD')
    fig.subplots_adjust(left=.03, right=.97, top=.82, bottom=.12, hspace=.27, wspace=.06)
    fig.text(.05, .935, '数据从哪来，又到哪去？', fontsize=31, weight='bold', color=INK)
    fig.text(.05, .867, '4 种图表，看场景、看效果、跟着代码画', fontsize=20, color='#52657A')
    for ax, stem, label in zip(axes.flat, stems, labels):
        pixels = plt.imread(OUT / f'{stem}.png')
        height, width = pixels.shape[:2]
        cropped = pixels[int(height*.18):int(height*.89), int(width*.03):int(width*.97)]
        ax.imshow(cropped)
        ax.axis('off')
        ax.set_title(label, fontsize=20, weight='bold', color=INK, pad=10)
    fig.text(.05, .055, '模拟数据 · Python 实际绘制', fontsize=15, color='#52657A')
    fig.text(.95, .055, '可以叫我才哥', fontsize=15, color='#52657A', ha='right')
    fig.savefig(OUT/'00_效果总览.png', dpi=160, facecolor=fig.get_facecolor())
    fig.savefig(OUT/'00_效果总览.svg', facecolor=fig.get_facecolor())
    plt.close(fig)
    edges = pd.read_csv(ROOT/'数据/桑基图_边表.csv')
    matrix = pd.read_csv(ROOT/'数据/部门协作_矩阵.csv', index_col=0)
    paths = pd.read_csv(ROOT/'数据/冲积图_完整路径.csv')
    assert edges.loc[edges.target=='注册', 'value'].sum() == 600
    assert edges.loc[edges.source=='注册', 'value'].sum() == 600
    assert np.triu(matrix.to_numpy(), 1).sum() == 470
    assert matrix.to_numpy().sum() == 940
    assert paths.value.sum() == 500
    assert paths.loc[paths.month2=='流失', 'value'].sum() == 120
    checks = {'version':'v1.1.0', 'data_type':'模拟教学数据', 'registered':600, 'paid':180,
              'collaboration_pairs_total':470, 'collaboration_endpoints_total':940,
              'cohort_total':500, 'lost':120, 'independent_scripts':4, 'png_count':5, 'status':'passed'}
    (ROOT/'数据验收.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
