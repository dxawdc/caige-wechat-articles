"""900×383独立微信公众号封面，以真实前3名金牌数绘图。"""
from pathlib import Path
import pandas as pd
from 图表工具 import D, ROOT, plt, RED, BLUE

df=pd.read_csv(D/'国家地区奖牌榜.csv').set_index('noc')
fig=plt.figure(figsize=(9,3.83),dpi=100,facecolor='#F3F7FA')
ax=fig.add_axes([.6,.23,.35,.55],facecolor='#F3F7FA')
values=[int(df.loc[x,'gold']) for x in ['CHN','JPN','KOR']]
ax.barh(['中国','日本','韩国'],values,color=[RED,BLUE,'#5A8C70'],height=.58)
ax.invert_yaxis(); ax.set_xlim(0,195);ax.set_xticks([])
ax.spines[['top','right','left','bottom']].set_visible(False)
ax.tick_params(axis='y',length=0,labelsize=14)
for i,v in enumerate(values):ax.text(v+3,i,str(v),va='center',fontsize=17,weight='bold')
fig.text(.065,.80,'2026 爱知·名古屋',fontsize=16,color=BLUE)
fig.text(.065,.59,'亚运会收官',fontsize=32,weight='bold')
fig.text(.065,.40,'把奖牌榜画出来',fontsize=23,weight='bold')
fig.text(.065,.20,'数据采集  /  地区地图  /  Python代码',fontsize=13)
fig.text(.94,.09,'可以叫我才哥',ha='right',fontsize=11,color='#6C7F8D')
out=ROOT/'封面';out.mkdir(exist_ok=True)
for ext in ['png','svg']:fig.savefig(out/f'亚运会封面.{ext}',dpi=100,facecolor=fig.get_facecolor())
plt.close(fig)
