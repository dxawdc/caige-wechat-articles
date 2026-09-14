"""v1.0.0 | 2026-09-14 | 公共绘图与结果输出；全部数据为模拟数据。"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; OUT=ROOT/'outputs'
DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
fonts={f.name for f in font_manager.fontManager.ttflist}
font=next((x for x in ['Microsoft YaHei','Noto Sans CJK SC','SimHei','Arial Unicode MS'] if x in fonts),'DejaVu Sans')
plt.rcParams.update({'font.family':font,'axes.unicode_minus':False,'font.size':12,'axes.titlesize':17,'axes.labelsize':12,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
GREEN='#168568'; BLUE='#427cbf'; ORANGE='#d68b31'; GRAY='#78858b'; INK='#203d39'

def savefig(fig,name):
    fig.text(.99,.014,'模拟数据 · 可以叫我才哥',ha='right',fontsize=10,color=GRAY)
    fig.savefig(OUT/(name+'_v1.0.0.png'),dpi=180,bbox_inches='tight')
    fig.savefig(OUT/(name+'_v1.0.0.svg'),bbox_inches='tight')
    plt.close(fig)

def result(name,value):
    (OUT/(name+'_v1.0.0.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)),encoding='utf8')

def csv(frame,name):
    frame.to_csv(OUT/(name+'_v1.0.0.csv'),index=False,encoding='utf-8-sig')
