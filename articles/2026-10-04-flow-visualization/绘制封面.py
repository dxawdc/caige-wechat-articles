"""按900×383横版尺寸重画桑基图封面；读取正文示例的同一份CSV。"""
import json
import hashlib
import pandas as pd
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle
from 图表工具 import ROOT, COLORS, plt, INK

OUT = ROOT / '封面'
OUT.mkdir(exist_ok=True)
edges = pd.read_csv(ROOT / '数据/桑基图_边表.csv')
values = {(r.source, r.target): int(r.value) for r in edges.itertuples()}
assert len(values) == len(edges) == 8
incoming = edges.groupby('target').value.sum().to_dict()
outgoing = edges.groupby('source').value.sum().to_dict()
assert incoming['注册'] == outgoing['注册'] == 600
assert outgoing['广告'] + outgoing['自然搜索'] + outgoing['好友分享'] == 1000

# 所有节点和流带使用相同的人数—像素比例。
scale = .15
node_colors = dict(zip(['广告', '自然搜索', '好友分享', '注册'], COLORS))
node_colors.update({'付费':'#CB6A7D', '注册未付费':'#7FA4CC', '未注册':'#A0ADB8'})
positions = {'广告':(122,163), '自然搜索':(122,248), '好友分享':(122,303),
             '注册':(434,147), '付费':(750,154),
             '注册未付费':(750,191), '未注册':(750,264)}
totals = {name:int(max(incoming.get(name,0),outgoing.get(name,0))) for name in positions}
width = 14
fig = plt.figure(figsize=(9, 3.83), dpi=100, facecolor='#F7FAFD')
ax = fig.add_axes([0,0,1,1])
ax.set(xlim=(0,900), ylim=(383,0))
ax.axis('off')

def text(x,y,label,size,color=INK,**kwargs):
    return ax.text(x,y,label,fontsize=size*.72,color=color,va='center',**kwargs)

def ribbon(x0,y0,x1,y1,height,color,via=None):
    # 上下边各画一条贝塞尔曲线，两边的差恒为value×scale。
    if via is None:
        d=(x1-x0)*.48
        vertices=[(x0,y0),(x0+d,y0),(x1-d,y1),(x1,y1),
                  (x1,y1+height),(x1-d,y1+height),(x0+d,y0+height),(x0,y0+height),(x0,y0)]
        codes=[Path.MOVETO,*([Path.CURVE4]*3),Path.LINETO,*([Path.CURVE4]*3),Path.CLOSEPOLY]
    else:
        xm,ym=via
        d0=(xm-x0)*.48; d1=(x1-xm)*.48
        vertices=[(x0,y0),(x0+d0,y0),(xm-d0,ym),(xm,ym),
                  (xm+d1,ym),(x1-d1,y1),(x1,y1),(x1,y1+height),
                  (x1-d1,y1+height),(xm+d1,ym+height),(xm,ym+height),
                  (xm-d0,ym+height),(x0+d0,y0+height),(x0,y0+height),(x0,y0)]
        codes=[Path.MOVETO,*([Path.CURVE4]*6),Path.LINETO,*([Path.CURVE4]*6),Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(vertices,codes),facecolor=color,alpha=.52,edgecolor='none'))

source_offsets={name:0 for name in positions}
target_offsets={name:0 for name in positions}
for source,target,value in edges[['source','target','value']].itertuples(index=False,name=None):
    x0,y0=positions[source]; x1,y1=positions[target]
    height=float(value)*scale
    sy=y0+source_offsets[source]; ty=y1+target_offsets[target]
    via=(441,245+target_offsets[target]) if target=='未注册' else None
    ribbon(x0+width,sy,x1,ty,height,node_colors[source],via)
    source_offsets[source]+=height
    target_offsets[target]+=height

for name,(x,y) in positions.items():
    ax.add_patch(Rectangle((x,y),width,totals[name]*scale,facecolor=node_colors[name],edgecolor='none'))
    if name in ['广告','自然搜索','好友分享']:
        text(x-14,y+totals[name]*scale/2,f'{name}\n{totals[name]}人',16,ha='right',linespacing=1.25)
    elif name=='注册':
        text(x+width/2,y-14,f'注册 {totals[name]}人',16,ha='center',weight='bold')
    else:
        text(x+width+17,y+totals[name]*scale/2,f'{name}\n{totals[name]}人',16,ha='left',linespacing=1.25)

text(450,47,'数据从哪来，又到哪去？',34,ha='center',weight='bold')
text(450,86,'桑基图 · 弦图 · 冲积图',20,color='#52657A',ha='center')
text(32,365,'模拟教学数据 · 1000位访客 · 固定7日观察窗',12,color='#63788D')
text(868,365,'可以叫我才哥',12,color='#63788D',ha='right')
fig.savefig(OUT/'桑基图封面.png',dpi=100,facecolor=fig.get_facecolor())
fig.savefig(OUT/'桑基图封面.svg',facecolor=fig.get_facecolor())
plt.close(fig)
result={'dimensions':[900,383],'ratio':'900:383','data_source':'数据/桑基图_边表.csv',
        'data_sha256':hashlib.sha256((ROOT/'数据/桑基图_边表.csv').read_bytes()).hexdigest(),
        'links':len(edges),'visitors':1000,'registered':600,'paid':180,
        'scale_pixels_per_person':scale,'used_in_article_body':False,'status':'passed'}
(ROOT/'封面验收.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
