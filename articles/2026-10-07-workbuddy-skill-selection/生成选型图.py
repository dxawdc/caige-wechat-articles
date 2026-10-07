"""以同一组矢量指令生成 PNG 和可编辑 SVG。依赖 Pillow；中文字体可用 --font 指定。"""
from pathlib import Path
import argparse, html, json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BG, INK, MUTED, GREEN, ORANGE = '#F5F3EC', '#153E36', '#61726C', '#23765D', '#E78445'
FONT = None

class Canvas:
    def __init__(self, w, h):
        self.w,self.h=w,h
        self.im=Image.new('RGB',(w,h),BG)
        self.d=ImageDraw.Draw(self.im)
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="{BG}"/>']
    def rect(self,x,y,w,h,fill,r=0,stroke=None):
        self.d.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=fill,outline=stroke,width=2)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="2"' if stroke else '')+'/>')
    def line(self,x1,y1,x2,y2,fill=GREEN,width=3):
        self.d.line((x1,y1,x2,y2),fill=fill,width=width)
        self.svg.append(f'<path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="{fill}" stroke-width="{width}"/>')
    def text(self,x,y,s,size=40,color=INK,bold=False):
        font=ImageFont.truetype(FONT,size)
        box=self.d.textbbox((x,y),s,font=font,anchor='lt')
        assert box[2] <= self.w-25, (s,box,self.w)
        self.d.text((x,y),s,font=font,fill=color,anchor='lt',stroke_width=1 if bold else 0)
        self.svg.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(s)}</text>')
    def header(self,n,title,sub):
        self.rect(64,54,116,10,ORANGE,5)
        self.text(64,94,title,62,bold=True)
        self.text(66,182,sub,31,color=MUTED)
        self.text(1050,61,f'{n:02}',32,color=GREEN)
    def footer(self):
        self.line(64,self.h-95,self.w-64,self.h-95,'#DADFD5',2)
        self.text(64,self.h-65,'WorkBuddy 技能选型 · 示意图',27,color=MUTED)
        self.text(self.w-280,self.h-65,'可以叫我才哥',28,color=GREEN)
    def save(self,name):
        out=ROOT/'配图';out.mkdir(exist_ok=True)
        self.im.save(out/(name+'.png'),optimize=True)
        (out/(name+'.svg')).write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')

def tile(c,y,num,title,skill,note,h=210):
    c.rect(64,y,1072,h,'#FFFFFF',22)
    c.rect(85,y+26,76,76,GREEN,20)
    c.text(100,y+45,num,37,color='#FFFFFF',bold=True)
    c.text(188,y+26,title,43,bold=True)
    c.text(188,y+91,skill,34,color=GREEN)
    c.text(188,y+146,note,32,color=MUTED)

def make():
    c=Canvas(1200,1540);c.header(1,'你要完成哪类工作？','先选任务，再看对应技能')
    rows=[('01','办公文件','Word / Excel / PPT / PDF','docx · xlsx · pptx · pdf'),('02','写作材料','方案 / 文章 / 内部汇报','按读者和用途选择写作流程'),('03','内容配图','封面 / 信息图 / 图文卡片','按单张或多张、阅读方式选择'),('04','资料与排版','网页保存 / 文章排版','把收集、写作与交付接起来'),('05','文件与杂事','文件 / 票据 / 会议表达','按整理对象选择专门流程'),('06','方法复用','把稳定的工作方法做成技能','先有成果和标准，再考虑定制')]
    for i,(num,title,sub,note) in enumerate(rows):
        y=260+i*190
        c.rect(64,y,1072,166,'#FFFFFF',20)
        c.text(92,y+26,num,40,color=ORANGE,bold=True)
        c.text(191,y+21,title,43,bold=True)
        c.text(470,y+28,sub,31,color=GREEN)
        c.text(191,y+99,note,32,color=MUTED)
    c.footer();c.save('图1_场景导航')

    c=Canvas(1200,1250);c.header(2,'办公文件，按交付物选','先确定最后要拿到什么文件')
    for i,row in enumerate([('01','Word 文档','docx','报告、方案、修订与格式'),('02','Excel 表格','xlsx','数据清洗、公式、统计与图表'),('03','演示文稿','pptx','汇报、课件、模板与可编辑页面'),('04','PDF 资料','pdf','提取、合并、拆分与扫描件识别')]):tile(c,260+i*214,*row,h=192)
    c.footer();c.save('图2_办公文件')

    c=Canvas(1200,1080);c.header(3,'写什么，就选什么流程','方案、内容与内部沟通各有重点')
    for i,row in enumerate([('05','把方案讲清楚','doc-coauthoring','补齐背景 → 组织结构 → 读者检查'),('06','研究后写文章','content-research-writer','查资料 → 列大纲 → 写作与引用'),('07','同步团队信息','internal-comms','围绕对象、目的与团队格式整理')]):tile(c,260+i*230,*row)
    c.footer();c.save('图3_写作选型')

    c=Canvas(1200,1390);c.header(4,'配图，按阅读方式选','不同任务，需要不同的信息组织')
    for i,(num,title,skill,note) in enumerate([('08','封面：让人看懂主题','baoyu-cover-image','一个主体，突出一项阅读收益'),('09','信息图：看清关系','baoyu-infographic','把流程、分类、对比组织成一张图'),('10','图文卡片：逐张展开','baoyu-xhs-images','拆分内容，安排连续阅读顺序')]):
        y=260+i*330
        c.rect(64,y,1072,300,'#FFFFFF',22)
        c.text(92,y+26,num,38,color=ORANGE,bold=True)
        c.text(177,y+25,title,43,bold=True)
        c.text(177,y+92,skill,34,color=GREEN)
        c.text(177,y+151,note,32,color=MUTED)
        if i==0:
            c.rect(180,y+215,285,52,'#DCECDF',8);c.rect(193,y+228,134,12,GREEN,4);c.rect(373,y+224,62,31,ORANGE,8)
        elif i==1:
            for x in [180,306,432]:c.rect(x,y+215,88,52,'#DCECDF',10)
            c.line(270,y+240,300,y+240);c.line(397,y+240,427,y+240)
        else:
            for j,x in enumerate([180,287,394,501]):
                c.rect(x,y+207,82,67,'#DCECDF',10);c.text(x+28,y+224,str(j+1),29,color=GREEN)
    c.footer();c.save('图4_配图选型')

    c=Canvas(1200,1090);c.header(5,'把资料变成文章','工作组合示意 · 各环节分别核对')
    for i,row in enumerate([('1','保存网页资料','baoyu-url-to-markdown','保留来源与日期，检查正文完整度'),('2','研究并完成写作','content-research-writer','组织论点与证据，核对关键引用'),('3','输出排版文件','baoyu-markdown-to-html','得到 HTML 后，继续检查实际排版')]):
        tile(c,260+i*230,*row,h=205)
    c.footer();c.save('图5_资料流程')

    c=Canvas(1200,1420);c.header(6,'从一组常用技能开始','按岗位需要挑选，不必一次装齐')
    rows=[('行政与日常办公','docx + pdf + file-organizer','文档交付、资料处理、文件整理'),('运营与数据汇报','xlsx + pptx','整理数据，形成可编辑汇报材料'),('产品与项目管理','doc-coauthoring + internal-comms','写清方案，同步项目进展'),('公众号与内容创作','content-research-writer','搭配 baoyu-cover-image 制作封面'),('知识与社交图文','baoyu-xhs-images','按需搭配 baoyu-infographic')]
    for i,(title,skill,note) in enumerate(rows):
        y=260+i*207;c.rect(64,y,1072,183,'#FFFFFF',20)
        c.rect(88,y+28,9,46,ORANGE,4)
        c.text(120,y+23,title,43,bold=True);c.text(120,y+84,skill,33,color=GREEN);c.text(120,y+133,note,31,color=MUTED)
    c.footer();c.save('图6_岗位组合')

    c=Canvas(1200,1230);c.header(7,'选好以后，跑通一件事','从小样本开始，打开实际成果检查')
    for i,row in enumerate([('1','核对来源','作者 / 仓库 / 版本','同名技能，也要确认是不是同一个'),('2','确认交付物','文档 / 表格 / 图片 / 页面','你需要的格式，能不能继续编辑'),('3','检查运行条件','依赖 / 服务 / 授权 / 费用','技能文件和所需工具分别确认'),('4','用小样本验证','执行 → 打开 → 核对 → 保留','有用再保留，重要文件先用副本')]):tile(c,250+i*213,*row,h=190)
    c.footer();c.save('图7_使用路径')

    for square in [False,True]:
        w,h=(1200,1200) if square else (1800,766)
        c=Canvas(w,h)
        c.rect(75,70,105,10,ORANGE,5)
        c.text(75,111,'WorkBuddy',51,color=GREEN,bold=True)
        c.text(75,207,'技能怎么选？',93 if square else 105,bold=True)
        c.text(75,347,'按工作来挑',77 if square else 88,bold=True)
        c.text(75,h-85,'可以叫我才哥',34,color=GREEN)
        bx,by=(185,580) if square else (1060,200)
        for i,(label,col) in enumerate([('文档',GREEN),('表格','#498C72'),('配图',ORANGE)]):
            x=bx+i*145;c.rect(x,by,125,225,'#FFFFFF',18,stroke='#DADFD5');c.rect(x+20,by+25,85,16,col,6)
            c.text(x+22,by+83,label,37,color=col,bold=True)
            for yy in [by+145,by+177]:c.line(x+23,yy,x+100,yy,'#DADFD5',5)
        c.rect(bx-40,by+207,550,188,GREEN,24)
        c.rect(bx+190,by+245,100,25,ORANGE,8)
        c.save('封面_方版模板' if square else '封面_横版模板')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--font',default='C:/Windows/Fonts/msyh.ttc');args=ap.parse_args()
    FONT=args.font
    if not Path(FONT).exists():raise SystemExit('请通过 --font 指定本机中文字体文件')
    make()
    print('已生成 7 张选型图、2 份封面模板；每份均含 PNG 与可编辑 SVG。')
