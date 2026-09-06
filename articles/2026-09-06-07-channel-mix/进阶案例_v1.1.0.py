"""v1.1.0 | 2026-09-06 | 教学模拟数据，运行断言并生成解释图。"""
from pathlib import Path
import json,runpy,math,sqlite3
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parent
g=runpy.run_path(str(ROOT/'绘图工具_v1.0.0.py'))
plt=g['plt'];figure=g['figure']
def explain(title,note,frame):
    fig,ax=figure(title,note);ax.axis('off')
    widths=[.23,.12,.65] if list(frame.columns)==['路径结果','人数','事件证据'] else None
    t=ax.table(cellText=frame.astype(str).values,colLabels=frame.columns,colWidths=widths,cellLoc='center',bbox=[-.06,-.04,1.1,1.10])
    t.auto_set_font_size(False);t.set_fontsize(11)
    for (r,c),cell in t.get_celld().items():
        cell.set_edgecolor('white');cell.set_linewidth(2)
        cell.set_facecolor('#e9f1fa' if r==0 else ('#f4f6f9' if r%2 else 'white'))
        if r==0:cell.set_text_props(weight='bold')
    fig.savefig(ROOT/'图片/03_进阶解释_v1.1.0.png',dpi=200);plt.close(fig)
def finish(values,checks):
    (ROOT/'结果/进阶验收_v1.1.0.json').write_text(json.dumps({'version':'v1.1.0','simulated':True,'passed':True,'checks':checks,**values},ensure_ascii=False,indent=2),encoding='utf-8')

# BEGIN MAIN
# 独立情景：组内提升幅度不同，展示基准顺序的影响。
w0=np.array([.8,.2]);w1=np.array([.3,.7])
r0=np.array([.6,.2]);r1=np.array([.7,.25])
old=float(w0@r0);new=float(w1@r1)
rate_first=float(w0@(r1-r0))
mix_after=float((w1-w0)@r1)
mix_first=float((w1-w0)@r0)
rate_after=float(w1@(r1-r0))
assert np.isclose(rate_first+mix_after,new-old)
assert np.isclose(mix_first+rate_after,new-old)
interaction=float((w1-w0)@(r1-r0))
symmetric_rate=(rate_first+rate_after)/2
symmetric_mix=(mix_first+mix_after)/2
# END MAIN
assert np.allclose([old,new,rate_first,mix_after,mix_first,rate_after],[.52,.385,.09,-.225,-.20,.065])
assert np.isclose(interaction,-.025)
assert np.allclose([symmetric_rate,symmetric_mix],[.0775,-.2125])
frame=pd.DataFrame([
 ['先换留存，再换结构','+9.00','-22.50','-13.50'],
 ['先换结构，再换留存','+6.50','-20.00','-13.50'],
 ['两条路径平均','+7.75','-21.25','-13.50'],
],columns=['计算路径','组内项/百分点','结构项/百分点','合计/百分点'])
frame.to_csv(ROOT/'数据/分解顺序对照_v1.1.0.csv',index=False,encoding='utf-8-sig')
explain('总变化相同，分项为何不同','独立情景：旧整体 52%，新整体 38.5%；本图不是因果归因',frame)
finish({'old':old,'new':new,'interaction_pp':interaction*100,'symmetric_rate_pp':symmetric_rate*100,'symmetric_mix_pp':symmetric_mix*100},5)
