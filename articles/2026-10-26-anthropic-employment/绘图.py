"""绘制报告端点对照、作者实践流程与可编辑封面；不生成或修改AI栅格图。"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '配图'
OUT.mkdir(exist_ok=True)
fonts = {f.name for f in fm.fontManager.ttflist}
font = next((f for f in ['Microsoft YaHei', 'Noto Sans CJK SC', 'SimHei', 'Arial Unicode MS'] if f in fonts), 'sans-serif')
plt.rcParams.update({'font.family': font, 'axes.unicode_minus': False, 'svg.fonttype': 'none', 'svg.hashsalt': 'caige-anthropic-employment'})
BG, INK, TEAL, RED, VIOLET, GRID = '#F9F7F2', '#213638', '#166B72', '#BD5B42', '#75628E', '#E3E0D8'

def canvas(w, h):
    fig = plt.figure(figsize=(w/100, h/100), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, w), ylim=(h, 0))
    ax.axis('off')
    return fig, ax

def txt(ax, x, y, value, size=26, color=INK, weight='normal', **kw):
    return ax.text(x, y, value, fontsize=size, color=color, weight=weight, va='center', **kw)

def save(fig, name, svg=False):
    fig.savefig(OUT / (name+'.png'), facecolor=BG, dpi=100)
    if svg:
        target = OUT / (name+'.svg')
        fig.savefig(target, facecolor=BG, metadata={'Date': None})
        target.write_text('\n'.join(line.rstrip() for line in target.read_text(encoding='utf8').splitlines())+'\n', encoding='utf8')
    plt.close(fig)

def chart():
    data = json.loads((ROOT / '数据/数据与来源.json').read_text(encoding='utf8'))['chart']
    fig, ax = canvas(1400, 1000)
    txt(ax, 75, 84, '初级技术人员，占比怎样变化？', 40, weight='bold')
    txt(ax, 75, 145, 'Anthropic｜2025—2026年报告观察期的前后端点', 21, '#667474')
    for i, row in enumerate(data['rows']):
        y = 230 + i * 335
        txt(ax, 75, y, row['label'], 34, weight='bold')
        txt(ax, 75, y+42, '分母：'+row['denominator'], 19, '#667474')
        start_x, width = 230, 930
        for j, (key, lab, color) in enumerate([('start', '较早端点', VIOLET), ('end', '较晚端点', TEAL)]):
            cy = y + 110 + j * 85
            txt(ax, 75, cy, lab, 25)
            ax.add_patch(Rectangle((start_x, cy-24), width, 48, color='#ECE9E2', lw=0))
            ax.add_patch(Rectangle((start_x, cy-24), width*row[key]/30, 48, color=color, lw=0))
            txt(ax, start_x+width*row[key]/30+18, cy, str(row[key])+'%', 40, color, 'bold')
        # Both panels share a zero-based 0–30% scale.
        for tick in [0, 10, 20, 30]:
            txt(ax, start_x+width*tick/30, y+257, str(tick)+'%', 17, '#667474', ha='center')
    txt(ax, 75, 905, '正文取整值重绘；同一尺度；不表示初级招聘人数下降的幅度。', 18, '#667474')
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
        ax.add_patch(Circle((145,y+70),35,fc=[TEAL,VIOLET,RED,TEAL][i],ec='none'))
        txt(ax,145,y+70,n,24,'white','bold',ha='center')
        txt(ax,220,y+55,title,34,weight='bold')
        txt(ax,220,y+115,desc,30)
        if i<3:
            ax.add_patch(FancyArrowPatch((600,y+181),(600,y+211),arrowstyle='-|>',mutation_scale=20,color=TEAL,lw=2))
    txt(ax,70,1160,'检查重点：结果是否可靠、是否支持具体决定。',22,TEAL,'bold')
    txt(ax,1130,1220,'可以叫我才哥',17,'#667474',ha='right')
    save(fig,'图2_任务检查顺序')

def cover(square=False):
    w,h=(1200,1200) if square else (1800,766)
    fig,ax=canvas(w,h)
    txt(ax,90,110,'Anthropic 内部就业报告',25,TEAL)
    txt(ax,90,245 if square else 300,'AI干得越多',98 if square else 68,INK,'bold')
    txt(ax,90,400 if square else 440,'人该做什么？',96 if square else 68,RED,'bold')
    # Editable geometric metaphor: task cards converging at a decision point.
    ox,oy=(340,575) if square else (1210,185)
    for i,c in enumerate([TEAL,VIOLET,RED]):
        x,y=ox+i*72,oy+i*95
        ax.add_patch(FancyBboxPatch((x,y),300,170,boxstyle='round,pad=0,rounding_size=20',fc=c,ec='none',alpha=.95))
        for k,ln in enumerate([190,145,170]):
            ax.plot([x+40,x+40+ln],[y+45+k*32,y+45+k*32],color=BG,lw=5,alpha=.8)
    ax.add_patch(Circle((ox-90,oy+235),62,fc=INK,ec='none'))
    txt(ax,ox-90,oy+235,'?',54,BG,'bold',ha='center')
    txt(ax,w-75,h-60,'概念示意',18,'#667474',ha='right')
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
    txt(ax,65,1245,'人类按40小时/人/周估算；代理运行口径见文末。',22,'#667474')
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
    print('Created 5 article figures; existing cover assets preserved.')
