"""四张教学图和一个可离线打开的交互桑基图。数据均为模拟数据。"""
from pathlib import Path
import csv
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import PathPatch, Rectangle, Wedge
from matplotlib.path import Path as MPath
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / '配图'
DATA = ROOT / '数据'
IMAGES.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)
fonts = {x.name for x in font_manager.fontManager.ttflist}
for name in ['Microsoft YaHei', 'Noto Sans CJK SC', 'SimHei', 'Arial Unicode MS']:
    if name in fonts:
        plt.rcParams['font.family'] = name
        break
else:
    raise RuntimeError('请安装中文字体，例如 Noto Sans CJK SC，再运行。')
plt.rcParams.update({'axes.unicode_minus': False, 'font.size': 17, 'svg.fonttype': 'none'})
COLORS = ['#3275BB', '#EE9D3A', '#28A59C', '#906BC3', '#CB6A7D']
INK = '#24364B'

def canvas(title, subtitle, height=6.7):
    fig, ax = plt.subplots(figsize=(8.8, height), facecolor='#F7FAFD')
    ax.set_facecolor('#F7FAFD')
    fig.subplots_adjust(left=.06, right=.94, bottom=.15, top=.77)
    fig.text(.06, .93, title, fontsize=25, weight='bold', color=INK)
    fig.text(.06, .85, subtitle, fontsize=14, color='#52657A')
    fig.text(.06, .055, '模拟数据 · 教学演示', fontsize=13, color='#66778B')
    fig.text(.94, .055, '可以叫我才哥', fontsize=13, ha='right', color='#66778B')
    return fig, ax

def save(fig, stem):
    fig.savefig(IMAGES / (stem + '.png'), dpi=180, facecolor=fig.get_facecolor())
    fig.savefig(IMAGES / (stem + '.svg'), facecolor=fig.get_facecolor())
    plt.close(fig)

def csv_save(name, headers, rows):
    with (DATA / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

def ribbon(ax, x0, y0, x1, y1, height, color, alpha=.48):
    dx = (x1 - x0) * .45
    points = [(x0,y0), (x0+dx,y0), (x1-dx,y1), (x1,y1),
              (x1,y1+height), (x1-dx,y1+height), (x0+dx,y0+height), (x0,y0+height), (x0,y0)]
    codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
             MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(points,codes), facecolor=color, edgecolor='none', alpha=alpha))

def sankey():
    labels = ['广告', '自然搜索', '好友分享', '注册', '付费', '注册未付费', '未注册']
    totals = [500,300,200,600,180,420,400]
    edges = [(0,3,300),(0,6,200),(1,3,200),(1,6,100),(2,3,100),(2,6,100),(3,4,180),(3,5,420)]
    pos = [(0,0),(0,610),(0,1020),(1,0),(2,0),(2,300),(2,840)]
    fig,ax = canvas('桑基图：1000 位访客去了哪里', '同一批用户 · 7 日观察窗 · 每人一个渠道和最终结果', 7.5)
    ax.set_xlim(-.27,2.38); ax.set_ylim(1450,-170); ax.axis('off')
    outgoing=[0]*7; incoming=[0]*7
    for s,t,v in edges:
        x0,y0=pos[s]; x1,y1=pos[t]
        ribbon(ax,x0+.06,y0+outgoing[s],x1,y1+incoming[t],v,COLORS[s%3] if s<3 else COLORS[t%5])
        outgoing[s]+=v; incoming[t]+=v
    for i,((x,y),v,name) in enumerate(zip(pos,totals,labels)):
        ax.add_patch(Rectangle((x,y),.06,v,facecolor=COLORS[i%5],edgecolor='none'))
        ax.text(x+.03,y-18,f'{name} {v}',ha='center',va='bottom',fontsize=17,weight='bold',color=INK,
                bbox={'facecolor':'#F7FAFD','edgecolor':'none','pad':1.5})
    save(fig,'01_桑基图')
    csv_save('桑基图_边表.csv',['source','target','value'],[(labels[s],labels[t],v) for s,t,v in edges])
    interactive=go.Figure(go.Sankey(node={'label':[f'{x} {v}人' for x,v in zip(labels,totals)],'pad':30},
        link={'source':[e[0] for e in edges],'target':[e[1] for e in edges],'value':[e[2] for e in edges]},
        valueformat='.0f',valuesuffix='人'))
    interactive.update_layout(title='模拟数据：1000位访客的注册与付费去向｜可以叫我才哥',font={'size':17},height=750)
    interactive.write_html(ROOT/'交互桑基图.html',include_plotlyjs=True,full_html=True)
    assert sum(totals[:3]) == 1000 == sum(totals[4:])
    assert sum(v for s,t,v in edges if t==3)==600==sum(v for s,t,v in edges if s==3)
    return edges

def chord_and_matrix():
    names=['产品','研发','设计','运营']
    matrix=np.array([[0,120,80,40],[120,0,100,60],[80,100,0,70],[40,60,70,0]])
    csv_save('部门协作_矩阵.csv',['部门']+names,[[n]+list(row) for n,row in zip(names,matrix)])
    pairs=[(i,j,int(matrix[i,j])) for i in range(4) for j in range(i+1,4)]
    csv_save('部门协作_边表.csv',['source','target','value'],[(names[i],names[j],v) for i,j,v in pairs])
    fig,ax=canvas('弦图：部门之间怎样协作', '无向关系 · 每对部门只记一次 · 带宽表示协作次数',8.3)
    ax.set_aspect('equal'); ax.set_xlim(-1.48,1.48);ax.set_ylim(-1.4,1.4);ax.axis('off')
    gap=.09; unit=(2*math.pi-gap*4)/matrix.sum(); start=.25
    segments={}
    for i in range(4):
        end=start+matrix[i].sum()*unit
        ax.add_patch(Wedge((0,0),1.04,math.degrees(start),math.degrees(end),width=.09,facecolor=COLORS[i]))
        mid=(start+end)/2
        ax.text(1.24*math.cos(mid),1.24*math.sin(mid),f'{names[i]}\n{matrix[i].sum()}次',ha='center',va='center',fontsize=19,weight='bold',color=INK)
        cursor=start
        for j in range(4):
            if matrix[i,j]:
                segments[i,j]=(cursor,cursor+matrix[i,j]*unit)
                cursor+=matrix[i,j]*unit
        start=end+gap
    for i,j,v in sorted(pairs,key=lambda e:e[2]):
        a,b=segments[i,j];c,d=segments[j,i]
        arc1=[(.94*math.cos(t),.94*math.sin(t)) for t in np.linspace(a,b,24)]
        arc2=[(.94*math.cos(t),.94*math.sin(t)) for t in np.linspace(c,d,24)]
        pts=arc1+[(0,0),arc2[0]]+arc2[1:]+[(0,0),arc1[0],arc1[0]]
        codes=[MPath.MOVETO]+[MPath.LINETO]*23+[MPath.CURVE3,MPath.CURVE3]+[MPath.LINETO]*23+[MPath.CURVE3,MPath.CURVE3,MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(pts,codes),facecolor=COLORS[i],edgecolor='white',lw=.5,alpha=.48))
    save(fig,'02_弦图')
    fig,ax=canvas('同一份协作数据，换成矩阵看', '行与列都是部门 · 格子表示两部门协作次数',7.5)
    ax.imshow(matrix,cmap='Blues',vmin=0,vmax=120)
    ax.set_xticks(range(4),names,fontsize=19);ax.set_yticks(range(4),names,fontsize=19)
    ax.tick_params(length=0);ax.xaxis.tick_top()
    for i in range(4):
        for j in range(4):
            ax.text(j,i,'—' if i==j else str(matrix[i,j]),ha='center',va='center',fontsize=24,color='white' if matrix[i,j]>=80 else INK)
    for s in ax.spines.values():s.set_visible(False)
    fig.text(.5,.105,'对称格子是同一条关系；合计时只取半个矩阵',ha='center',fontsize=13,color='#52657A')
    save(fig,'04_关系矩阵')
    assert np.array_equal(matrix,matrix.T) and np.triu(matrix,1).sum()==470
    return matrix

def alluvial():
    rows=[('新用户','轻度','轻度',180),('新用户','轻度','流失',80),('新用户','轻度','重度',40),
          ('新用户','重度','重度',100),('回流用户','重度','重度',60),('回流用户','重度','流失',40)]
    csv_save('冲积图_完整路径.csv',['cohort','month1','month2','value'],rows)
    orders=[['新用户','回流用户'],['轻度','重度'],['轻度','重度','流失']]
    fig,ax=canvas('冲积图：同一批用户如何变化', '500 位用户 · 3 个观察点 · 蓝色新用户，橙色回流用户',7.5)
    ax.set_xlim(-.25,2.3);ax.set_ylim(780,-190);ax.axis('off')
    bounds={}; centers={}
    for stage,order in enumerate(orders):
        cursor=0
        for name in order:
            total=sum(r[3] for r in rows if r[stage]==name)
            offset=cursor
            for i,r in enumerate(rows):
                if r[stage]==name:
                    bounds[stage,i]=offset;offset+=r[3]
            centers[stage,name]=(cursor,total)
            cursor+=total+90
    for i,row in enumerate(rows):
        for stage in [0,1]:
            ribbon(ax,stage+.06,bounds[stage,i],stage+1,bounds[stage+1,i],row[3],COLORS[0 if row[0]=='新用户' else 1],.55)
    for (stage,name),(y,v) in centers.items():
        ax.add_patch(Rectangle((stage,y),.06,v,facecolor=INK,alpha=.7))
        ax.text(stage+.03,y-12,f'{name} {v}',ha='center',va='bottom',fontsize=17,weight='bold',color=INK,
                bbox={'facecolor':'#F7FAFD','edgecolor':'none','pad':1.5})
    for i,t in enumerate(['进入批次','第 1 月','第 2 月']):ax.text(i+.03,-120,t,ha='center',fontsize=19,color=INK)
    save(fig,'03_冲积图')
    assert sum(r[3] for r in rows)==500
    assert sum(r[3] for r in rows if r[1]=='轻度')==300
    assert sum(r[3] for r in rows if r[2]=='流失')==120
    return rows

if __name__=='__main__':
    edges=sankey();matrix=chord_and_matrix();rows=alluvial()
    result={'数据类型':'模拟教学数据','sankey_initial':1000,'sankey_registered':600,'sankey_paid':180,
        'sankey_unregistered':400,'sankey_registered_unpaid':420,'registration_rate':.6,'paid_per_registration':.3,
        'paid_per_visitor':.18,'chord_unique_pair_total':470,'chord_endpoint_total':int(matrix.sum()),
        'alluvial_total':500,'alluvial_lost':120,'png_count':len(list(IMAGES.glob('*.png'))),'checks':'passed'}
    (ROOT/'数据验收.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
