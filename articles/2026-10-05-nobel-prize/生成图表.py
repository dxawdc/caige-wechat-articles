"""生成可用于公众号的高清统计配图，全部数据来自分析数据.py的整理表。"""
from pathlib import Path
import json, math, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'数据'/'整理'; IMG=ROOT/'配图'; IMG.mkdir(exist_ok=True)
FONT_PATH=os.environ.get('NOBEL_CN_FONT',r'C:\Windows\Fonts\msyh.ttc')
FONT=FontProperties(fname=FONT_PATH)
plt.rcParams.update({'font.family':FONT.get_name(),'axes.unicode_minus':False,'font.size':15,'axes.labelsize':15,'xtick.labelsize':14,'ytick.labelsize':16,'savefig.dpi':180})
BG='#FAF8F3'; INK='#18323D'; MUTED='#687A80'; BLUE='#236A88'; GOLD='#BE8B35'; TEAL='#49887E'; LINE='#E5E7E3'
COLORS={'物理学':BLUE,'化学':GOLD,'生理学或医学':'#164858','文学':'#8C7272','和平':TEAL,'经济学':'#63738E'}
NAMES={'Harvard University':'哈佛大学','Massachusetts Institute of Technology (MIT)':'麻省理工学院','Stanford University':'斯坦福大学','University of California, Berkeley':'加州大学伯克利分校','University of Chicago':'芝加哥大学','California Institute of Technology (Caltech)':'加州理工学院','Rockefeller University':'洛克菲勒大学','University of Cambridge':'剑桥大学','Columbia University':'哥伦比亚大学','Princeton University':'普林斯顿大学','University of Oxford':'牛津大学','Yale University':'耶鲁大学'}
files=[]

def load(name): return pd.read_csv(DATA/name)
def frame(title,sub,size=(10,7),foot='数据：NobelPrize.org 官方API｜1901—2025'):
    size=(size[0]*.8,size[1])
    fig=plt.figure(figsize=size,facecolor=BG)
    fig.text(.065,.945,title,fontsize=23,fontweight='bold',color=INK,va='top')
    fig.text(.065,.878,sub,fontsize=12,color=MUTED,va='top')
    fig.text(.065,.032,foot,fontsize=10,color=MUTED)
    fig.text(.94,.032,'可以叫我才哥',fontsize=10,color=BLUE,ha='right')
    fig.add_artist(Rectangle((.065,.964),.045,.008,transform=fig.transFigure,facecolor=GOLD,edgecolor='none'))
    return fig
def axes(fig,box=(.18,.13,.72,.67)):
    ax=fig.add_axes(box,facecolor=BG)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(length=0,pad=9,colors=MUTED)
    ax.set_axisbelow(True)
    return ax
def save(fig,name):
    # 标题与页脚按实际文本边界收缩，避免长中文超出画布。
    fig.canvas.draw()
    for artist in fig.texts:
        box=artist.get_window_extent(fig.canvas.get_renderer())
        if box.x1>fig.bbox.x1-12:
            available=fig.bbox.x1-12-box.x0
            if available>0: artist.set_fontsize(artist.get_fontsize()*available/box.width)
    fig.savefig(IMG/name,facecolor=fig.get_facecolor())
    plt.close(fig); files.append(name)

def overview():
    f=frame('125年诺贝尔奖，先看这几个数','1901—2025完整年份｜经济学纪念奖自1969年起计入',size=(10,6.7))
    cards=[('633','次颁奖','一个年份 × 一个学科 = 一次颁奖'),('1,026','条获奖记录','同一人或组织重复获奖分别计数'),('990','位个人','按官方获奖者ID去重'),('28','个组织','和平奖也颁给组织')]
    for i,(num,label,detail) in enumerate(cards):
        x=.07+(i%2)*.46; y=.58-(i//2)*.31
        f.text(x,y,num,fontsize=47,color=BLUE if i!=1 else GOLD,fontweight='bold')
        f.text(x+.01,y-.07,label,fontsize=19,color=INK)
        f.text(x+.01,y-.125,detail,fontsize=11,color=MUTED)
    save(f,'00_总览.png')

def schedule():
    f=frame('2026年诺奖公布时间表','北京时间｜生理学或医学奖于10月5日率先公布',size=(10,6.5),foot='来源：NobelPrize.org 2026年官方公布日程')
    rows=[('10月05日','周一','生理学或医学','17:30'),('10月06日','周二','物理学','17:45'),('10月07日','周三','化学','17:45'),('10月08日','周四','文学','19:00'),('10月09日','周五','和平','17:00'),('10月12日','周一','经济学','17:45')]
    for i,(dt,day,cat,t) in enumerate(rows):
        y=.76-i*.101
        f.text(.07,y,dt,fontsize=19,color=INK); f.text(.27,y,day,fontsize=14,color=MUTED)
        f.text(.4,y,cat,fontsize=18,color=COLORS[cat]); f.text(.83,y,t,fontsize=21,color=BLUE,fontweight='bold',ha='right')
    f.text(.065,.095,'除和平奖外，官方时间均为“最早公布时间”。',fontsize=11,color=MUTED)
    save(f,'01_公布日程.png')

def categories():
    d=load('学科统计.csv').sort_values('award_records',ascending=False)
    f=frame('哪个学科的获奖记录最多？','获奖记录 ≠ 颁奖次数｜同一奖项可由1—3个个人或组织共享',size=(10,7.2))
    ax=axes(f,(.25,.16,.66,.62)); y=np.arange(len(d))
    ax.barh(y,d.award_records,height=.55,color=[COLORS[x] for x in d.category]); ax.set_yticks(y,d.category,color=INK); ax.invert_yaxis(); ax.set_xlim(0,280); ax.set_xticks([0,100,200]); ax.xaxis.grid(color=LINE)
    for i,r in enumerate(d.itertuples()):
        ax.text(r.award_records+5,i,str(r.award_records),va='center',fontsize=18,color=INK,fontweight='bold')
        ax.text(5,i+.33,f'{r.prizes}次颁奖',va='center',fontsize=11,color=MUTED)
    f.text(.065,.095,'和平奖143条记录：112条个人记录 + 31条组织记录。',fontsize=11,color=MUTED)
    save(f,'02_学科分布.png')

def country_rank():
    d=load('出生地国家排名.csv'); d=d[d.unique_people>=d.iloc[14].unique_people]
    f=frame('获奖者出生在哪里？','出生地国家Top15（含并列）｜已知出生地987人，另3人字段缺失',size=(10,9.5))
    ax=axes(f,(.18,.13,.73,.67)); y=np.arange(len(d)); ax.barh(y,d.unique_people,height=.62,color=[GOLD if x=='CN' else BLUE for x in d.birth_country_code]); ax.set_yticks(y,d.birth_country_cn,color=INK); ax.invert_yaxis(); ax.set_xlim(0,335); ax.set_xticks([0,100,200,300]); ax.xaxis.grid(color=LINE)
    for i,r in enumerate(d.itertuples()): ax.text(r.unique_people+5,i,str(r.unique_people),va='center',color=INK,fontsize=14,fontweight='bold')
    f.text(.065,.085,'按个人ID去重；出生地按现今国家归并。出生地不代表国籍。',fontsize=11,color=MUTED)
    save(f,'03_国家排名.png')

def world_map():
    d=load('出生地国家排名.csv'); counts=dict(zip(d.birth_country_alpha3,d.unique_people))
    geo=json.loads((ROOT/'数据'/'原始'/'world.geojson').read_text(encoding='utf8'))
    f=frame('诺奖获奖者的出生地分布','按个人去重｜颜色表示人数区间，灰色为样本中未记录获奖者',size=(12,7.7))
    ax=f.add_axes((.04,.22,.92,.56),projection='mollweide',facecolor=BG)
    cols=['#E6E7E3','#DCECF0','#A7CED7','#67A5B6','#28708C','#123C51']
    bins=[1,5,15,30,100]
    plotted=set()
    for item in geo['features']:
        prop=item['properties']; iso=prop['ADM0_A3']; iso={'TWN':'CHN','FRA':'FRA','NOR':'NOR'}.get(iso,iso)
        if iso=='ATA': continue
        count=counts.get(iso,0); idx=sum(count>=b for b in bins)
        geom=item['geometry']; polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
        for poly in polys:
            ring=np.asarray(poly[0],dtype=float); ring[:,0]=np.clip(ring[:,0],-180,180)
            ax.add_patch(Polygon(np.deg2rad(ring),closed=True,facecolor=cols[idx],edgecolor=BG,linewidth=.4))
        plotted.add(iso)
    # 110m底图省略的小岛用官方国家坐标点标示，并采用相同人数色阶。
    raw=json.loads((ROOT/'数据'/'原始'/'laureates.json').read_text(encoding='utf8'))['laureates']
    import 分析数据 as analysis
    marker_countries=[]; seen=set()
    for person in raw:
        loc=person.get('birth',{}).get('place',{}).get('countryNow',{})
        name=loc.get('en','')
        if not name: continue
        _,iso,cn=analysis.country(name)
        if iso in plotted or iso in seen or iso not in counts: continue
        if 'longitude' in loc and 'latitude' in loc:
            count=counts[iso]; idx=sum(count>=b for b in bins)
            ax.scatter(math.radians(float(loc['longitude'])),math.radians(float(loc['latitude'])),s=18,color=cols[idx],edgecolor=BLUE,linewidth=.5,zorder=5)
            seen.add(iso); marker_countries.append(cn)
    ax.set_xticks([]); ax.set_yticks([]); ax.spines['geo'].set_visible(False)
    labels=['0人','1—4人','5—14人','15—29人','30—99人','100人及以上']
    for i,(color,label) in enumerate(zip(cols,labels)):
        x=.07+i*.147; f.add_artist(Rectangle((x,.153),.024,.021,transform=f.transFigure,facecolor=color)); f.text(x+.031,.156,label,fontsize=11,color=MUTED)
    f.text(.065,.105,'987人分布于81个国家；小岛采用地理坐标点补充。',fontsize=12,color=INK)
    f.text(.065,.071,'底图：Natural Earth 1:110m，Mollweide投影；国家地域归并见配套映射表。',fontsize=10,color=MUTED)
    (ROOT/'验收'/'地图核验.json').write_text(json.dumps({'country_count':len(counts),'people_total':int(d.unique_people.sum()),'polygon_country_matches':sorted(set(counts)&plotted),'point_supplements':marker_countries,'unmapped_codes':sorted(set(counts)-plotted-seen),'projection':'Mollweide','boundary_source':'Natural Earth 110m'},ensure_ascii=False,indent=2),encoding='utf8')
    save(f,'04_世界地图.png')

def repeats():
    f=frame('谁不止一次拿到诺贝尔奖？','5位个人各获奖2次；2个组织分别获奖3次、2次',size=(10,8.5))
    rows=[('红十字国际委员会','1917、1944、1963 · 和平奖',3,TEAL),('联合国难民署','1954、1981 · 和平奖',2,TEAL),('玛丽·居里','1903 · 物理学；1911 · 化学',2,BLUE),('莱纳斯·鲍林','1954 · 化学；1962 · 和平',2,BLUE),('约翰·巴丁','1956、1972 · 物理学',2,BLUE),('弗雷德里克·桑格','1958、1980 · 化学',2,BLUE),('巴里·夏普莱斯','2001、2022 · 化学',2,BLUE)]
    for i,(name,detail,n,c) in enumerate(rows):
        y=.76-i*.091
        f.text(.075,y,name,fontsize=18,color=INK,fontweight='bold'); f.text(.075,y-.037,detail,fontsize=11,color=MUTED)
        for j in range(3):
            f.add_artist(plt.Circle((.71+j*.054,y+.004),.012,transform=f.transFigure,facecolor=c if j<n else LINE,edgecolor='none'))
        f.text(.915,y,str(n)+'次',fontsize=18,color=c,ha='right',fontweight='bold')
    save(f,'05_多次获奖.png')

def schools():
    d=load('高校排名.csv').head(12)
    f=frame('获奖时，他们在哪所高校任职？','按个人ID去重｜校内院系归并、加州大学按校区拆分',size=(10,9))
    ax=axes(f,(.40,.16,.50,.64)); y=np.arange(len(d)); ax.barh(y,d.unique_people,height=.6,color=BLUE); ax.set_yticks(y,[NAMES[x] for x in d.institution_normalized],color=INK,fontsize=16); ax.invert_yaxis(); ax.set_xlim(0,45); ax.set_xticks([0,10,20,30,40]); ax.xaxis.grid(color=LINE)
    for i,r in enumerate(d.itertuples()): ax.text(r.unique_people+1,i,str(r.unique_people),va='center',fontsize=16,color=INK,fontweight='bold')
    f.text(.065,.094,'758条获奖记录具有任职机构；同一人可同时计入多所高校。',fontsize=11,color=MUTED)
    f.text(.065,.065,'包含获奖时的医学院、校内实验室及明确前身；完整归并表随数据提供。',fontsize=10,color=MUTED)
    save(f,'06_高校排名.png')

def money():
    d=load('奖金历史.csv')
    f=frame('2026年诺奖奖金，提高到1,200万','每个完整奖项的名义金额｜单位：百万瑞典克朗（SEK）',size=(10,6.8),foot='来源：官方奖金历史表 + 2026-09-18官方奖金公告')
    announced=load('2026年已公布奖金.csv').iloc[0]
    ax=axes(f,(.12,.18,.8,.58)); ax.plot(d.year,d.nominal_sek/1e6,color=GOLD,lw=3); ax.plot([2025,2026],[11,announced.nominal_sek/1e6],color=GOLD,lw=3,linestyle='--'); ax.fill_between(d.year,0,d.nominal_sek/1e6,color=GOLD,alpha=.12); ax.set_ylim(0,14.2); ax.set_xlim(1901,2026); ax.set_xticks([1901,1920,1940,1960,1980,2000,2026]); ax.set_yticks([0,3,6,9,12]); ax.yaxis.grid(color=LINE)
    ax.scatter([1901,2001,2012,2025],d.set_index('year').loc[[1901,2001,2012,2025],'nominal_sek']/1e6,color=GOLD,s=35,zorder=4)
    ax.text(1904,1.0,'1901：150,782 SEK',color=INK,fontsize=12)
    ax.annotate('2001：1,000万',(2001,10),(1970,11.5),fontsize=11,color=INK,arrowprops={'arrowstyle':'-','color':MUTED})
    ax.annotate('2012：降至800万',(2012,8),(1980,6.3),fontsize=11,color=INK,arrowprops={'arrowstyle':'-','color':MUTED})
    ax.scatter([2026],[12],color=GOLD,s=40,zorder=4)
    ax.text(2026,12.7,'2026：1,200万',ha='right',color=INK,fontsize=13,fontweight='bold')
    f.text(.065,.096,'2026比2025年增加100万（9.1%）；三人平分，每人400万SEK。',fontsize=11,color=MUTED)
    save(f,'07_名义奖金.png')
    f=frame('扣除物价变化，奖金并没涨73倍','名义金额 vs 按2025年币值折算｜单位：百万瑞典克朗',size=(10,7.2),foot='来源：诺贝尔基金会官方奖金历史表（统一按2025年币值折算）')
    ax=axes(f,(.12,.18,.8,.57)); ax.plot(d.year,d.real_2025_sek/1e6,color=BLUE,lw=3,label='按2025年币值折算'); ax.plot(d.year,d.nominal_sek/1e6,color=GOLD,lw=2.3,label='当年名义奖金'); ax.set_xlim(1901,2025); ax.set_ylim(0,18); ax.set_xticks([1901,1920,1940,1960,1980,2000,2025]); ax.set_yticks([0,5,10,15]); ax.yaxis.grid(color=LINE); ax.legend(loc='upper left',frameon=False,fontsize=12)
    ax.annotate('1901：约1,083万',(1901,10.833458),(1906,13.3),color=BLUE,fontsize=12,arrowprops={'arrowstyle':'-','color':MUTED})
    ax.annotate('2001：约1,555万',(2001,15.547541),(1976,16.7),color=BLUE,fontsize=11,arrowprops={'arrowstyle':'-','color':MUTED})
    ax.text(2025,12,'2025：1,100万',ha='right',fontsize=12,color=INK,fontweight='bold')
    f.text(.065,.095,'1901 → 2025：名义金额约72.95倍；实际币值约1.015倍。',fontsize=12,color=INK)
    save(f,'08_实际奖金.png')

def ages():
    e=load('获奖记录.csv'); d=load('性别与年龄学科统计.csv'); cats=list(COLORS)
    f=frame('诺奖获奖年龄：17岁到97岁','按获奖年份12月10日计算周岁｜975条记录生日完整，另20条缺失',size=(10,7.7))
    ax=axes(f,(.24,.2,.64,.56)); arr=[e[(e.category==c)&e.age_dec10.notna()].age_dec10 for c in cats]
    b=ax.boxplot(arr,orientation='horizontal',tick_labels=cats,widths=.5,patch_artist=True,showfliers=False,whis=(0,100),medianprops={'color':BG,'linewidth':2.4},whiskerprops={'color':MUTED},capprops={'color':MUTED})
    for box,c in zip(b['boxes'],cats): box.set_facecolor(COLORS[c]); box.set_edgecolor(COLORS[c])
    ax.invert_yaxis(); ax.set_xlim(10,105); ax.set_xticks([20,40,60,80,100]); ax.xaxis.grid(color=LINE); ax.set_xlabel('年龄（岁）')
    for i,c in enumerate(cats):
        r=d[d.category==c].iloc[0]; ax.text(103,i+1,f'{r.median_age:g}',va='center',ha='left',color=INK,fontsize=16,fontweight='bold')
    f.text(.875,.795,'中位数',fontsize=11,color=MUTED,ha='center')
    f.text(.065,.118,'箱体为中间50%的获奖年龄；须线为全部样本最小值与最大值。',fontsize=11,color=MUTED)
    f.text(.065,.075,'年龄表示获得该年份奖项时的年龄，无法据此推算做出成果的年龄。',fontsize=11,color=MUTED)
    save(f,'09_获奖年龄.png')

def gender():
    d=load('性别与年龄学科统计.csv').copy(); d['female_percent']=d.female_records/d.people_records*100; d=d.sort_values('female_percent',ascending=False)
    f=frame('女性获奖比例，学科差异很大','995条个人获奖记录中，女性68条（6.8%）；去重后为67位女性',size=(10,7))
    ax=axes(f,(.25,.2,.66,.58)); y=np.arange(len(d)); ax.barh(y,d.female_percent,height=.57,color=TEAL); ax.set_yticks(y,d.category,color=INK); ax.invert_yaxis(); ax.set_xlim(0,24); ax.set_xticks([0,5,10,15,20],['0%','5%','10%','15%','20%']); ax.xaxis.grid(color=LINE)
    for i,r in enumerate(d.itertuples()): ax.text(r.female_percent+.5,i,f'{r.female_percent:.1f}%  ({r.female_records}/{r.people_records})',fontsize=12,color=INK,va='center')
    f.text(.065,.1,'分母为各学科个人获奖记录；和平奖的组织记录不进入性别统计。',fontsize=11,color=MUTED)
    save(f,'10_女性学科分布.png')
    d=load('十年性别年龄趋势.csv')
    f=frame('女性获奖比例，近年怎样变化？','按十年分组｜2020年代仅含2020—2025，时间长度与前组不同',size=(10,7))
    ax=axes(f,(.12,.23,.8,.55)); x=np.arange(len(d)); ax.bar(x,d.female_percent,color=[TEAL]*(len(d)-1)+[GOLD],width=.65); ax.set_xticks(x,[str(v)+'s' for v in d.decade],rotation=45,ha='right',fontsize=11); ax.set_ylim(0,23); ax.set_yticks([0,5,10,15,20],['0%','5%','10%','15%','20%']); ax.yaxis.grid(color=LINE)
    for i,r in enumerate(d.itertuples()): ax.text(i,r.female_percent+.5,f'{r.female_percent:.1f}%',ha='center',fontsize=10,color=INK)
    f.text(.065,.095,'2000—2009：11/119；2010—2019：13/117；2020—2025：14/72。',fontsize=11,color=MUTED)
    save(f,'11_女性比例趋势.png')

def shared():
    d=load('共享奖项时期统计.csv')
    f=frame('诺奖，越来越常由多人共享','按已颁发的“年份 × 学科”奖项统计｜全学科，含和平奖组织',size=(10,6.8))
    ax=axes(f,(.24,.25,.66,.5)); y=np.arange(len(d)); left=np.zeros(len(d)); colors=[BLUE,TEAL,GOLD]
    for col,color,label in zip(['solo','two','three'],colors,['1个获奖主体','2个获奖主体','3个获奖主体']):
        vals=d[col]/d.total*100; ax.barh(y,vals,left=left,color=color,height=.55,label=label)
        for i,(v,s) in enumerate(zip(vals,left)):
            if v>8: ax.text(s+v/2,i,f'{v:.1f}%',ha='center',va='center',color='white',fontsize=15,fontweight='bold')
        left+=vals
    ax.set_yticks(y,d.period,color=INK); ax.invert_yaxis(); ax.set_xlim(0,100); ax.set_xticks([0,50,100],['0%','50%','100%']); f.legend(*ax.get_legend_handles_labels(),bbox_to_anchor=(.19,.205),loc='upper left',ncol=3,frameon=False,fontsize=11)
    f.text(.065,.115,'共享奖项占比：1901—1950为22.3%，2001—2025为64.7%。',fontsize=12,color=INK)
    f.text(.065,.075,'经济学1969年加入、学科结构也在变化；不单凭总趋势解释原因。',fontsize=10,color=MUTED)
    save(f,'12_共享奖项.png')

def mobility():
    d=load('出生地与任职国家.csv'); us=d[d.country_code=='US'].drop_duplicates(['laureate_id','year','category']); usborn=int((us.birth_country_code=='US').sum()); foreign=len(us)-usborn
    f=frame('在美国机构获奖，也可能出生于别处','筛选获奖时有美国任职机构、且出生地已知的个人获奖记录',size=(10,6.5))
    ax=axes(f,(.27,.3,.63,.43)); values=[usborn,foreign]; labels=['出生于美国','出生于其他国家']; y=np.arange(2); ax.barh(y,values,height=.48,color=[BLUE,GOLD]); ax.set_yticks(y,labels,color=INK); ax.invert_yaxis(); ax.set_xlim(0,335); ax.set_xticks([0,100,200,300]); ax.xaxis.grid(color=LINE)
    for i,v in enumerate(values): ax.text(v+5,i,f'{v}条',fontsize=18,color=INK,va='center',fontweight='bold')
    f.text(.065,.157,f'已知出生地的{len(us)}条记录中，{foreign}条（{foreign/len(us)*100:.1f}%）出生于美国之外。',fontsize=13,color=INK)
    f.text(.065,.09,'按每个奖项去重；同获奖者重复获奖分别计数。任职地不等于国籍。',fontsize=11,color=MUTED)
    save(f,'13_出生与任职.png')

def contact_sheet():
    thumbs=[]
    for name in files:
        im=Image.open(IMG/name).convert('RGB'); im.thumbnail((520,490))
        card=Image.new('RGB',(560,540),'#E8E9E6'); card.paste(im,((560-im.width)//2,15))
        ImageDraw.Draw(card).text((15,512),name,font=__import__('PIL').ImageFont.truetype(FONT_PATH,18),fill='#18323D')
        thumbs.append(card)
    rows=math.ceil(len(thumbs)/3); out=Image.new('RGB',(1680,rows*540),'#E8E9E6')
    for i,im in enumerate(thumbs): out.paste(im,((i%3)*560,(i//3)*540))
    out.save(ROOT/'验收'/'全部图表预览.jpg',quality=92)
    (ROOT/'验收'/'配图清单.json').write_text(json.dumps(files,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    overview(); schedule(); categories(); country_rank(); world_map(); repeats(); schools(); money(); ages(); gender(); shared(); mobility(); contact_sheet()
    print('生成',len(files),'张图表')
