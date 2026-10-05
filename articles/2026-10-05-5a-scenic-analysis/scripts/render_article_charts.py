"""从核验CSV绘制适合公众号手机阅读的统计图。"""
from pathlib import Path
import json, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon, Rectangle
from matplotlib.colors import ListedColormap, BoundaryNorm
from pyproj import Transformer
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8')
D = ROOT/'data'; OUT = ROOT/'文章配图'; OUT.mkdir(exist_ok=True)
font = Path('C:/Windows/Fonts/msyh.ttc')
if font.exists(): fontManager.addfont(str(font))
plt.rcParams.update({'font.family': 'Microsoft YaHei' if font.exists() else 'sans-serif',
    'axes.unicode_minus': False, 'font.size': 16, 'axes.edgecolor': '#D5DCCD',
    'xtick.color': '#68786C', 'ytick.color': '#203A35'})
BG='#F5F1E7'; GREEN='#246954'; DARK='#173831'; GRAY='#6B796E'; GOLD='#B08E4B'; RED='#B65139'
prov=pd.read_csv(D/'省级数量.csv'); city=pd.read_csv(D/'市级数量.csv')
years=pd.read_csv(D/'现存名录认定年分布.csv'); hist=pd.read_csv(D/'历史公开数量节点.csv')
latest=pd.read_csv(D/'最新认定批次.csv'); types=pd.read_csv(D/'景区类型数量.csv')
price=pd.read_csv(D/'门票核验样本.csv'); fin=pd.read_csv(D/'上市运营公司财务样本.csv')
seg=pd.read_csv(D/'峨眉山收入构成.csv')

def sheet(title, subtitle, height=7):
    f=plt.figure(figsize=(6,height), facecolor=BG)
    f.text(.07, 1-.27/height, '5A景区 · 数据图鉴', fontsize=14, color=GREEN, weight='bold', va='top')
    f.text(.07, 1-.65/height, title, fontsize=23, color=DARK, weight='bold', va='top')
    f.text(.07, 1-1.15/height, subtitle, fontsize=13, color=GRAY, va='top', linespacing=1.7)
    f.text(.07,.32/height,'可以叫我才哥  ·  数据核对 2026.10.05',fontsize=12,color=GRAY)
    return f

def axis(f, rect):
    a=f.add_axes(rect,facecolor=BG)
    for s in ['top','right','left']: a.spines[s].set_visible(False)
    a.tick_params(length=0, labelsize=12)
    a.grid(axis='x',color='#D9DFD0',lw=.6); a.set_axisbelow(True)
    return a

def save(f, name):
    f.savefig(OUT/(name+'.png'),dpi=200); plt.close(f)
    print('SAVED',name)

def bars(a, labels, values, xmax, color=GREEN, fs=16, fmt=lambda v:f'{v:g}'):
    y=np.arange(len(values)); a.barh(y,values,color=color,height=.62)
    a.set_yticks(y,labels,fontsize=fs); a.invert_yaxis(); a.set_xlim(0,xmax)
    for yy,v in zip(y,values): a.text(v+xmax*.025,yy,fmt(v),va='center',fontsize=fs,color=DARK)

def polygons(geo):
    return [geo['coordinates']] if geo['type']=='Polygon' else geo.get('coordinates',[]) if geo['type']=='MultiPolygon' else []

proj=Transformer.from_crs('EPSG:4326','+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +datum=WGS84 +units=m',always_xy=True)
def patches(geo, projected=True, main=False):
    out=[]
    for p in polygons(geo):
        r=np.asarray(p[0])
        if main and r[:,1].max()<18: continue
        x,y=proj.transform(r[:,0],r[:,1]) if projected else (r[:,0],r[:,1])
        out.append(Polygon(np.c_[x,y],closed=True))
    return out

f=sheet('全国358家，分布在哪里？','市级统计示意 · 220个单位有5A',6.3)
a=f.add_axes([.025,.19,.95,.54],facecolor=BG);a.set_axis_off();a.set_aspect('equal')
colors=['#FFFFFF','#D3E2C5','#A3C39A','#6A9D7D','#37775B','#174F3C']
cmap=ListedColormap(colors);norm=BoundaryNorm([-.5,.5,1.5,3.5,5.5,8.5,20],6)
features=json.loads((D/'city_features.json').read_text('utf-8'))['features']
country=json.loads((D/'sources/china_national.json').read_text('utf-8'))['features']
boundaries=json.loads((D/'sources/china_boundaries.json').read_text('utf-8'))['features']
counts=city.set_index('city_code')['count'].to_dict()
for ft in features:
    a.add_collection(PatchCollection(patches(ft['geometry'],main=True),facecolor=cmap(norm(counts.get(int(ft['properties']['adcode']),0))),edgecolor=BG,lw=.24))
for ft in boundaries:
    code=ft['properties']['adcode']
    if isinstance(code,int):
        a.add_collection(PatchCollection(patches(ft['geometry'],main=True),facecolor='#DFE0D2' if code in [710000,810000,820000] else 'none',edgecolor=GRAY,lw=.3))
for ft in country: a.add_collection(PatchCollection(patches(ft['geometry'],main=True),facecolor='none',edgecolor=GRAY,lw=.5))
a.set_xlim(-2900000,2400000);a.set_ylim(1600000,6050000)
for code,label,off in [(500000,'重庆12',(-32,-10)),(110000,'北京9',(10,12)),(320500,'苏州6',(12,-12))]:
    ft=next(ft for ft in features if int(ft['properties']['adcode'])==code)
    x,y=proj.transform(*(ft['properties'].get('centroid') or ft['properties']['center']))
    a.annotate(label,(x,y),xytext=off,textcoords='offset points',fontsize=12,color=DARK,bbox=dict(fc=BG,ec='none',alpha=.85,pad=1.5),arrowprops=dict(arrowstyle='-',color=GRAY,lw=.6))
x,y=proj.transform(121,23.5);a.text(x,y,'台湾',fontsize=10,color=GRAY)
ins=f.add_axes([.83,.18,.11,.2],facecolor=BG)
for ft in country: ins.add_collection(PatchCollection(patches(ft['geometry'],False),facecolor='#D3E2C5',edgecolor=GRAY,lw=.4))
for ft in boundaries:
    if ft['properties']['adcode']=='100000_JD': ins.add_collection(PatchCollection(patches(ft['geometry'],False),facecolor=GRAY,edgecolor='none'))
ins.set_xlim(106,124);ins.set_ylim(2,24);ins.set_aspect('equal');ins.set_xticks([]);ins.set_yticks([]);ins.set_title('南海诸岛',fontsize=9,pad=3)
for i,(co,lab) in enumerate(zip(colors,['0','1','2–3','4–5','6–8','9+'])):
    x=.08+i*.142;f.add_artist(Rectangle((x,.137),.048,.02,transform=f.transFigure,facecolor=co));f.text(x+.058,.138,lab,fontsize=11,color=DARK)
f.text(.07,.092,'来源：文旅部名录；DataV行政区划边界',fontsize=11,color=GRAY)
save(f,'01_全国市级分布')

f=sheet('江苏26家，浙江22家','省级属地记录359条 · 全国实体358家',12.1)
a=axis(f,[.17,.08,.70,.78]); bars(a,prov.province.tolist(),prov['count'].tolist(),32,color=[GREEN if i<2 else '#83A18C' for i in range(31)],fs=15)
a.set_xticks([0,10,20,30]);a.set_xlabel('5A数量 / 家',fontsize=13)
save(f,'02_各省级地区数量')

f=sheet('达到80%，需要20个省级地区','按省级数量降序 · 分母359条属地记录',6.1)
a=axis(f,[.12,.20,.75,.49]);a.grid(False);x=np.arange(1,32);v=prov['count'].to_numpy();cum=np.cumsum(v)/v.sum()*100
a.bar(x,v,color='#86A58C',width=.73);a.set_xlim(.2,31.8);a.set_ylim(0,32);a.set_xticks([1,5,10,15,20,25,31]);a.set_xlabel('省级数量排名',fontsize=14);a.set_ylabel('数量 / 家',fontsize=13)
b=a.twinx();b.plot(x,cum,color=GOLD,lw=2.6);b.set_ylim(0,110);b.set_yticks([0,20,40,60,80,100],['0%','20%','40%','60%','80%','100%'],fontsize=12)
b.axhline(80,color=GRAY,ls='--',lw=.8);b.scatter([5,20],[cum[4],cum[19]],color=RED,s=30)
b.annotate('前5位 28.1%',(5,cum[4]),xytext=(10,5),textcoords='offset points',fontsize=13,color=DARK)
b.annotate('第20位跨过80%',(20,cum[19]),xytext=(-42,20),textcoords='offset points',fontsize=13,color=RED)
for s in ['top','left','right']:b.spines[s].set_visible(False)
f.text(.07,.095,'柱：省级数量   线：累计占比',fontsize=12,color=GRAY);save(f,'03_省级集中度')

f=sheet('首批66家，到当前358家','现存认定年分布，与历史数量分开看',9)
a=axis(f,[.13,.53,.71,.26]);a.grid(False);xx=years.directory_first_year;yy=years.existing_count
a.bar(xx,yy,color=GREEN,width=.7);a.set_ylim(0,76);a.set_ylabel('现存家数',fontsize=12)
a.set_xticks([2007,2011,2015,2019,2024])
a.set_title('现存名录按目录年份分组',fontsize=16,loc='left',color=DARK,pad=15)
for x,y in zip(xx,yy):
    if y>=25:a.text(x,y+2,str(y),ha='center',fontsize=11,color=DARK)
b=a.twinx();b.plot(xx,years.retrospective_cumulative_existing,color=GOLD,lw=2);b.set_ylim(0,400);b.set_yticks([0,200,400]);b.tick_params(labelsize=11);b.set_ylabel('回溯累计',fontsize=12,color=GOLD)
for s in ['top','left','right']:b.spines[s].set_visible(False)
f.text(.13,.46,'柱：现存家数   线：现存名单回溯累计\n回溯累计不等于当年年末总量',fontsize=12,color=GRAY,linespacing=1.8)
a=axis(f,[.13,.15,.76,.23]);a.grid(False);h=hist[hist.year!=2007];a.scatter(h.year,h['count'],s=85,color=GREEN)
a.set_ylim(0,410);a.set_xticks(h.year);a.tick_params(axis='x',labelrotation=40);a.set_ylabel('公开数量 / 家',fontsize=12);a.set_title('有明确来源的历史数量节点',fontsize=16,loc='left',pad=15,color=DARK)
for _,r in h.iterrows():
    dx=-8 if r.year==2018 else 8 if r.year==2019 else 0
    a.annotate(str(r['count']),(r.year,r['count']),xytext=(dx,12),textcoords='offset points',fontsize=14,color=DARK,ha='right' if r.year==2018 else 'left' if r.year==2019 else 'center',weight='bold')
f.text(.13,.075,'2007年首批认定66家，非年末存量。',fontsize=12,color=GRAY);save(f,'04_认定年份与历史节点')

short={24:'衡水湖',35:'晋祠天龙山',44:'老牛湾黄河大峡谷',60:'大安嫩江湾',67:'扎龙',120:'金华双龙',145:'冠豸山',160:'篁岭',176:'周村古商城',193:'宝泉',209:'麻城龟峰山',237:'万绿湖',247:'花山岩画',284:'成都天台山',294:'万峰林',323:'乾陵',331:'冶力关',341:'六盘山红军长征',357:'天山托木尔'}
f=sheet('最近一批：19家新晋5A','正式认定公告成文：2024.12.26',10)
for i,r in latest.reset_index(drop=True).iterrows():
    y=.825-i*.0375
    f.text(.08,y,f'{i+1:02d}',fontsize=14,color=GOLD,va='center')
    f.text(.17,y,r.province,fontsize=15,color=GRAY,va='center')
    f.text(.32,y,short[int(r.atlas_id)],fontsize=16,color=DARK,va='center',weight='bold')
    f.add_artist(plt.Line2D([.08,.92],[y-.018,y-.018],transform=f.transFigure,color='#DFE2D5',lw=.6))
f.text(.08,.07,'采用常用简称 · 完整名称见配套数据',fontsize=12,color=GRAY);save(f,'05_最新批次名单')

f=sheet('自然风光159家，占44.4%','作者按主要体验分类 · 非官方分类',6.4)
a=axis(f,[.25,.18,.59,.54]);bars(a,types.category.tolist(),types['count'].tolist(),220,fs=16,fmt=lambda v:f'{v:g}')
a.set_xticks([0,50,100,150])
f.text(.07,.10,'每家景区只归入1个主类别，共358家。',fontsize=12,color=GRAY);save(f,'06_景区类型')

ev=json.loads((D/'evidence_summary.json').read_text('utf-8'))
freq=[int((price.adult_peak_regular_yuan==0).sum())]+[int(((price.adult_peak_regular_yuan>lo)&(price.adult_peak_regular_yuan<=hi)).sum()) for lo,hi in [(0,50),(50,100),(100,150),(150,200)]]
f=sheet(f'{len(price)}家基础票，怎样分布？',f"票种资料覆盖{ev['price_entity_covered_n']}家 · {ev['price_product_n']}个产品",9)
f.text(.08,.795,f'样本均价 {price.adult_peak_regular_yuan.mean():.1f}元   中位数 {price.adult_peak_regular_yuan.median():g}元',fontsize=16,color=GREEN,weight='bold')
a=axis(f,[.28,.49,.55,.25]);bars(a,['免费','1–50元','51–100元','101–150元','151–200元'],freq,max(freq)+5,fs=15,fmt=lambda v:f'{v:g}家')
a.set_xticks([])
f.text(.08,.405,'基础入园免费',fontsize=18,color=GREEN,weight='bold')
f.text(.08,.38,'南浔、大小洞天、天涯海角、\n岳麓山·橘子洲、花明楼、东湖公共景区',fontsize=14,color=DARK,linespacing=1.9,va='top')
f.text(.08,.235,'便宜的入园票，可能只覆盖一部分体验',fontsize=15,color=DARK,weight='bold')
f.text(.08,.21,'青岩大门票10元、参观套票60元；\n天坛入园15元、旺季联票34元。',fontsize=13,color=GRAY,linespacing=1.8,va='top')
f.text(.08,.115,'55家为来源公布的基础票标准，非全国均价。\n子景点、含车船套票与临时活动分开记录。',fontsize=11,color=GRAY,linespacing=1.8,va='top')
save(f,'07_门票样本')

companies=fin[(fin.year==2025)&(fin.comparison_group=='旅游运营公司')].sort_values('revenue_yi',ascending=False).company.tolist()
f=sheet('14家公司，三年的经营账本','图中比较12家旅游运营公司 · 集团另列',14.5)
a=axis(f,[.26,.54,.60,.32]);y=np.arange(len(companies))
for j,(year,col) in enumerate(zip([2023,2024,2025],['#C8D9B9','#8BAC90',GREEN])):
    v=fin[fin.year==year].set_index('company').loc[companies,'revenue_yi'].to_numpy()
    a.barh(y+(j-1)*.23,v,height=.20,color=col,label=str(year))
    if year==2025:
        for i,val in enumerate(v):a.text(val+.25,y[i]+.23,f'{val:.2f}',fontsize=11,color=DARK,va='center')
a.set_yticks(y,companies,fontsize=13);a.invert_yaxis();a.set_xlim(0,26);a.set_xticks([0,10,20]);a.set_title('营业收入 / 亿元',loc='left',fontsize=16,pad=15,color=DARK);a.legend(loc='lower right',fontsize=10,frameon=False,ncol=3)
a=axis(f,[.26,.18,.60,.28]);a.axvline(0,color=GRAY,lw=.7);f25=fin[fin.year==2025].set_index('company').loc[companies]
for j,(key,col,label) in enumerate([('net_profit_yi',GREEN,'归母净利润'),('adjusted_net_profit_yi',GOLD,'扣非归母净利润')]):
    v=f25[key].to_numpy();a.barh(y+(j-.5)*.29,v,height=.24,color=col,label=label)
    for i,val in enumerate(v):a.text(val+.09 if val>=0 else val-.09,y[i]+(j-.5)*.29,f'{val:.2f}',va='center',ha='left' if val>=0 else 'right',fontsize=10,color=DARK)
a.set_yticks(y,companies,fontsize=13);a.invert_yaxis();a.set_xlim(-7,4.6);a.set_xticks([-6,-3,0,3]);a.set_title('2025年利润 / 亿元',loc='left',fontsize=16,pad=15,color=DARK);a.legend(loc='lower left',fontsize=9,frameon=False)
f.text(.08,.12,'多元集团2025年合并营收：\n中青旅113.37亿元；华侨城A313.81亿元',fontsize=14,color=DARK,linespacing=1.8)
f.text(.08,.065,'集团含旅行社、地产等；上述数字均非5A全区收入。\n各公司范围不同，详见CSV；三特审计带强调事项段。',fontsize=11,color=GRAY,linespacing=1.8)
save(f,'08_运营公司财务')


f=sheet('索道收入，高于游山门票','峨眉山A · 2025年公司营业收入构成',5.8)
a=axis(f,[.29,.30,.57,.36]);labels=['索道','游山门票','酒店','其他业务'];values=seg.revenue_wan.to_numpy()/10000
bars(a,labels,values,5.4,color=[GREEN,'#89A98C',GOLD,'#B7C2AE'],fs=16,fmt=lambda v:f'{v:.2f}')
a.set_xticks([0,1,2,3,4]);a.set_xlabel('营业收入 / 亿元',fontsize=13)
f.text(.07,.15,'索道占41.8%   游山门票占27.0%',fontsize=16,color=GREEN,weight='bold')
f.text(.07,.09,'游山门票采用公司年报收入确认口径。',fontsize=11,color=GRAY);save(f,'09_峨眉山收入结构')

projects=pd.read_csv(D/'景区相关项目与业务收入.csv')
f=sheet('把收入进一步拆到经营项目','2025年 · 5项经营主体与8项业务分部',12.8)
for kind,rect,title in [('经营主体',[.40,.56,.43,.25],'经营主体收入 / 亿元'),('业务分部',[.40,.15,.43,.27],'业务分部收入 / 亿元')]:
    p=projects[projects.scope_type==kind].sort_values('revenue_yi',ascending=False)
    a=axis(f,rect);bars(a,p.project.tolist(),p.revenue_yi.tolist(),p.revenue_yi.max()*1.25,fs=12,fmt=lambda v:f'{v:.2f}')
    a.set_title(title,loc='left',fontsize=16,pad=18,color=DARK);a.set_xticks([0,5,10,15] if kind=='经营主体' else [0,1,2,3,4])
f.text(.07,.505,'乌镇公司含房产去化，非纯门票收入。\n索道等经营主体也不代表所在5A全区收入。',fontsize=12,color=GRAY,linespacing=1.8,va='top')
f.text(.07,.078,'两组范围不同，含上下级项目；不能加总或视作全国排行。',fontsize=11,color=GRAY)
save(f,'10_项目与业务收入')

# 用于逐张验收的缩略总览，不插入正文。


thumbs=[]
for p in sorted(OUT.glob('[0-9][0-9]_*.png')):
    im=Image.open(p).convert('RGB');tile=Image.new('RGB',(400,680),BG)
    th=ImageOps.contain(im,(390,635));tile.paste(th,((400-th.width)//2,15))
    ImageDraw.Draw(tile).text((15,653),p.stem,fill=DARK)
    thumbs.append(tile)
canvas=Image.new('RGB',(1200,680*((len(thumbs)+2)//3)),BG)
for i,t in enumerate(thumbs):canvas.paste(t,((i%3)*400,(i//3)*680))
check=ROOT/'验收';check.mkdir(exist_ok=True);canvas.save(check/'文章图表总览.jpg',quality=92)
