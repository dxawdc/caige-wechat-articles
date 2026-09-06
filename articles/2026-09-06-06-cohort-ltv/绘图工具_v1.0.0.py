"""v1.0.0 | 2026-09-06 | 公众号教学案例静态绘图工具。"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
ROOT=Path(__file__).resolve().parent
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei','Noto Sans CJK SC','DejaVu Sans'], 'axes.unicode_minus':False,'font.size':13,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'white','axes.labelcolor':'#263247','text.color':'#263247','xtick.color':'#59677b','ytick.color':'#59677b'})
BLUE='#3478b8'; ORANGE='#db8c30'; GRAY='#e9edf2'; INK='#263247'
def figure(title, note):
    fig,ax=plt.subplots(figsize=(7.2,4.8),dpi=200)
    fig.subplots_adjust(left=.14,right=.95,top=.78,bottom=.19)
    fig.text(.08,.94,title,fontsize=19,weight='bold',va='top')
    fig.text(.08,.865,note,fontsize=10.5,color='#66748a',va='top')
    fig.text(.08,.045,'教学模拟数据  ·  才哥AGI',fontsize=10,color='#7b8796')
    return fig,ax
def save(fig,name):
    (ROOT/'图片').mkdir(exist_ok=True)
    fig.savefig(ROOT/'图片'/f'{name}_v1.0.0.png',dpi=200)
    plt.close(fig)
def bar(title,note,labels,values,name,unit='',colors=None):
    fig,ax=figure(title,note)
    fig.subplots_adjust(left=.28)
    y=np.arange(len(labels));ax.barh(y,values,color=colors or BLUE,height=.54)
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(0,max(values)*1.28 if max(values)>0 else 1)
    ax.set_xlabel(unit);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    for i,v in enumerate(values):ax.text(v+max(values)*.02,i,f'{v:.2f}'.rstrip('0').rstrip('.'),va='center',fontsize=14,weight='bold')
    save(fig,name)
def table(title,note,frame,name):
    fig,ax=figure(title,note);ax.axis('off')
    t=ax.table(cellText=frame.astype(str).values,colLabels=list(frame.columns),loc='center',cellLoc='center',bbox=[-.06,-.02,1.1,1.02])
    t.auto_set_font_size(False);t.set_fontsize(12)
    for (r,c),cell in t.get_celld().items():
        cell.set_edgecolor('white');cell.set_linewidth(2)
        cell.set_facecolor('#e9f1fa' if r==0 else ('#f4f6f9' if r%2 else '#ffffff'))
        if r==0:cell.set_text_props(weight='bold',color=INK)
    save(fig,name)
def result(value):
    (ROOT/'结果').mkdir(exist_ok=True)
    (ROOT/'结果/验收结果_v1.0.0.json').write_text(json.dumps({'version':'v1.0.0','simulated':True,**value},ensure_ascii=False,indent=2),encoding='utf-8')
def csv(frame,name):
    (ROOT/'数据').mkdir(exist_ok=True)
    frame.to_csv(ROOT/'数据'/f'{name}_v1.0.0.csv',index=False,encoding='utf-8-sig')
