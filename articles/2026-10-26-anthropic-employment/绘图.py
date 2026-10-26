"""绘制报告端点对照、作者实践流程与可编辑封面；不生成或修改AI栅格图。"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch, Polygon
import 手绘主题 as hand

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '配图'
OUT.mkdir(exist_ok=True)
fonts = {f.name for f in fm.fontManager.ttflist}
font = next((f for f in ['Microsoft YaHei', 'Noto Sans CJK SC', 'SimHei', 'Arial Unicode MS'] if f in fonts), 'sans-serif')
plt.rcParams.update({'font.family': font, 'axes.unicode_minus': False, 'svg.fonttype': 'none', 'svg.hashsalt': 'caige-anthropic-employment'})
BG, INK, TEAL, RED, VIOLET, GRID = hand.PAPER, hand.INK, hand.BLUE, hand.ORANGE, hand.ORANGE, '#C5D1D6'

def canvas(w, h):
    fig = plt.figure(figsize=(w/100, h/100), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, w), ylim=(h, 0))
    ax.axis('off')
    if h>900 and w!=h: hand.paper(ax,w,h)
    return fig, ax

def txt(ax, x, y, value, size=26, color=INK, weight='normal', **kw):
    return hand.text(ax,x,y,value,size,color,weight,**kw)

def save(fig, name, svg=False):
    for ax in fig.axes: hand.finish(ax)
    fig.savefig(OUT / (name+'.png'), facecolor=BG, dpi=100)
    if svg:
        # Keep actual editable text nodes in SVG; PNG retains the ink-stroke effect.
        for ax in fig.axes:
            for label in ax.texts: label.set_path_effects([])
        target = OUT / (name+'.svg')
        fig.savefig(target, facecolor=BG, metadata={'Date': None})
        target.write_text('\n'.join(line.rstrip() for line in target.read_text(encoding='utf8').splitlines())+'\n', encoding='utf8')
    plt.close(fig)

def chart():
    data = json.loads((ROOT / '数据/数据与来源.json').read_text(encoding='utf8'))['chart']
    fig, ax = canvas(1400, 1000)
    txt(ax, 75, 84, '初级技术人员，占比怎样变化？', 40, weight='bold')
    txt(ax, 75, 145, 'Anthropic｜2025—2026年报告观察期的前后端点', 21, '#667474')
    ax.add_patch(Circle((90,195),10,fc=BG,ec=VIOLET,lw=2))
    txt(ax,115,195,'较早端点',22,VIOLET)
    ax.add_patch(Circle((345,195),10,fc=TEAL,ec=TEAL,lw=2))
    txt(ax,370,195,'较晚端点',22,TEAL)
    start_x,width=170,1070
    for tick in [0,10,20,30]:
        x=start_x+width*tick/30
        ax.plot([x,x],[310,830],color=GRID,lw=.8,alpha=.7,linestyle='--')
        txt(ax,x,858,str(tick)+'%',22,hand.MUTED,ha='center')
    for i, row in enumerate(data['rows']):
        y=260+i*330
        txt(ax,75,y,row['label'],32,weight='bold')
        txt(ax,75,y+42,'分母：'+row['denominator'],21,hand.MUTED)
        cy=y+130
        a=start_x+width*row['start']/30
        b=start_x+width*row['end']/30
        hand.line(ax,[b,a],[cy,cy],hand.MUTED,1.8)
        ax.add_patch(Circle((a,cy),13,fc=BG,ec=VIOLET,lw=2.5,zorder=3))
        ax.add_patch(Circle((b,cy),13,fc=TEAL,ec=TEAL,lw=2.5,zorder=3))
        txt(ax,a,cy-43,str(row['start'])+'%',37,VIOLET,'bold',ha='center')
        txt(ax,b,cy-43,str(row['end'])+'%',37,TEAL,'bold',ha='center')
        arrow=FancyArrowPatch((a-10,cy+35),(b+10,cy+35),connectionstyle='arc3,rad=-.16',arrowstyle='->',mutation_scale=22,color=INK,lw=1.8)
        arrow.set_sketch_params(scale=1.1,length=150,randomness=2)
        ax.add_patch(arrow)
        txt(ax,(a+b)/2,cy+70+abs(a-b)*.08,'下降'+str(row['start']-row['end'])+'个百分点',26,INK,ha='center')
    txt(ax,75,905,'同一0—30%尺度；仅比较报告端点。',20,hand.MUTED)
    txt(ax, 75, 956, '数据：Anthropic（2026-10-16）', 17, '#667474')
    txt(ax, 1325, 956, '可以叫我才哥', 17, '#667474', ha='right')
    save(fig, '图1_初级技术人员占比')

def workflow():
    fig, ax = canvas(1200, 1250)
    txt(ax, 70, 80, '让一项AI协作任务有始有终', 32, weight='bold')
    txt(ax, 70, 140, '以每周业务简报为例 · 作者实践建议', 21, '#667474')
    steps = [
        ('01', '定义任务', '明确读者、问题、数据范围'),
        ('02', '交给AI', '整理、计算、起草，标出疑问'),
        ('03', '人工验收', '核对数字，检查结论是否可靠'),
        ('04', '反馈改进', '记录错误，听取使用者反馈')]
    for i, (n, title, desc) in enumerate(steps):
        y = 225 + i*220
        ax.add_patch(FancyBboxPatch((70,y),1060,170,boxstyle='round,pad=0,rounding_size=20',fc='white',ec=GRID,lw=1.5))
        tape=Polygon([(930,y-12),(1050,y-6),(1048,y+15),(928,y+10)],fc='#E8C76F',ec='none',alpha=.5,zorder=3)
        tape.set_sketch_params(scale=1,length=120,randomness=2)
        ax.add_patch(tape)
        ax.add_patch(Circle((145,y+70),35,fc=[TEAL,VIOLET,RED,TEAL][i],ec='none'))
        txt(ax,145,y+70,n,24,'white','bold',ha='center')
        txt(ax,220,y+55,title,34,weight='bold')
        txt(ax,220,y+115,desc,30)
        if i<3:
            arrow=FancyArrowPatch((600,y+179),(620,y+211),connectionstyle='arc3,rad=.35',arrowstyle='->',mutation_scale=23,color=TEAL,lw=2)
            arrow.set_sketch_params(scale=1.2,length=150,randomness=2)
            ax.add_patch(arrow)
    txt(ax,70,1160,'检查重点：结果是否可靠、是否支持具体决定。',22,TEAL,'bold')
    txt(ax,1130,1220,'可以叫我才哥',17,'#667474',ha='right')
    save(fig,'图2_任务检查顺序')

def cover(square=False):
    w,h=(1200,1200) if square else (1800,766)
    fig,ax=canvas(w,h)
    hand.paper(ax,w,h)
    data=json.loads((ROOT/'数据/数据与来源.json').read_text(encoding='utf8'))['productivity']
    growth=[round((row['ratio']-1)*100) for row in data['rows']]
    assert growth==[410,210,210,70,40,40]
    roles=['工程师','数据科学家','法务人员','销售人员','招聘人员','应付账款\n处理人员']
    if not square:
        txt(ax,100,130,'Anthropic 内部就业报告',30,INK)
        txt(ax,100,275,'六类岗位',64,INK,'bold')
        txt(ax,100,390,'人均产出',64,INK,'bold')
        txt(ax,100,505,'增加了多少？',64,TEAL,'bold')
        hand.line(ax,[104,800],[575,568],'#D8B346',9,alpha=.65)
        txt(ax,100,655,'相对2025年12月 · 原图终点增幅',24,hand.MUTED)
        hand.line(ax,[945,945],[105,665],hand.MUTED,1.2,linestyle='--',alpha=.5)
        txt(ax,1010,110,'六类岗位人均产出增幅',29,INK,'bold')
        x,width,top,gap,bh=1240,285,195,76,35
        labelx,valuex,labelsize,valuesize=1010,1585,23,31
    else:
        txt(ax,90,115,'六类岗位',52,INK,'bold')
        txt(ax,90,215,'人均产出增加了多少？',48,TEAL,'bold')
        hand.line(ax,[95,1055],[280,274],'#D8B346',8,alpha=.65)
        txt(ax,90,335,'相对2025年12月 · 原图终点增幅',25,hand.MUTED)
        x,width,top,gap,bh=400,445,440,95,42
        labelx,valuex,labelsize,valuesize=95,915,30,38
    for i,(role,value) in enumerate(zip(roles,growth)):
        y=top+i*gap
        txt(ax,labelx,y,role,labelsize,INK,linespacing=1.05)
        ax.add_patch(Rectangle((x,y-bh/2),width*value/450,bh,fc=TEAL,lw=0))
        txt(ax,valuex,y,f'+{value}%',valuesize,TEAL,'bold')
    axis_y=top+5*gap+bh/2+32
    hand.line(ax,[x,x+width],[axis_y,axis_y],hand.MUTED,1)
    for tick in [0,200,400]:
        txt(ax,x+width*tick/450,axis_y+30,str(tick)+'%',20 if not square else 24,hand.MUTED,ha='center')
    if not square:
        txt(ax,1010,712,'较2025年12月；按各岗位自身指标',19,hand.MUTED)
    else:
        txt(ax,90,1085,'各岗位按自身产出指标计算',24,hand.MUTED)
        txt(ax,90,1140,'来源：Anthropic 内部就业报告',23,hand.MUTED)
    save(fig,'封面_方版模板' if square else '封面_横版模板',svg=True)


def footer(ax, h, w=1300):
    txt(ax,65,h-35,'来源：Anthropic · 2026-10-16',17,'#667474')
    txt(ax,w-65,h-35,'可以叫我才哥',17,'#667474',ha='right')

def productivity():
    data=json.loads((ROOT/'数据/数据与来源.json').read_text(encoding='utf8'))['productivity']
    fig,ax=canvas(1300,1430)
    txt(ax,65,80,'哪些岗位的人均产出增加了？',36,weight='bold')
    txt(ax,65,140,'2025年12月 = 1；比较原图标注的终点倍数',23,'#667474')
    for i,row in enumerate(data['rows']):
        y=230+i*170
        txt(ax,65,y,row['role']+'｜'+row['metric'].replace('人均',''),27,weight='bold')
        x,width=65,1010
        ax.add_patch(Rectangle((x,y+37),width,43,fc='#ECE9E2',lw=0))
        ax.add_patch(Rectangle((x,y+37),width*row['ratio']/5.5,43,fc=TEAL,lw=0))
        # Dashed line marks a shared reference of 1, with all bars starting at zero.
        ax.plot([x+width/5.5]*2,[y+30,y+86],color=VIOLET,lw=2,linestyle='--')
        txt(ax,x+width*row['ratio']/5.5+20,y+60,f"{row['ratio']:.1f}倍",34,TEAL,'bold')
    for tick in [0,1,2,3,4,5]:
        txt(ax,65+1010*tick/5.5,1260,str(tick),20,'#667474',ha='center')
    txt(ax,65,1320,'各岗位原单位不同；倍数不代表贡献排名或AI因果效果。',21,'#667474')
    footer(ax,1430)
    save(fig,'图2_各岗位人均产出')

def ai_usage():
    data=json.loads((ROOT/'数据/数据与来源.json').read_text(encoding='utf8'))
    fig,ax=canvas(1300,1370)
    txt(ax,65,75,'AI被用得更多，也用得更广',36,weight='bold')
    txt(ax,65,150,'A. 非技术员工的编程类AI会话',28,weight='bold')
    txt(ax,65,202,'月度指标 · 次/月',22,'#667474')
    s=data['nontechnical_sessions']
    for i,(label,key,color) in enumerate([('2025年8月','start',VIOLET),('2026年5月','end',TEAL)]):
        y=295+i*115
        txt(ax,65,y,label,25)
        ax.add_patch(Rectangle((340,y-25),750*s[key]/100,50,fc=color,lw=0))
        txt(ax,340+750*s[key]/100+22,y,str(s[key]),40,color,'bold')
    ax.plot([340,1090],[480,480],color=GRID,lw=2)
    for tick in [0,50,100]: txt(ax,340+750*tick/100,515,str(tick),21,'#667474',ha='center')
    txt(ax,65,590,'90 ÷ 2 = 45倍（本文计算）',29,TEAL,'bold')
    ax.plot([65,1235],[650,650],color=GRID,lw=2)
    txt(ax,65,730,'B. 交互式代理运行工时 / 人类估算工时',27,weight='bold')
    txt(ax,65,785,'2026年8月 · 比值',22,'#667474')
    for i,(label,key,color) in enumerate([('全公司','all_employees',TEAL),('其中：研究组织','research_organizations',RED)]):
        y=875+i*120
        value=data['agent_hours'][key]
        txt(ax,65,y,label,25)
        ax.add_patch(Rectangle((340,y-25),750*value/20,50,fc=color,lw=0))
        txt(ax,340+750*value/20+20,y,str(value)+'∶1',34,color,'bold')
    ax.plot([340,1090],[1070,1070],color=GRID,lw=2)
    for tick in [0,10,20]: txt(ax,340+750*tick/20,1110,str(tick),21,'#667474',ha='center')
    txt(ax,65,1190,'上下两组单位不同；研究组织属于公司内部子集。',22,'#667474')
    txt(ax,65,1245,'人类按40小时/人/周估算；仅计交互式代理。',22,'#667474')
    footer(ax,1370)
    save(fig,'图3_AI使用规模')

def coordination():
    data=json.loads((ROOT/'数据/数据与来源.json').read_text(encoding='utf8'))
    fig,ax=canvas(1300,1360)
    txt(ax,65,75,'任务管理和人际协作，也在增加',34,weight='bold')
    txt(ax,65,150,'A. 元工作在交互式会话中的占比',28,weight='bold')
    txt(ax,65,205,'设计流程、编写指令、审阅与监控等',23,'#667474')
    for i,(label,key,color) in enumerate([('2025年8—10月','start',VIOLET),('2026年4—6月','end',TEAL)]):
        y=300+i*115
        value=data['meta_work'][key]
        txt(ax,65,y,label,24)
        ax.add_patch(Rectangle((375,y-25),700*value/30,50,fc=color,lw=0))
        txt(ax,375+700*value/30+20,y,str(value)+'%',38,color,'bold')
    ax.plot([375,1075],[480,480],color=GRID,lw=2)
    for tick in [0,10,20,30]: txt(ax,375+700*tick/30,520,str(tick)+'%',20,'#667474',ha='center')
    txt(ax,65,590,'增加12个百分点 · 达到原来的2.2倍',27,TEAL,'bold')
    ax.plot([65,1235],[650,650],color=GRID,lw=2)
    txt(ax,65,725,'B. 会议时长相对一年前的增幅',28,weight='bold')
    for i,(lab,key,color) in enumerate([('全体员工中位数','all_employee_median_growth_percent',TEAL),('技术个人贡献者','technical_ic_growth_percent',RED)]):
        y=850+i*115
        value=data['meetings'][key]
        txt(ax,65,y,lab,24)
        ax.add_patch(Rectangle((375,y-25),700*value/25,50,fc=color,lw=0))
        txt(ax,375+700*value/25+20,y,'+'+str(value)+'%',36,color,'bold')
    ax.plot([375,1075],[1030,1030],color=GRID,lw=2)
    for tick in [0,10,20]: txt(ax,375+700*tick/25,1070,str(tick)+'%',20,'#667474',ha='center')
    txt(ax,65,1160,'上图为会话占比，下图为时长相对增幅。',23,'#667474')
    txt(ax,65,1220,'技术个人贡献者：不担任人员管理的技术岗位。',22,'#667474')
    footer(ax,1360)
    save(fig,'图4_管理与协作')

if __name__=='__main__':
    chart(); productivity(); ai_usage(); coordination(); workflow()
    # Existing cover assets remain unchanged when revising article data.
    for square,stem in [(False,'封面_横版模板'),(True,'封面_方版模板')]:
        if not (OUT/(stem+'.svg')).exists() or not (OUT/(stem+'.png')).exists(): cover(square)
    print('Created 5 hand-drawn article figures; exact data coordinates preserved.')
