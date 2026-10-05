"""统一绘制公众号与4K静态图：图内仅标题、范围、刻度、图例和数值。"""
from pathlib import Path
import json,sys,math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from matplotlib.patches import Polygon,Rectangle,FancyBboxPatch
from matplotlib.collections import PatchCollection
from matplotlib.colors import ListedColormap,BoundaryNorm
from PIL import Image,ImageOps,ImageDraw,ImageFont
from pyproj import Transformer
R=Path(__file__).resolve().parents[1];D=R/'data'
BG='#FFFFFF';INK='#191919';GREEN='#E9875D';SOFT='#7CC4CE';GOLD='#3296A7';GRAY='#858585';GRID='#ECECEC';RED='#CB603C'
PALE_BLUE='#E9F6F7';PALE_ORANGE='#FCEADC';PALE_GRAY='#F4F4F4';BLUE_INK='#246879'
fontManager.addfont('C:/Windows/Fonts/msyh.ttc')
fontManager.addfont('C:/Windows/Fonts/msyhbd.ttc')
plt.rcParams.update({'font.family':'Microsoft YaHei','axes.unicode_minus':False,'font.size':13,'axes.edgecolor':GRID,'xtick.color':GRAY,'ytick.color':INK,'axes.labelcolor':GRAY})
prov=pd.read_csv(D/'省级数量.csv');city=pd.read_csv(D/'市级数量.csv');master=pd.read_csv(D/'全国5A景区主表.csv')
years=pd.read_csv(D/'现存名录认定年分布.csv');historic=pd.read_csv(D/'历史公开数量节点.csv');latest=pd.read_csv(D/'最新认定批次.csv');types=pd.read_csv(D/'景区类型数量.csv')
price=pd.read_csv(D/'门票核验样本.csv');fin=pd.read_csv(D/'上市运营公司财务样本.csv');seg=pd.read_csv(D/'峨眉山收入构成.csv');projects=pd.read_csv(D/'景区相关项目与业务收入.csv')
ev=json.loads((D/'evidence_summary.json').read_text('utf-8'))
features=json.loads((D/'city_features.json').read_text('utf-8'))['features'];country=json.loads((D/'sources/china_national.json').read_text('utf-8'))['features'];boundaries=json.loads((D/'sources/china_boundaries.json').read_text('utf-8'))['features']
transform=Transformer.from_crs('EPSG:4326','+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +datum=WGS84 +units=m',always_xy=True)
TEXT_LOG=[];LAYOUT_LOG=[]
def text(f,x,y,t,size=13,color=INK,weight=None,**kw):
    TEXT_LOG.append(str(t));return f.text(x,y,t,fontsize=size,color=color,weight=weight,**kw)
def sheet(title,scope='',height=6,wide=False):
    f=plt.figure(figsize=(16,9) if wide else (6,height),facecolor=BG);h=9 if wide else height
    x=.055 if wide else .055
    text(f,x,1-.23/h,title,29 if wide else 23,INK,'bold',va='top',linespacing=1.35)
    scope_offset=1.32 if '\n' in title else 1.02
    if scope:text(f,x,1-scope_offset/h,scope,12,GRAY,va='top')
    text(f,x,.20/h,'可以叫我才哥 · 5A数据图鉴',10,GRAY)
    text(f,.945,.20/h,'2026.10.05',10,GRAY,ha='right')
    return f
def axis(f,rect,title=None,unit=None):
    a=f.add_axes(rect,facecolor=BG)
    for s in ['top','right','left']:a.spines[s].set_visible(False)
    a.tick_params(length=0,pad=7,labelsize=13);a.grid(axis='x',color=GRID,lw=.7);a.set_axisbelow(True)
    if title:a.set_title(title,fontsize=16,color=INK,loc='left',pad=15)
    if unit:a.set_xlabel(unit,fontsize=12,labelpad=8)
    return a
def bars(a,labels,values,maxv=None,colors=GREEN,fs=14,fmt=lambda v:f'{v:g}'):
    vals=np.asarray(values);y=np.arange(len(vals));mx=maxv or max(vals.max(),1)*1.2
    a.barh(y,vals,color=colors,height=.64);a.set_yticks(y,labels,fontsize=fs);a.invert_yaxis();a.set_xlim(0,mx)
    for j,v in enumerate(vals):a.text(v+mx*.02,j,fmt(v),va='center',fontsize=fs,color=INK)
def ranked(a,labels,values,maxv=None,fs=15,fmt=lambda v:f'{v:g}',shares=None,rank=True):
    """固定同一零点与线性长度，用编号、行背景和数值标签构成榜单。"""
    values=np.asarray(values); n=len(values); maxv=maxv or max(values.max(),1)*1.13
    a.set_xlim(0,1);a.set_ylim(n-.35,-.75);a.set_axis_off()
    start=.37 if rank else .28; end=.81 if shares is None else .70
    for i,(label,v) in enumerate(zip(labels,values)):
        row_h=.84 if n>15 else .68;label_h=.66 if n>15 else .47
        a.add_patch(FancyBboxPatch((.01,i-row_h/2),.98,row_h,boxstyle='round,pad=0,rounding_size=.03',facecolor=BG,edgecolor=GRID,lw=.65))
        if rank:a.text(.049,i,f'{i+1}',color=GREEN if i<3 else GOLD,fontsize=fs+1,ha='center',va='center',weight='bold')
        lx=.085 if rank else .015;lw=start-lx-.025
        a.add_patch(FancyBboxPatch((lx,i-label_h/2),lw,label_h,boxstyle='round,pad=0,rounding_size=.02',facecolor=PALE_BLUE,edgecolor='none'))
        a.text(lx+lw/2,i,label,fontsize=fs,ha='center',va='center',color=INK)
        a.plot([start,end],[i,i],lw=7,color=PALE_GRAY,solid_capstyle='round')
        if v:a.plot([start,start+(end-start)*v/maxv],[i,i],lw=7,color=GREEN,solid_capstyle='butt')
        vx=.90 if shares is None else .78
        a.add_patch(FancyBboxPatch((vx-.06,i-label_h/2),.12,label_h,boxstyle='round,pad=0,rounding_size=.025',facecolor=PALE_BLUE,edgecolor='none'))
        a.text(vx,i,fmt(v),fontsize=fs,color=BLUE_INK,weight='bold',ha='center',va='center')
        if shares is not None:a.text(.94,i,f'{shares[i]:.1%}',fontsize=fs-1,color=BLUE_INK,ha='center',va='center')
    a.text(.045 if rank else .02,-.66,'排名' if rank else '票价',fontsize=fs-1,color=GRAY,ha='center',va='bottom')
    a.text((.085+start)/2 if rank else .13,-.66,'地区' if rank else '',fontsize=fs-1,color=GRAY,ha='center',va='bottom')
    a.text(.90 if shares is None else .78,-.66,'数量 / 家',fontsize=fs-1,color=GRAY,ha='center',va='bottom')
    if shares is not None:a.text(.94,-.66,'占比',fontsize=fs-1,color=GRAY,ha='center',va='bottom')
def geometry(g,project=True,main=False):
    polys=[g['coordinates']] if g['type']=='Polygon' else g.get('coordinates',[]) if g['type']=='MultiPolygon' else []
    out=[]
    for p in polys:
        r=np.asarray(p[0])
        if main and r[:,1].max()<18:continue
        x,y=transform.transform(r[:,0],r[:,1]) if project else (r[:,0],r[:,1]);out.append(Polygon(np.c_[x,y],closed=True))
    return out
def mapplot(f,rect):
    a=f.add_axes(rect,facecolor=BG);a.set_axis_off();a.set_aspect('equal')
    colors=['#FFFFFF','#FFF0E4','#FBD1B0','#F5AF82','#E9875D','#CB603C'];cmap=ListedColormap(colors);norm=BoundaryNorm([-.5,.5,1.5,3.5,5.5,8.5,20],6);counts=city.set_index('city_code')['count'].to_dict()
    for ft in features:
        a.add_collection(PatchCollection(geometry(ft['geometry'],main=True),facecolor=cmap(norm(counts.get(int(ft['properties']['adcode']),0))),edgecolor='#D9D9D9',lw=.18))
    for ft in boundaries:
        code=ft['properties']['adcode']
        if isinstance(code,int):a.add_collection(PatchCollection(geometry(ft['geometry'],main=True),facecolor='#E9E9E9' if code in [710000,810000,820000] else 'none',edgecolor=GRAY,lw=.35))
    for ft in country:a.add_collection(PatchCollection(geometry(ft['geometry'],main=True),facecolor='none',edgecolor=GRAY,lw=.55))
    a.set_xlim(-2900000,2400000);a.set_ylim(1600000,6050000)
    for code,label,offset in [(500000,'重庆 12',(-36,-9)),(110000,'北京 9',(8,9)),(320500,'苏州 6',(8,-8))]:
        ft=next(i for i in features if int(i['properties']['adcode'])==code);xy=transform.transform(*(ft['properties'].get('centroid') or ft['properties']['center']))
        a.annotate(label,xy,xytext=offset,textcoords='offset points',fontsize=11,color=INK,bbox=dict(fc=BG,ec='none',alpha=.85,pad=1))
    x,y=transform.transform(121,23.5);a.text(x,y,'台湾',fontsize=9,color=GRAY)
    ins=f.add_axes([rect[0]+rect[2]*.82,rect[1]+.01,rect[2]*.15,rect[3]*.25],facecolor=BG)
    for ft in country:ins.add_collection(PatchCollection(geometry(ft['geometry'],False),facecolor=PALE_ORANGE,edgecolor=GRAY,lw=.4))
    for ft in boundaries:
        if ft['properties']['adcode']=='100000_JD':ins.add_collection(PatchCollection(geometry(ft['geometry'],False),facecolor=GRAY,edgecolor='none'))
    ins.set_xlim(106,124);ins.set_ylim(2,24);ins.set_aspect('equal');ins.set_xticks([]);ins.set_yticks([]);ins.set_title('南海诸岛',fontsize=8)
    for s in ins.spines.values():s.set_color(GRID)
    return colors
def maplegend(f,colors,x=.09,y=.12,width=.83):
    for i,(c,l) in enumerate(zip(colors,['0','1','2–3','4–5','6–8','9+'])):
        xx=x+i*width/6;f.add_artist(Rectangle((xx,y),width/6*.30,.020,transform=f.transFigure,facecolor=c,edgecolor=GRID,lw=.5));text(f,xx+width/6*.40,y,l,11)
def province(a,fs=14):ranked(a,prov.province,prov['count'],30,fs=fs,fmt=lambda v:f'{v:g}')
def pareto(a):
    v=prov['count'].to_numpy();x=np.arange(1,len(v)+1);cum=np.cumsum(v)/sum(v)*100
    a.grid(False);a.bar(x,v,color=GREEN,width=.75,label='数量');a.set_xlim(.3,31.8);a.set_ylim(0,31);a.set_xticks([1,5,10,15,20,25,31]);a.set_xlabel('省级数量排名',fontsize=12);a.set_ylabel('家',fontsize=12)
    b=a.twinx();b.plot(x,cum,color=GOLD,lw=2.2,label='累计占比');b.set_ylim(0,110);b.set_yticks([0,20,40,60,80,100],[f'{v}%' for v in [0,20,40,60,80,100]],fontsize=11)
    b.axhline(80,color=GRAY,ls='--',lw=.8);b.scatter([20],[cum[19]],color=RED,s=30);b.annotate('20',(20,cum[19]),xytext=(-8,11),textcoords='offset points',fontsize=12,color=RED)
    for s in ['top','right','left']:b.spines[s].set_visible(False)
    a.legend(handles=[plt.Rectangle((0,0),1,1,color=GREEN),plt.Line2D([0],[0],color=GOLD,lw=2)],labels=['数量','累计占比'],frameon=False,fontsize=11,loc='upper right')
def recognition(a):
    a.grid(False);xx=years.directory_first_year;v=years.existing_count;a.bar(xx,v,color=GREEN,width=.7);a.set_ylim(0,76);a.set_xticks([2007,2011,2015,2019,2024]);a.set_ylabel('现存家数',fontsize=12)
    for x,y in zip(xx,v):
        if y>=25:a.text(x,y+2,str(y),ha='center',fontsize=10,color=INK)
    b=a.twinx();b.plot(xx,years.retrospective_cumulative_existing,color=GOLD,lw=2);b.set_ylim(0,400);b.set_yticks([0,200,400]);b.set_ylabel('回溯累计',fontsize=11,color=GOLD);b.tick_params(length=0,labelsize=11)
    for s in ['top','right','left']:b.spines[s].set_visible(False)
def history(a):
    h=historic[historic.year!=2007];x=np.arange(len(h));a.grid(False);a.scatter(x,h['count'],s=75,color=GREEN);a.set_xticks(x,h.year.astype(str));a.set_xlim(-.4,len(h)-.6);a.set_ylim(0,410);a.set_ylabel('家',fontsize=12)
    for xx,y in zip(x,h['count']):a.text(xx,y+17,str(y),ha='center',fontsize=13,color=INK)
short={24:'衡水湖',35:'晋祠天龙山',44:'老牛湾黄河大峡谷',60:'大安嫩江湾',67:'扎龙',120:'金华双龙',145:'冠豸山',160:'篁岭',176:'周村古商城',193:'宝泉',209:'麻城龟峰山',237:'万绿湖',247:'花山岩画',284:'成都天台山',294:'万峰林',323:'乾陵',331:'冶力关',341:'六盘山红军长征',357:'天山托木尔'}
def batch(f,rect,columns=1):
    x,y,w,h=rect;rows=math.ceil(len(latest)/columns)
    for i,r in latest.reset_index(drop=True).iterrows():
        col=i//rows;row=i%rows;xx=x+col*w/columns;yy=y+h-(row+.5)*h/rows
        f.add_artist(FancyBboxPatch((xx-.006,yy-h/rows*.34),w/columns*.95,h/rows*.68,boxstyle='round,pad=0.003,rounding_size=.006',transform=f.transFigure,facecolor=PALE_BLUE if row%2==0 else BG,edgecolor=GRID,lw=.7))
        text(f,xx+.012,yy,f'{i+1:02d}',13,GREEN,'bold',va='center');text(f,xx+w/columns*.14,yy,r.province,13,BLUE_INK,va='center');text(f,xx+w/columns*.33,yy,short[int(r.atlas_id)],15 if columns==1 else 13,INK,'bold',va='center')
        f.add_artist(plt.Line2D([xx,xx+w/columns*.95],[yy-h/rows*.46]*2,transform=f.transFigure,color=GRID,lw=.6))
def typebars(a,fs=15):
    ranked(a,types.category,types['count'],170,fs=fs,fmt=lambda v:f'{v:g}',shares=types['count'].to_numpy()/358)
    # 类型榜单使用明确类别名。
    a.text(.22,-.66,'景区类型',fontsize=fs-1,color=GRAY,ha='center',va='bottom',bbox={'fc':BG,'ec':'none','pad':2})
def pricedist(a):
    freq=[int((price.adult_peak_regular_yuan==0).sum())]+[int(((price.adult_peak_regular_yuan>lo)&(price.adult_peak_regular_yuan<=hi)).sum()) for lo,hi in [(0,50),(50,100),(100,150),(150,200)]]
    bars(a,['免费','1–50元','51–100元','101–150元','151–200元'],freq,max(freq)*1.3,colors=[SOFT,GREEN,GREEN,GREEN,GREEN],fs=15,fmt=lambda v:f'{v:g}家');step=10 if max(freq)>30 else 5;a.set_xticks(np.arange(0,max(freq)*1.3,step));a.set_xlabel('景区数量 / 家',fontsize=12)
companies=fin[(fin.year==2025)&(fin.comparison_group=='旅游运营公司')].sort_values('revenue_yi',ascending=False).company.tolist()
def revenue(a,fs=14):
    y=np.arange(len(companies))
    for j,(year,col) in enumerate([(2023,'#F9D8C6'),(2024,'#F1B391'),(2025,GREEN)]):
        vals=fin[fin.year==year].set_index('company').loc[companies,'revenue_yi'].to_numpy();a.barh(y+(j-1)*.22,vals,height=.19,color=col,label=str(year))
        if year==2025:
            for i,v in enumerate(vals):a.text(v+.3,y[i]+.22,f'{v:.2f}',va='center',fontsize=12,color=INK)
    a.set_yticks(y,companies,fontsize=fs);a.invert_yaxis();a.set_xlim(0,26);a.set_xticks([0,10,20]);a.legend(loc='lower right',fontsize=10,frameon=False,ncol=3)
def profit(a,fs=14):
    y=np.arange(len(companies));f25=fin[fin.year==2025].set_index('company').loc[companies]
    for j,(key,col,label) in enumerate([('net_profit_yi',GREEN,'归母'),('adjusted_net_profit_yi',GOLD,'扣非归母')]):
        vals=f25[key].to_numpy();a.barh(y+(j-.5)*.50,vals,height=.34,color=col,label=label)
        for i,v in enumerate(vals):a.text(v+.11 if v>=0 else v-.11,y[i]+(j-.5)*.50,f'{v:.2f}',va='center',ha='left' if v>=0 else 'right',fontsize=12,color=INK)
    a.axvline(0,color=GRAY,lw=.7);a.set_yticks(y,companies,fontsize=fs);a.invert_yaxis();a.set_xlim(-7,4.8);a.set_xticks([-6,-3,0,3]);a.legend(loc='lower left',fontsize=10,frameon=False)
def composition(f,rect):
    a=f.add_axes(rect,facecolor=BG);values=seg.revenue_wan.to_numpy()/10000
    a.pie(values,labels=['索道','游山票','酒店','其他'],colors=[GREEN,SOFT,'#F3C39A','#BFDDE1'],startangle=90,wedgeprops={'width':.38,'edgecolor':BG,'linewidth':3},autopct='%1.1f%%',pctdistance=.81,textprops={'fontsize':14,'color':INK})
    a.text(0,.10,f'{values.sum():.2f}',ha='center',va='center',fontsize=25,color=INK,weight='bold');a.text(0,-.14,'亿元',ha='center',fontsize=12,color=GRAY);a.set_aspect('equal')
def projectbars(a,kind,fs=14):
    p=projects[projects.scope_type==kind].sort_values('revenue_yi',ascending=False)
    labels=p.project.tolist()
    if kind=='经营主体':labels=[n+'*' if n.startswith('乌镇') else n for n in labels]
    bars(a,labels,p.revenue_yi,p.revenue_yi.max()*1.28,fs=fs,fmt=lambda v:f'{v:.2f}');a.set_xticks([0,5,10,15] if kind=='经营主体' else [0,1,2,3,4])
def province_types(a):
    p=master.assign(macro=master.category.map({'自然风光':'自然','历史人文':'人文','宗教文化':'人文','红色纪念':'人文','古城古镇':'人文','主题休闲':'休闲','综合景观':'综合'}));mx=pd.crosstab(p.province,p.macro).reindex(prov.province).fillna(0);mx.loc['陕西','自然']+=1;names=prov.head(10).province.tolist();left=np.zeros(len(names))
    for col,c in [('自然',GREEN),('人文',SOFT),('休闲','#F3C39A'),('综合','#BFDDE1')]:
        v=mx.loc[names,col].to_numpy();a.barh(np.arange(len(names)),v,left=left,color=c,height=.63,label=col);left+=v
    a.set_yticks(range(len(names)),names,fontsize=15);a.invert_yaxis();a.set_xlim(0,30);a.set_xticks([0,10,20,30]);a.legend(loc='lower right',frameon=False,fontsize=11,ncol=2)
def save(f,folder,name,wide=False):
    f.canvas.draw();renderer=f.canvas.get_renderer();bounds=f.bbox
    boxes=[t.get_window_extent(renderer) for t in f.texts]
    assert all(b.x0>=-1 and b.x1<=bounds.width+1 and b.y0>=-1 and b.y1<=bounds.height+1 for b in boxes),f'文字超出图片范围: {name}'
    gap=boxes[0].y0-boxes[1].y1
    assert gap>=3,f'标题与范围标注重叠: {name}, gap={gap}'
    overlap=[]
    for a in f.axes:
        for label in list(a.texts)+[a.title,a._left_title]:
            if label.get_text() and label.get_visible() and boxes[1].overlaps(label.get_window_extent(renderer)):
                overlap.append(label.get_text())
    assert not overlap,f'范围说明与图表标签重叠: {name}, {overlap}'
    LAYOUT_LOG.append({'figure':name,'header_gap_px_at_100dpi':round(gap,2),'figure_text_inside_bounds':True,'scope_clear_of_plot_labels':True})
    folder.mkdir(exist_ok=True);f.savefig(folder/(name+'.png'),dpi=240 if wide else 200);plt.close(f);print('SAVED',name,flush=True)
def render_article():
    out=R/'文章配图'
    f=sheet('全国358家5A，\n都分布在哪里？','市级数量 · 白色为0',6.2);colors=mapplot(f,[.025,.17,.95,.57]);maplegend(f,colors,y=.11);save(f,out,'01_全国市级分布')
    f=sheet('江苏26家、浙江22家，\n5A景区数量领跑全国','31个省级地区 · 359条属地记录',13.2);province(axis(f,[.04,.065,.92,.79]),fs=15);save(f,out,'02_各省级地区数量')
    f=sheet('5A景区省级数量，\n前5个地区占28.1%','359条属地记录 · 累计占比',6.2);pareto(axis(f,[.13,.17,.72,.55]));save(f,out,'03_省级集中度')
    f=sheet('从首批66家，\n到现存358家5A','现存名录回溯 · 历史公开节点',8.7);recognition(axis(f,[.15,.46,.69,.29],title='现存目录认定年'));history(axis(f,[.15,.12,.73,.24],title='历史公开数量节点'));save(f,out,'04_认定年份与历史节点')
    f=sheet('新晋19家5A，\n分布在19个省级地区','2024.12.26正式认定',9.2);batch(f,[.06,.085,.89,.74]);save(f,out,'05_最新批次名单')
    f=sheet('自然风光159家，\n占全国5A的44.4%','358家 · 作者主要体验分类',6.4);typebars(axis(f,[.04,.12,.92,.58]),fs=15);save(f,out,'06_景区类型')
    f=sheet('基础票样本中，\n51—100元这一档最多',f'{len(price)}家基础票 · 非随机样本',6.9);pricedist(axis(f,[.29,.265,.57,.47]));text(f,.07,.115,'样本均价',11,GRAY);text(f,.28,.105,f'{price.adult_peak_regular_yuan.mean():.1f}元',21,GREEN,'bold');text(f,.56,.115,'中位数',11,GRAY);text(f,.75,.105,f'{price.adult_peak_regular_yuan.median():g}元',21,BLUE_INK,'bold');save(f,out,'07_门票样本')
    f=sheet('12家旅游运营公司的\n三年营收与2025年利润','公司合并口径 · 亿元',12);revenue(axis(f,[.28,.52,.59,.30],title='营业收入'));profit(axis(f,[.28,.075,.59,.365],title='2025年利润'));save(f,out,'08_运营公司财务')
    f=sheet('峨眉山A的账本里，\n索道收入高于游山门票','2025年 · 公司合并口径',7);composition(f,[.13,.25,.74,.45]);
    for i,(name,value,col) in enumerate(zip(['索道','游山票','酒店','其他'],seg.revenue_wan.to_numpy()/10000,[GREEN,SOFT,'#F3C39A','#BFDDE1'])):
        x=.07+(i%2)*.47;y=.185-(i//2)*.082;f.add_artist(Rectangle((x,y-.026),.022,.033,transform=f.transFigure,facecolor=col,edgecolor='none'));text(f,x+.04,y,name,13,INK,va='center');text(f,x+.205,y,f'{value:.2f}亿元',14,INK,'bold',va='center')
    save(f,out,'09_峨眉山收入结构')
    f=sheet('景区相关经营主体，\n与业务分部收入对比','2025年 · 两组业务范围不同',11.5);projectbars(axis(f,[.43,.54,.43,.285],title='经营主体 / 亿元'),'经营主体',fs=13);projectbars(axis(f,[.43,.105,.43,.32],title='业务分部 / 亿元'),'业务分部',fs=13);text(f,.08,.465,'* 乌镇公司含房产销售',11,GRAY);save(f,out,'10_项目与业务收入')
    contact(out,R/'验收/文章图表总览.jpg',3,400,640)
def render_desktop():
    out=R/'图集'
    f=sheet('全国358家5A：江苏、浙江的景区数量领跑','358个实体 · 359条省级属地记录',wide=True);co=mapplot(f,[.015,.17,.60,.62]);maplegend(f,co,x=.075,y=.12,width=.50);province(axis(f,[.65,.10,.30,.74]),fs=12);save(f,out,'01_全国市级热力地图',True)
    f=sheet('认定年份与历史数量','现存名录回溯 · 历史公开节点',wide=True);recognition(axis(f,[.08,.43,.52,.36],title='现存目录认定年'));history(axis(f,[.08,.11,.52,.21],title='历史公开数量节点'));text(f,.70,.68,'2007',26,GOLD);text(f,.70,.58,'首批 66家',24,INK);text(f,.70,.40,'2024',26,GOLD);text(f,.70,.30,'正式认定 21＋19家',22,INK);save(f,out,'02_认定年份与历史数量',True)
    f=sheet('最新一批5A景区','19家 · 2024.12.26正式认定',wide=True);batch(f,[.07,.11,.88,.66],3);save(f,out,'03_最新批次19家',True)
    f=sheet('省级数量与累计占比','359条属地记录',wide=True);pareto(axis(f,[.08,.15,.84,.63]));save(f,out,'04_省市集中度帕累托图',True)
    f=sheet('自然风光占44.4%，历史人文位居第二','358家 · 作者主要体验分类',wide=True);typebars(axis(f,[.075,.16,.85,.62]),fs=17);save(f,out,'05_景区类型分布',True)
    f=sheet('基础票价与收费范围',f'{len(price)}家基础票样本 · 非随机',wide=True);pricedist(axis(f,[.14,.20,.34,.50],title='价格分布'))
    for x,label,val in [(.55,'样本均价',f'{price.adult_peak_regular_yuan.mean():.1f}元'),(.77,'样本中位数',f'{price.adult_peak_regular_yuan.median():g}元')]:text(f,x,.67,val,30,GREEN,'bold');text(f,x,.61,label,13,GRAY)
    text(f,.55,.45,'基础入园',16,INK);text(f,.78,.45,'交通',16,INK);text(f,.55,.36,'九寨沟 190元',19,GREEN);text(f,.78,.36,'观光车 90元',19,GRAY);text(f,.55,.24,'天坛 15元',19,GREEN);text(f,.78,.24,'—',19,GRAY);text(f,.55,.16,'天坛旺季联票 34元',14,INK);save(f,out,'06_门票价格与收费口径',True)
    f=sheet('旅游运营公司财务','12家公司 · 公司合并口径',wide=True);revenue(axis(f,[.15,.14,.31,.64],title='营业收入 / 亿元'),fs=13);profit(axis(f,[.64,.14,.30,.64],title='2025年利润 / 亿元'),fs=13);save(f,out,'07_运营公司营收与利润',True)
    f=sheet('省级景区类型与收入结构','省级属地记录 · 峨眉山A公司口径',wide=True);province_types(axis(f,[.10,.15,.39,.60],title='数量最多的10省级地区 / 家'));composition(f,[.60,.18,.31,.56]);text(f,.64,.76,'峨眉山A · 2025年',16,INK);save(f,out,'08_景观结构与有趣发现',True)
    contact(out,out/'图集总览.png',2,960,596)
def contact(folder,target,columns,width,height):
    paths=sorted(folder.glob('[0-9][0-9]_*.png'));canvas=Image.new('RGB',(columns*width,math.ceil(len(paths)/columns)*height),BG);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14 if width==400 else 24)
    for i,p in enumerate(paths):
        im=ImageOps.contain(Image.open(p).convert('RGB'),(width-20,height-48));x=i%columns*width+(width-im.width)//2;y=i//columns*height;canvas.paste(im,(x,y+5));ImageDraw.Draw(canvas).text((i%columns*width+12,y+height-32),p.stem,font=font,fill=INK)
    target.parent.mkdir(exist_ok=True);canvas.save(target)
def report():
    (R/'验收/图表设计验收.json').write_text(json.dumps({'version':'v1.4.0','style':'白底黑色粗标题；橙青双色；排名编号与数值标签；长解释置于正文','reference_url':'https://mp.weixin.qq.com/s/Vesj127yTU9DmTl7AkfLng','reference_title':'中国竞争最激烈的考试，挤破头也难上岸','reference_author':'网易数读','reference_policy':'参考视觉方法，绘制本篇数据与自有品牌','mobile_figures':10,'desktop_figures':8,'zero_map_color':'#FFFFFF','free_label':'免费','layout':LAYOUT_LOG,'authored_figure_text':TEXT_LOG},ensure_ascii=False,indent=2)+'\n','utf-8')
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');render_article();render_desktop();report()
