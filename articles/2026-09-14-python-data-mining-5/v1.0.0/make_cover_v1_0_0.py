"""v1.0.0 | 2026-09-14 | 绘制本篇封面，品牌为公众号名称。"""
from common_v1_0_0 import *
from matplotlib.patches import FancyBboxPatch

def main():
    fig=plt.figure(figsize=(10,4.25));fig.patch.set_facecolor('#f0f7f3')
    fig.text(.06,.84,'PYTHON  /  DATA ANALYSIS',fontsize=13,color=GREEN,weight='bold')
    fig.text(.06,.64,'从预测到分群',fontsize=34,color=INK,weight='bold')
    fig.text(.06,.48,'跑通 5 类数据分析与挖掘模型',fontsize=23,color=INK,weight='bold')
    for i,label in enumerate(['线性回归','逻辑回归','决策树','K-Means','关联规则']):
        x=.06+i*.178
        fig.add_artist(FancyBboxPatch((x,.23),.158,.115,boxstyle='round,pad=0.01',transform=fig.transFigure,facecolor='white',edgecolor='#cbded4'))
        fig.text(x+.079,.27,label,ha='center',fontsize=13,color=GREEN,weight='bold')
    fig.text(.06,.09,'模拟数据 · Python实操 · 指标解读',fontsize=12,color=GRAY)
    fig.text(.94,.09,'可以叫我才哥',ha='right',fontsize=13,color=GREEN)
    fig.savefig(OUT/'00_cover_v1.0.0.png',dpi=150,facecolor=fig.get_facecolor());plt.close(fig)

if __name__=='__main__':main()
