"""v1.0.0 | 2026-09-15 | 原创讲解示意图；不修改或伪造软件截图。依赖 Pillow。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).parent
OUT = R / '图片_v1.0.0'
OUT.mkdir(exist_ok=True)
NAVY, TEAL, INK, MUTED = '#152C3D', '#147D82', '#213F50', '#6F8591'
BG, LINE = '#F2F7F6', '#DCE8E7'
def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('msyhbd.ttc' if bold else 'msyh.ttc'), size)
def canvas(h, title, tag):
    im = Image.new('RGB', (1600,h), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,1600,20), fill=TEAL)
    d.text((80,65),'可以叫我才哥  /  BROWSERSKILL',font=font(25,True),fill=TEAL)
    d.text((80,125),title,font=font(54,True),fill=INK)
    d.text((80,210),tag,font=font(26),fill=MUTED)
    d.text((80,h-70),'BrowserSkill 实操分享 · v1.0.0 · 2026.09.15',font=font(23),fill=MUTED)
    return im,d
def card(d,box,number,title,lines):
    x,y,x2,y2=box
    d.rounded_rectangle(box,22,fill='white',outline=LINE,width=2)
    d.rounded_rectangle((x+30,y+30,x+98,y+98),15,fill='#E4F2EF')
    d.text((x+42,y+40),number,font=font(32,True),fill=TEAL)
    d.text((x+30,y+130),title,font=font(37,True),fill=INK)
    for i,line in enumerate(lines):d.text((x+30,y+195+i*43),line,font=font(26),fill=MUTED)
def save(im,name):im.save(OUT/name,optimize=True)

im,d=canvas(1000,'把一句任务，变成可核对的结果','安装三件套  /  8 类使用场景  /  真实浏览器演示')
for x,n,title,lines in [(80,'01','告诉 AI 目标',['在哪个页面做什么','输出文件与完成标准']),
                        (570,'02','在浏览器里操作',['观察、填写、筛选','必要时交给人接手']),
                        (1060,'03','留下结果证据',['截图 + 快照 + CSV','核对页面与输出一致'])]:
    card(d,(x,310,x+460,675),n,title,lines)
d.rounded_rectangle((80,730,1520,870),20,fill=NAVY)
d.text((120,760),'本篇演示：12 条资料 → 4 条 Python 资料 → 36 分钟',font=font(37,True),fill='white')
d.text((120,815),'虚构资料 · 筛选使用兼容处理 · 数据结果已核对',font=font(25),fill='#A8C8CE')
save(im,'00_文章导览_v1.0.0.png')

im,d=canvas(1220,'安装时，别漏掉这三部分','Skill 是操作说明；CLI 和浏览器扩展负责把操作接起来。')
for y,n,title,lines in [(300,'1','Skill：让 Agent 知道怎么用',['执行 bsk install-skill，安装后新开 Agent 对话']),
                       (495,'2','bsk：在电脑上接收与转发命令',['安装 CLI；需要的本地后台服务由工具自动启动']),
                       (690,'3','扩展：在 Chrome / Edge 中执行',['从对应浏览器商店安装，打开弹窗查看连接状态'])]:
    d.rounded_rectangle((80,y,1520,y+165),20,fill='white',outline=LINE,width=2)
    d.ellipse((112,y+43,190,y+121),fill=TEAL)
    d.text((136,y+51),n,font=font(41,True),fill='white')
    d.text((225,y+26),title,font=font(37,True),fill=INK)
    d.text((225,y+91),lines[0],font=font(28),fill=MUTED)
d.rounded_rectangle((80,915,1520,1080),20,fill=NAVY)
d.text((125,946),'Agent → bsk / 本地服务 → 扩展 → Agent Window',font=font(34,True),fill='white')
d.text((125,1012),'使用当前浏览器配置的登录状态；已有用户标签页需要明确借用。',font=font(26),fill='#B3D1D6')
save(im,'01_安装与原理_v1.0.0.png')

im,d=canvas(1130,'连接检查：这台电脑的实测状态','以下为实际输出摘要，已移除本机路径、进程与浏览器标识。')
items=[('CLI / 扩展版本','0.2.1 / 0.2.1','版本已核对'),('本地服务运行','OK','bsk doctor'),
       ('服务通信协议','1.1 · 兼容','bsk doctor'),('浏览器扩展连接','1 个浏览器 · OK','bsk doctor'),
       ('浏览器通信协议','兼容 · OK','bsk doctor')]
for i,(a,b,c) in enumerate(items):
    y=305+i*113
    d.rounded_rectangle((80,y,1520,y+95),16,fill='white')
    d.text((115,y+24),a,font=font(29,True),fill=INK)
    d.text((625,y+24),b,font=font(29,True),fill=TEAL)
    d.text((1240,y+28),c,font=font(23),fill=MUTED)
d.text((85,927),'说明：本机原有手工放置的 Skill；受管安装检测显示 N/A。',font=font(28),fill=INK)
d.text((85,977),'运行连接正常，仍需另行确认 Agent 对话能读取到技能。',font=font(28),fill=MUTED)
save(im,'02_连接检查_v1.0.0.png')

im=Image.new('RGB',(1800,765),NAVY);d=ImageDraw.Draw(im)
for i in range(5):
    x=1160+i*75;d.rounded_rectangle((x,105+i*32,x+385,500+i*32),28,outline='#244B5B',width=3)
d.rounded_rectangle((90,94,500,150),18,fill=TEAL)
d.text((118,102),'可以叫我才哥 · 工具实操',font=font(28,True),fill='white')
d.text((90,215),'让 AI 用上',font=font(100,True),fill='white')
d.text((90,347),'我的浏览器',font=font(100,True),fill='white')
d.text((98,527),'BrowserSkill 安装与实操',font=font(45,True),fill='#8ED1CA')
d.text((98,618),'资料整理 / 表单填写 / 手机布局 / 真实体验',font=font(29),fill='#BAD1D9')
d.rounded_rectangle((1250,235,1650,520),24,fill='#F0F6F4')
d.rounded_rectangle((1280,264,1620,312),10,fill='#CFE5E0')
for i,w in enumerate([270,210,250]):d.rounded_rectangle((1285,355+i*43,1285+w,373+i*43),6,fill=['#147D82','#8CB7B7','#B0CECD'][i])
im.save(R/'公众号封面_v1.0.0.png',optimize=True)
print('Created 3 explanatory figures and 1 cover; browser screenshots unchanged.')
