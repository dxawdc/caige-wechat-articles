from pathlib import Path
import json,sys,math
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
from matplotlib.patches import Polygon,Rectangle
from matplotlib.collections import PatchCollection
from matplotlib.colors import ListedColormap,BoundaryNorm
from pyproj import Transformer
from PIL import Image,ImageOps,ImageDraw,ImageFont
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1];D=R/'data';O=R/'图集';O.mkdir(exist_ok=True)
fontManager.addfont('C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':'Microsoft YaHei','axes.unicode_minus':False,'font.size':11,'axes.labelcolor':'#132A32','xtick.color':'#54665F','ytick.color':'#54665F','axes.edgecolor':'#D1D6CB','savefig.facecolor':'#F5F1E7'})
BG='#F5F1E7';NAVY='#132A32';GREEN='#236954';RED='#B34F33';GOLD='#B6975E';MUTED='#647169';GRID='#D9DDD2'
CATCOL={'自然风光':GREEN,'历史人文':'#486A8C','宗教文化':GOLD,'红色纪念':RED,'古城古镇':'#719889','主题休闲':'#998AB1','综合景观':'#A8AC94'}
master=pd.read_csv(D/'全国5A景区主表.csv',dtype={'atlas_id':str});prov=pd.read_csv(D/'省级数量.csv');city=pd.read_csv(D/'市级数量.csv');assoc=pd.read_csv(D/'市级属地关系.csv');years=pd.read_csv(D/'现存名录认定年分布.csv');latest=pd.read_csv(D/'最新认定批次.csv',dtype={'atlas_id':str});historic=pd.read_csv(D/'历史公开数量节点.csv');price=pd.read_csv(D/'门票核验样本.csv');fin=pd.read_csv(D/'上市运营公司财务样本.csv');seg=pd.read_csv(D/'峨眉山收入构成.csv')
summary=json.loads((D/'summary.json').read_text('utf-8'))
proj=Transformer.from_crs('EPSG:4326','+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +datum=WGS84 +units=m +no_defs',always_xy=True)
features=json.loads((D/'city_features.json').read_text('utf-8'))['features']
country=json.loads((D/'sources/china_national.json').read_text('utf-8'))
province_shapes=json.loads((D/'sources/china_boundaries.json').read_text('utf-8'))['features']
def sheet(num,title,subtitle):
 f=plt.figure(figsize=(16,9),facecolor=BG)
 f.text(.04,.948,'中国5A景区 · 数据图鉴',fontsize=12,color=GREEN,weight='bold')
 f.text(.96,.948,f'{num:02d} / 08     2026.10.05',fontsize=10,color=MUTED,ha='right')
 f.text(.04,.873,title,fontsize=29,color=NAVY,weight='bold')
 f.text(.04,.831,subtitle,fontsize=11,color=MUTED)
 f.add_artist(plt.Line2D([.04,.96],[.811,.811],transform=f.transFigure,color=GRID,lw=1))
 return f
def ax(f,rect,title=None):
 a=f.add_axes(rect,facecolor=BG)
 for s in ['top','right','left']:a.spines[s].set_visible(False)
 a.tick_params(length=0,pad=5)
 a.grid(axis='x',color=GRID,lw=.6);a.set_axisbelow(True)
 if title:a.set_title(title,fontsize=13,color=NAVY,loc='left',pad=14,weight='bold')
 return a
def text(f,x,y,t,size=11,color=NAVY,weight=None,**kw):return f.text(x,y,t,fontsize=size,color=color,weight=weight,**kw)
def footer(f,lines):
 for i,l in enumerate(lines):text(f,.04,.064-i*.019,l,7.5,MUTED)
def save(f,name):
 f.savefig(O/f'{name}.png',dpi=240);plt.close(f);print('SAVED',name)
def kpi(f,x,y,value,label,detail=None):
 text(f,x,y,value,29,GREEN,'bold');text(f,x,y-.038,label,11)
 if detail:text(f,x,y-.068,detail,8.5,MUTED)
def polys(geo):
 if geo['type']=='Polygon':return [geo['coordinates']]
 if geo['type']=='MultiPolygon':return geo['coordinates']
 return []
def patches(geo,projected=True,main_only=False):
 out=[]
 for polygon in polys(geo):
  r=np.asarray(polygon[0])
  if main_only and r[:,1].max()<18:continue
  xx,yy=proj.transform(r[:,0],r[:,1]) if projected else (r[:,0],r[:,1]);out.append(Polygon(np.c_[xx,yy],closed=True))
 return out
def mapplot(f,rect,counts=None,label=True):
 a=f.add_axes(rect,facecolor=BG);a.set_axis_off();a.set_aspect('equal')
 colors=['#FFFFFF','#D9E4CC','#A7C3A0','#6D9E84','#397960','#18513E'];cmap=ListedColormap(colors);norm=BoundaryNorm([-.5,.5,1.5,3.5,5.5,8.5,20],6)
 counts=counts if counts is not None else city.set_index('city_code')['count'].to_dict()
 for feat in features:
  code=int(feat['properties']['adcode']);a.add_collection(PatchCollection(patches(feat['geometry'],main_only=True),facecolor=cmap(norm(counts.get(code,0))),edgecolor=BG,linewidth=.20,zorder=2))
 for feat in province_shapes:
  code=feat['properties']['adcode']
  if code in [710000,810000,820000]:a.add_collection(PatchCollection(patches(feat['geometry'],main_only=True),facecolor='#E2DFD3',edgecolor=MUTED,linewidth=.35,zorder=2))
  elif isinstance(code,int):a.add_collection(PatchCollection(patches(feat['geometry'],main_only=True),facecolor='none',edgecolor='#647965',linewidth=.28,zorder=3))
 for feat in country['features']:a.add_collection(PatchCollection(patches(feat['geometry'],main_only=True),facecolor='none',edgecolor='#62796A',linewidth=.4,zorder=3))
 a.set_xlim(-2900000,2400000);a.set_ylim(1600000,6050000)
 if label:
  for code,name in [(500000,'重庆 12'),(110000,'北京 9'),(320500,'苏州 6')]:
   ft=next(v for v in features if int(v['properties']['adcode'])==code);c=ft['properties'].get('centroid') or ft['properties']['center'];px,py=proj.transform(*c);a.annotate(name,(px,py),xytext=(10,10),textcoords='offset points',fontsize=9,weight='bold',color=NAVY,bbox=dict(fc=BG,ec='none',alpha=.85,pad=2))
  px,py=proj.transform(121,23.5);a.text(px,py,'台湾',fontsize=8,color=MUTED)
 # 南海诸岛附图使用同一国界源，保持岛屿与断续线的真实几何。
 inset=f.add_axes([rect[0]+rect[2]*.82,rect[1]+.002,rect[2]*.16,rect[3]*.25],facecolor=BG)
 for ft in country['features']:inset.add_collection(PatchCollection(patches(ft['geometry'],False),facecolor='#DFE8D6',edgecolor='#657768',lw=.5))
 for ft in province_shapes:
  if ft['properties']['adcode']=='100000_JD':inset.add_collection(PatchCollection(patches(ft['geometry'],False),facecolor='#657768',edgecolor='none'))
 inset.set_xlim(106,124);inset.set_ylim(2,24);inset.set_aspect('equal');inset.set_xticks([]);inset.set_yticks([])
 inset.set_title('南海诸岛',fontsize=7,pad=3)
 for s in inset.spines.values():s.set_color(GRID)
 return a,colors
def barh(a,labels,values,colors=GREEN,xmax=None,fs=10,unit=''):
 y=np.arange(len(labels));a.barh(y,values,color=colors,height=.68);a.set_yticks(y,labels,fontsize=fs);a.invert_yaxis();a.set_xlim(0,xmax or max(values)*1.16)
 for yy,v in zip(y,values):a.text(v+max(values)*.02,yy,f'{v:g}{unit}',va='center',fontsize=fs,color=NAVY)

# 01 全国市级热力图与全部31省份排名。
f=sheet(1,'全国358家5A景区，落在哪里？','市级分布着色地图 × 31省级地区数量排名｜跨区域景区按属地分别计入，全国实体去重')
kpi(f,.055,.739,'358','独立景区', '文旅部当前服务页 / 去重名录')
kpi(f,.26,.739,'31','省级地区', '新疆含兵团2家')
kpi(f,.45,.739,str(summary['cities_with_5a']),'有5A的地图统计单位','含地市、州、盟及省直辖县级单位')
a,colors=mapplot(f,[.015,.135,.63,.535]);text(f,.058,.135,'5A数量',9,MUTED)
for i,(co,lab) in enumerate(zip(colors,['0','1','2–3','4–5','6–8','9及以上'])):
 f.add_artist(Rectangle((.115+i*.07,.13),.025,.015,transform=f.transFigure,facecolor=co,edgecolor='none'));text(f,.144+i*.07,.132,lab,8)
a=ax(f,[.727,.13,.217,.625],'各省级地区 / 家');barh(a,prov.province.tolist(),prov['count'].tolist(),[GREEN if i<2 else '#7C9F87' for i in range(31)],30,fs=8)
footer(f,['来源：文旅部数据服务名录、旅游服务地图；市级边界：DataV行政区划。数据读取：2026-10-05；地图为统计示意。',f'口径：省级归属359条，壶口瀑布跨陕晋；市级归属{len(assoc)}条，阿尔山—柴河/福建土楼/沂蒙山等跨市分别计入；直辖市整体统计。'])
save(f,'01_全国市级热力地图')

# 02 现存认定年分布，不能推作历史行政增减。
f=sheet(2,'从首批66家，到当前358家','认定年分布与历史数量分开看：现存名录有摘牌、恢复、目录年份差异，回溯累计不等于历史年末存量')
a=ax(f,[.075,.42,.55,.30],'现存名录按目录认定年分布 / 家');a.grid(False);xx=years.directory_first_year;yy=years.existing_count
a.bar(xx,yy,color=[RED if y==2024 else GREEN for y in xx],width=.66);a.set_xticks(xx,[str(y)[2:] for y in xx],fontsize=9);a.set_ylim(0,77);a.set_ylabel('现存景区数量',fontsize=9);a.set_xlabel('目录认定年份（20xx）',fontsize=9)
for x,y in zip(xx,yy):
 if y:a.text(x,y+1.5,str(y),ha='center',fontsize=8)
b=a.twinx();b.plot(xx,years.retrospective_cumulative_existing,color=GOLD,lw=2,marker='.',ms=4);b.set_ylim(0,400);b.tick_params(labelsize=8,colors=GOLD);b.set_ylabel('现存名录回溯累计',fontsize=8,color=GOLD)
for s in b.spines.values():s.set_visible(False)
text(f,.073,.354,'历史公开数量节点 / 仅展示有来源的节点',13,NAVY,'bold')
h=historic[historic.year!=2007];a=ax(f,[.075,.135,.55,.165]);a.grid(False)
a.scatter(h.year,h['count'],s=45,color=GREEN);a.set_ylim(0,410);a.set_xticks(h.year);a.set_ylabel('公开存量 / 家',fontsize=9)
for _,r in h.iterrows():a.text(r.year,r['count']+13,str(r['count']),ha='center',fontsize=10,weight='bold')
text(f,.685,.721,'2007 · 首批66家',21,GREEN,'bold');text(f,.685,.665,'故宫、黄山、西湖、九寨沟等\n开启国家5A级景区评定。',12,linespacing=1.8)
text(f,.685,.557,'目录2007年景区现存65家',12,NAVY,'bold');text(f,.685,.505,'目录中山海关标有恢复年份；\n年度统计取首次目录年份。',10,MUTED,linespacing=1.8)
text(f,.685,.374,'2024 · 两次正式新认定',20,RED,'bold');text(f,.685,.302,'2月：21家\n12月：19家',17,linespacing=1.6)
text(f,.685,.189,'最新一批：2024-12-26公告\n19家名单见第03页。',11,MUTED,linespacing=1.6)
footer(f,['来源：文旅部名录及2024年2月、12月认定公告；历史数量节点来源见数据表。首批66家由中国旅游报回顾确认。','读图：柱为“目前仍在名录中的认定年数量”，金线为其回溯累计；未补造历年摘牌/恢复事件，因此不作为历年净新增或年末库存。'])
save(f,'02_认定年份与历史数量')

# 03 单列最新正式批次地图与19个条目。
f=sheet(3,'最新一批：19个新晋5A景区','文化和旅游部公告 · 文旅资源发〔2024〕100号｜成文2024-12-26，发布2024-12-27；截至本次核对为最近一批')
ct={k:int(v)*3 for k,v in latest.groupby('city_code').size().items()};mapplot(f,[.015,.215,.48,.535],ct,label=False)
text(f,.06,.723,'19家',26,RED,'bold');text(f,.06,.676,'覆盖19个省级地区',13)
text(f,.06,.16,'绿色为本批入选地市\n景区实体名单以正式认定公告为准。',10,MUTED,linespacing=1.8)
short={24:'衡水湖',35:'晋祠天龙山',44:'老牛湾黄河大峡谷',60:'大安嫩江湾',67:'扎龙生态旅游区',120:'双龙风景旅游区',176:'周村古商城',160:'篁岭',193:'宝泉',209:'麻城龟峰山',237:'万绿湖',145:'冠豸山',247:'花山岩画',284:'成都天台山',294:'万峰林',323:'乾陵',331:'冶力关',341:'六盘山红军长征',357:'天山托木尔'}
latest=latest.copy();latest['short_name']=latest.atlas_id.map(lambda a:short[int(a)])
for i,(_,r) in enumerate(latest.iterrows()):
 col=i//10;row=i%10;x=.52+col*.235;y=.744-row*.061
 text(f,x,y,f'{i+1:02d}',9,RED,'bold');text(f,x+.027,y,r.short_name,12,NAVY,'bold');text(f,x+.027,y-.025,f'{r.province} · {r.city}',8.5,MUTED)
footer(f,['来源：中国政府网/文化和旅游部《文化和旅游部关于确定19家旅游景区为国家5A级旅游景区的公告》。','本页采用景区常用简称，完整认定名称、目录名称及公告链接保存在“最新认定批次”数据表；目录年分布另见第02页。'])
save(f,'03_最新批次19家')

# 04 帕累托：正确用于地域集中度，而非时间顺序。
f=sheet(4,'5A景区，集中在少数省市吗？','数量从高到低排序 × 累计占比｜省级归属359条、市级归属362条，分别使用各自分母')
x=np.arange(len(prov));cum=prov['count'].cumsum()/359*100;k80=int(np.searchsorted(cum,80))+1
kpi(f,.07,.741,f'{k80} / 31','达到80%归属量所需省级地区');kpi(f,.38,.741,f'{prov.head(5)["count"].sum()/359:.1%}','前5省级地区占比');kpi(f,.70,.741,'48家','江苏＋浙江',f'占358个独立景区的{48/358:.1%}')
a=ax(f,[.07,.335,.87,.30],'省级数量帕累托图');a.grid(False);a.bar(x,prov['count'],color=[GREEN if i<k80 else '#C3CAB6' for i in x],width=.7)
a.set_xticks(x,prov.province.tolist(),rotation=45,ha='right',fontsize=9);a.set_ylim(0,32);a.set_ylabel('归属数量 / 家',fontsize=9)
for i,c in enumerate(prov['count']):a.text(i,c+.55,str(c),ha='center',fontsize=8)
b=a.twinx();b.plot(x,cum,color=RED,marker='.',lw=2);b.axhline(80,color=RED,lw=.8,ls='--',alpha=.6);b.set_ylim(0,110);b.set_yticks([0,20,40,60,80,100],['0%','20%','40%','60%','80%','100%']);b.tick_params(colors=RED,labelsize=9)
for s in b.spines.values():s.set_visible(False)
text(f,.07,.208,'地市排名 / 直辖市单列',13,NAVY,'bold')
top=city[~city.city_code.isin([110000,120000,310000,500000])].head(6)
for i,(_,r) in enumerate(top.iterrows()):
 xx=.075+i*.143;text(f,xx,.148,r.city,12);text(f,xx+.07,.148,str(r['count']),19,GREEN,'bold')
text(f,.07,.108,'直辖市：重庆12 · 北京9 · 上海5 · 天津2；辖域大小不同，排名不等同旅游吸引力。',9,MUTED)
footer(f,['来源：文旅部名录/地图字段及跨区域人工核对；新疆含兵团。帕累托图按归属数量计算，跨省壶口在两省各计1次。','解释：这里衡量优质景区的空间供给集中度；不能直接推断客流、旅游收入或居民旅游便利度。'])
save(f,'04_省市集中度帕累托图')

# 05 完整358作者分类。
f=sheet(5,'看山水，也看历史与生活','358个景区的主导景观类型｜作者研究分类：每个景区归入一种主类型，实际体验可以兼具多类')
cats=master.category.value_counts();a=ax(f,[.15,.35,.40,.365],'全国类型分布 / 家');barh(a,cats.index.tolist(),cats.values.tolist(),[CATCOL[c] for c in cats.index],190,fs=12)
for i,(c,v) in enumerate(cats.items()):text(f,.572,.682-i*.046,f'{v/358:.1%}',12,CATCOL[c],'bold')
examples={'自然风光':'黄山 · 九寨沟 · 稻城亚丁','历史人文':'故宫 · 龙门石窟 · 秦始皇帝陵','综合景观':'青城山—都江堰 · 三峡大坝—屈原故里','古城古镇':'周庄 · 乌镇 · 南浔古镇','宗教文化':'五台山 · 九华山 · 峨眉山','主题休闲':'长隆 · 环球恐龙城 · 清明上河园','红色纪念':'井冈山 · 韶山 · 西柏坡'}
for i,c in enumerate(cats.index):
 y=.708-i*.078;text(f,.686,y,c,12,CATCOL[c],'bold');text(f,.686,y-.028,examples[c],8.5,MUTED)
text(f,.15,.237,'分类规则',13,NAVY,'bold');text(f,.15,.177,'自然以主要山水地貌为主；历史看文物与古迹；宗教看寺观文化；红色看纪念叙事。\n古城古镇、现代主题设施独立归类；多主题联合挂牌景区归为综合景观。',11,MUTED,linespacing=1.8)
footer(f,['来源：文旅部景区名称和简介；全部358家单标签人工研究分类。主表保留原始简介与分类字段，方便按不同分类法复算。','这是作者分析口径，非文旅部官方类型认定；如把寺观、古镇、红色等合并为广义人文，分布会随分类框架变化。'])
save(f,'05_景区类型分布')

# 06 价格产品范围与基础票分布。
ev=json.loads((D/'evidence_summary.json').read_text('utf-8'))
f=sheet(6,'门票多少钱？先分清买的是什么',f"覆盖{ev['price_entity_covered_n']}家、{ev['price_product_n']}个产品｜其中{len(price)}家基础票可计算；子景点、含交通票及活动分别记录")
kpi(f,.07,.737,f"{ev['price_entity_covered_n']}家",'有票种核验资料',f"全国实体覆盖{ev['price_entity_coverage_pct']:.1f}%")
kpi(f,.32,.737,f'{price.adult_peak_regular_yuan.mean():.1f}元','基础票样本均价','非随机样本；各来源公布标准')
kpi(f,.57,.737,f'{price.adult_peak_regular_yuan.median():g}元','基础票样本中位数','来源时间不同，非同日实时售价')
kpi(f,.81,.737,f"{ev['free_sample_n']}家",'基础入园免费','付费展馆等另计')
freq=[int((price.adult_peak_regular_yuan==0).sum())]+[int(((price.adult_peak_regular_yuan>lo)&(price.adult_peak_regular_yuan<=hi)).sum()) for lo,hi in [(0,50),(50,100),(100,150),(150,200)]]
a=ax(f,[.15,.23,.36,.35],'55家基础票标准分布 / 家');barh(a,['免费','1–50元','51–100元','101–150元','151–200元'],freq,xmax=max(freq)+4,fs=13)
text(f,.59,.575,'免费基础入园',18,GREEN,'bold');text(f,.59,.525,'南浔、大小洞天、天涯海角、岳麓山·橘子洲、\n花明楼、东湖公共景区；可选项目收费另看。',11,linespacing=1.9)
text(f,.59,.398,'一张基础票 ≠ 完成一次游览',18,NAVY,'bold');text(f,.59,.341,'九寨沟：旺季门票190元＋观光车90元。\n青岩：大门票10元；参观套票60元。\n稻城亚丁：2026年8月起临时免费，有效期复核。',11,linespacing=2)
text(f,.59,.174,'200元是基础票样本最高，不是全国最高价。',11,RED)
footer(f,['来源：景区及政府价格目录；票种、公布日期、有效期与计入统计范围逐条记录在CSV。','联合挂牌的子景点、联票和含交通产品不计入基础票均价；历史全国2023年均价68元与本样本不可直接比较。'])
save(f,'06_门票价格与收费口径')

# 07 财务覆盖14家公司，12家旅游运营公司比较，2家多元集团另列。
f=sheet(7,'景区相关公司，靠什么赚钱？','14家公司 × 2023—2025年报比较｜公司合并口径，业务范围逐家核验；不作为全国5A收入排行')
companies=fin[(fin.year==2025)&(fin.comparison_group=='旅游运营公司')].sort_values('revenue_yi',ascending=False).company.tolist();y=np.arange(len(companies))
a=ax(f,[.14,.18,.30,.54],'营业收入 / 亿元')
for j,(year,col) in enumerate([(2023,'#C7D4BB'),(2024,'#709D82'),(2025,GREEN)]):
    vals=fin[fin.year==year].set_index('company').loc[companies,'revenue_yi'];a.barh(y+(j-1)*.23,vals,height=.20,color=col,label=str(year))
    if year==2025:
        for i,v in enumerate(vals):a.text(v+.25,y[i]+.23,f'{v:.2f}',va='center',fontsize=9)
a.set_yticks(y,companies,fontsize=11);a.invert_yaxis();a.set_xlim(0,26);a.legend(loc='lower right',frameon=False,fontsize=8,ncol=3)
a=ax(f,[.61,.18,.31,.54],'2025年归母与扣非归母利润 / 亿元');v=fin[fin.year==2025].set_index('company').loc[companies]
a.barh(y-.16,v.net_profit_yi,height=.30,color=GREEN,label='归母净利润');a.barh(y+.16,v.adjusted_net_profit_yi,height=.30,color=GOLD,label='扣非归母净利润');a.axvline(0,color=MUTED,lw=.7);a.set_yticks(y,companies,fontsize=10);a.invert_yaxis();a.set_xlim(-7,4);a.legend(frameon=False,fontsize=8,loc='lower left')
text(f,.07,.105,'多元集团另列：中青旅2025年合并营收113.37亿元；华侨城A313.81亿元。含旅行社、地产等业务。',11,NAVY)
footer(f,['来源：14家公司2025年年度报告；精确数值、相关景区、公司合并范围和PDF页码见CSV。','另提供13项经营主体/业务分部收入，不能与公司合并收入加总；三特索道审计带强调事项段。'])
save(f,'07_运营公司营收与利润')



# 08 更多可以由全量名录推得的有趣问题。
f=sheet(8,'还有哪些值得继续挖的数据？','先用完整名录回答供给结构，再用相同统计范围研究票价、客流与商业模式')
pp=master.assign(macro=master.category.map({'自然风光':'自然','历史人文':'人文','宗教文化':'人文','红色纪念':'人文','古城古镇':'人文','主题休闲':'休闲','综合景观':'综合'}))
mx=pd.crosstab(pp.province,pp.macro).reindex(prov.province).fillna(0)
# 联合挂牌壶口同时归陕晋，人文/自然地图仍依据实体主表，陕西补回自然1。
mx.loc['陕西','自然']+=1
topnames=prov.head(10).province.tolist();a=ax(f,[.13,.27,.42,.43],'数量最多的10省级地区：类型结构 / 家');a.grid(axis='x',color=GRID);left=np.zeros(10)
for c,col in [('自然',GREEN),('人文','#486A8C'),('休闲','#998AB1'),('综合','#A8AC94')]:
 vals=mx.loc[topnames,c].values;a.barh(np.arange(10),vals,left=left,color=col,height=.63,label=c);left+=vals
a.set_yticks(range(10),topnames,fontsize=11);a.invert_yaxis();a.set_xlim(0,30);a.legend(loc='lower right',frameon=False,fontsize=9)
text(f,.13,.18,'同样拥有较多5A，景观构成也可能不同。\n省级数量衡量供给，客流和收入还需另取同口径数据。',11,MUTED,linespacing=1.8)
blocks=[('联合挂牌的“1家”','苏州园林含拙政园、留园、虎丘；\n福建土楼与沂蒙山还跨地市。', '看名录数量，也要看景区组合。'),('低门票 ≠ 低消费','九寨沟需关注观光车，山岳景区需关注索道；\n免费古镇仍可能有游船、演出与展馆。','门票、必要交通、可选项目分别统计。'),('经营模式比门票更丰富','以峨眉山A为例，2025年索道收入\n占比41.8%，高于游山门票。','用收入分部看“门票之外”。')]
for i,(title,body,take) in enumerate(blocks):
 y=.70-i*.191;text(f,.64,y,title,17,GREEN,'bold');text(f,.64,y-.058,body,10,MUTED,linespacing=1.8);text(f,.64,y-.117,take,10,NAVY)
footer(f,['来源：全国358个景区名录、官方简介、核验票务页及2025公司年报；省级结构采用跨省归属口径，宏观类型由作者研究分类合并。','后续可扩展：游客量、接待承载量、季节性、交通时间、人口/面积标准化密度；需另取完整且同年份的对应数据，不能以本图直接推出。'])
save(f,'08_景观结构与有趣发现')

# 单一总览缩略图，便于电脑端选图。
ims=[];ff=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',27)
for path in sorted(O.glob('0*.png')):
 im=Image.open(path).convert('RGB');im.thumbnail((960,540));ims.append((path,im))
contact=Image.new('RGB',(1920,4*596),(245,241,231));draw=ImageDraw.Draw(contact)
for i,(p,im) in enumerate(ims):
 x=(i%2)*960;y=(i//2)*596;contact.paste(im,(x,y));draw.text((x+22,y+549),p.stem,font=ff,fill=NAVY)
contact.save(O/'图集总览.png')
print('CHARTS',len(ims),'3840×2160')
