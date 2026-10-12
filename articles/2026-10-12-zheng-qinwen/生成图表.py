"""确定性生成中文信息图及可编辑SVG；所有数值读取冻结数据。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, math, html, os
from datetime import date

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'配图'; OUT.mkdir(exist_ok=True)
D=json.loads((ROOT/'数据/生涯数据.json').read_text(encoding='utf8'))
INK='#202B54'; BLUE='#4457C4'; CORAL='#DB655A'; PURPLE='#9471BE'; GRID='#E4E6F1'; BG='#FAFAFE'; MUTED='#6C7390'
FONT=os.environ.get('CAIGE_FONT','C:/Windows/Fonts/msyh.ttc')
BOLD=os.environ.get('CAIGE_BOLD_FONT','C:/Windows/Fonts/msyhbd.ttc')
S=2
class Canvas:
 def __init__(self,w,h):
  self.w=w;self.h=h;self.im=Image.new('RGB',(w*S,h*S),BG);self.d=ImageDraw.Draw(self.im);self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="{BG}"/>']
 def rect(self,x,y,w,h,fill,stroke=None,sw=1):
  self.d.rectangle((x*S,y*S,(x+w)*S,(y+h)*S),fill=fill,outline=stroke,width=sw*S)
  self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
 def line(self,pts,color=GRID,width=2):
  self.d.line([(x*S,y*S) for x,y in pts],fill=color,width=width*S,joint='curve')
  self.svg.append(f'<polyline points="'+ ' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')
 def circle(self,x,y,r,color,stroke=None,sw=2):
  self.d.ellipse(((x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S),fill=color,outline=stroke,width=sw*S)
  self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="{stroke or "none"}" stroke-width="{sw}"/>')
 def text(self,x,y,s,size=32,color=INK,bold=False,anchor='left'):
  s=str(s);font=ImageFont.truetype(BOLD if bold else FONT,size*S); length=self.d.textlength(s,font=font)/S
  x0=x-(length/2 if anchor=='center' else length if anchor=='right' else 0)
  self.d.text((x0*S,y*S),s,font=font,fill=color,anchor='lt')
  self.svg.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" text-anchor="'+{'left':'start','center':'middle','right':'end'}[anchor]+f'" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{html.escape(s)}</text>')
  assert x0>=-2 and x0+length<=self.w+2, (s,x0,length,self.w)
 def save(self,name):
  self.im.resize((self.w,self.h),Image.Resampling.LANCZOS).save(OUT/(name+'.png'))
  (OUT/(name+'.svg')).write_text('\n'.join(self.svg+['</svg>']),encoding='utf8',newline='\n')

def header(c,num,title,subtitle):
 c.rect(60,48,44,7,CORAL);c.text(124,39,'QINWEN ZHENG  /  CAREER ATLAS',23,BLUE,True)
 c.text(60,99,title,58,INK,True);c.text(60,181,subtitle,27,MUTED)
 c.text(1140,43,num,24,MUTED,anchor='right')
def footer(c,source):
 c.line([(60,c.h-91),(1140,c.h-91)])
 c.text(60,c.h-68,source,21,MUTED)
 c.text(1140,c.h-39,'截至2026.10.12  ·  可以叫我才哥',20,MUTED,anchor='right')
def metric(c,x,y,n,label,color=BLUE):
 c.text(x,y,n,100,color,True);c.text(x,y+124,label,27,MUTED)
def court(c,x,y,w,h,color=BLUE):
 c.rect(x,y,w,h,None,color,3); c.line([(x+w*.13,y),(x+w*.13,y+h)],color,2);c.line([(x+w*.87,y),(x+w*.87,y+h)],color,2)
 c.line([(x,y+h*.5),(x+w,y+h*.5)],color,3)
 c.line([(x+w*.13,y+h*.25),(x+w*.87,y+h*.25)],color,2);c.line([(x+w*.13,y+h*.75),(x+w*.87,y+h*.75)],color,2)
 c.line([(x+w*.5,y+h*.25),(x+w*.5,y+h*.75)],color,2)

def ranks():
 c=Canvas(1200,1550);header(c,'01','排名，记录上升也记录低谷','2018—2025年终排名  /  2026年周排名关键节点')
 metric(c,62,250,'4','生涯最高 · 2025.06.16');metric(c,665,250,'23','最新排名 · 2026.10.12',CORAL)
 c.text(60,460,'年终排名',33,INK,True);c.text(1140,465,'纵轴为对数刻度 · 越高名次越靠前',22,MUTED,anchor='right')
 x0,x1,y0,y1=130,1080,560,900
 def fy(v):return y0+(math.log10(v)-math.log10(3))/(3-math.log10(3))*(y1-y0)
 for v in [5,10,30,100,300,1000]:
  y=fy(v);c.line([(x0,y),(x1,y)]);c.text(105,y-12,v,22,MUTED,anchor='right')
 pts=[(x0+i*(x1-x0)/7,fy(v)) for i,(_,v) in enumerate(D['year_end_rankings'])]
 c.line(pts,BLUE,6)
 for (year,v),(x,y) in zip(D['year_end_rankings'],pts):
  c.circle(x,y,8,BG,BLUE,4);c.text(x,y-44,v,30,BLUE,True,'center');c.text(x,931,year,24,MUTED,anchor='center')
 c.text(60,1010,'2026：从160回到23',34,INK,True);c.text(60,1062,'同一年内的起伏，不能用一个年终数字概括。',26,MUTED)
 rows=D['ranking2026_keypoints'];start=date.fromisoformat(rows[0][0]);end=date.fromisoformat(rows[-1][0]);
 def xx(ds):return 130+(date.fromisoformat(ds)-start).days/(end-start).days*950
 def yy(v):return 1140+(v-1)/179*235
 for v in [1,80,160]:
  y=yy(v);c.line([(130,y),(1080,y)]);c.text(105,y-12,v,22,MUTED,anchor='right')
 pts=[(xx(ds),yy(v)) for ds,v in rows];c.line(pts,CORAL,5)
 for idx,label in [(0,'01.05'),(4,'06.15'),(9,'10.12')]:
  ds,v=rows[idx];x,y=pts[idx];c.circle(x,y,7,CORAL);c.text(x,y-41,v,29,CORAL,True,'center');c.text(x,1390,label,23,MUTED,anchor='center')
 footer(c,'来源：WTA球员排名档案；下图按实际日期间隔绘制。');c.save('01_排名曲线')

def titles():
 c=Canvas(1200,1600);header(c,'02','六次登顶，跨过不同的赛场','WTA官方生涯六冠口径  /  含巴黎奥运女单金牌')
 metric(c,62,245,'6','WTA官方生涯冠军数');metric(c,660,245,'3 : 3','红土 : 硬地',CORAL)
 c.text(60,455,'日期 / 举办地',24,MUTED);c.text(630,455,'级别 / 决赛对手与比分',24,MUTED)
 for i,r in enumerate(D['titles']):
  y=525+i*127;color=CORAL if r['surface']=='红土' else BLUE
  c.circle(81,y+24,12,color)
  if i<5:c.line([(81,y+42),(81,y+113)],GRID,3)
  c.text(116,y-2,r['event'],37,INK,True);c.text(116,y+51,r['date'].replace('-','.')+'  ·  '+r['surface'],23,MUTED)
  c.text(630,y-3,r['level'],29,color,True);c.text(630,y+38,r['opponent'],27,INK)
  c.text(630,y+77,r['score'],26,MUTED);c.line([(115,y+115),(1140,y+115)],GRID,1)
 c.rect(60,1330,1080,113,'#EEEFFA')
 c.text(85,1352,'另列高光：2023杭州亚运会女单金牌',30,INK,True)
 c.text(85,1400,'五站WTA巡回赛冠军 + 一枚奥运金牌；亚运与WTA125另计。',24,MUTED)
 footer(c,'来源：WTA六场决赛报道；亚运冠军由亚洲奥林匹克理事会核验。');c.save('02_冠军年表')

def olympics():
 c=Canvas(1200,1680);header(c,'03','巴黎金牌，是六场胜利连成的路','2024巴黎奥运会女单  /  比分以郑钦文在前')
 metric(c,60,245,'6','连胜夺金');metric(c,650,245,'2','场先丢首盘后逆转',CORAL)
 c.text(60,448,'赢下一盘',24,BLUE,True);c.text(220,448,'输掉一盘',24,CORAL,True)
 c.text(1135,448,'盘比分以独立色块呈现',23,MUTED,anchor='right')
 for i,r in enumerate(D['olympics2024']):
  y=520+i*155;c.circle(88,y+26,25,BLUE if i!=5 else CORAL);c.text(88,y+6,i+1,29,'#FFFFFF',True,'center')
  if i<5:c.line([(88,y+56),(88,y+131)],GRID,4)
  c.text(140,y-5,r['round']+'  /  '+r['opponent'],32,INK,True)
  for j,(a,b) in enumerate(r['sets']):
   x=715+j*134; col=BLUE if a>b else CORAL;c.rect(x,y-6,113,57,col);c.text(x+56.5,y+4,f'{a}–{b}',31,'#FFFFFF',True,'center')
  c.text(140,y+47,r['score'],28,MUTED);c.text(140,y+92,r['note'],26,CORAL if i in [2,3,5] else MUTED)
 c.text(60,1495,'最难的两轮，恰好都发生在半决赛之前。',35,INK,True)
 footer(c,'来源：WTA奥运官方签表与战报；括号为抢七负方小分。');c.save('03_奥运夺冠之路')

def slams():
 c=Canvas(1200,1320);header(c,'04','大满贯，四条进度不同的路','生涯最佳轮次与正赛胜负  /  资格赛不计入')
 metric(c,60,245,'35','大满贯正赛胜场');metric(c,650,245,'1','次进入大满贯决赛',CORAL)
 stages=['一轮','二轮','三轮','16强','八强','四强','决赛','冠军'];xs=[390+i*94 for i in range(8)]
 for x,label in zip(xs,stages):c.text(x,458,label,22,MUTED,anchor='center')
 for i,r in enumerate(D['grand_slam_best']):
  y=535+i*140;col=CORAL if r['surface']=='红土' else PURPLE if r['surface']=='草地' else BLUE
  c.text(60,y-12,r['event'],42,INK,True);c.text(62,y+48,r['surface']+' · '+str(r['wins'])+'胜'+str(r['losses'])+'负',24,MUTED)
  c.line([(xs[0],y+16),(xs[-1],y+16)],GRID,5)
  c.line([(xs[0],y+16),(xs[r['stage']],y+16)],col,7)
  for j,x in enumerate(xs):c.circle(x,y+16,9,col if j<=r['stage'] else BG,col if j<=r['stage'] else GRID,2)
  c.circle(xs[r['stage']],y+16,15,col)
  c.text(390,y+52,r['result']+'  /  '+r['years'],27,col,True)
 c.rect(60,1110,1080,90,'#EEEFFA');c.text(84,1136,'硬地与红土已有深轮次成绩；草地仍有很大提升空间。',29,INK,True)
 footer(c,'来源：WTA球员赛事档案；节点表示比赛轮次，并非胜率。');c.save('04_大满贯进度')

def beijing():
 c=Canvas(1200,1690);header(c,'05','北京这一冠，先熬过四场第三盘','2026中国网球公开赛  /  首个WTA 1000冠军')
 metric(c,60,245,'7','场晋级，走到冠军');metric(c,650,245,'7–5  6–4','决赛击败安德烈娃',CORAL)
 c.text(60,462,'前四轮均进入第三盘，第二轮为对手退赛。',29,INK,True)
 c.text(60,511,'随后连续三场直落两盘，包括最后的决赛。',28,MUTED)
 for i,r in enumerate(D['beijing2026']):
  y=590+i*115;col=CORAL if i<4 else BLUE
  c.text(62,y,r['round'],24,MUTED);c.text(240,y-3,r['opponent'],31,INK,True)
  c.text(240,y+44,r['score'],27,MUTED)
  for j in range(r['sets_played']):
   x=985+j*53;c.rect(x,y+4,34,34,None if r['retirement'] and j==2 else col,col,3)
  c.line([(60,y+94),(1140,y+94)],GRID,1)
 c.rect(60,1423,1080,108,'#EEEFFA')
 c.text(85,1445,'首个1000赛冠军，为奥运金牌之外再添一块拼图。',30,INK,True)
 c.text(85,1492,'RET = 对手退赛；方块表示比赛进入的盘数，空心为未完成盘。',23,MUTED)
 footer(c,'来源：WTA中网决赛前瞻与决赛报道。');c.save('05_中网夺冠之路')

def covers():
 for square in [False,True]:
  w,h=(1200,1200) if square else (1800,766);c=Canvas(w,h)
  if square:
   c.rect(0,0,w,20,CORAL);c.text(84,95,'郑钦文',110,INK,True);c.text(84,238,'冠军之外',110,CORAL,True)
   c.text(90,402,'从巴黎到北京',39,INK);c.text(90,458,'看见起伏与突破',39,INK)
   court(c,680,620,370,470,BLUE);c.circle(350,830,160,PURPLE);c.circle(400,777,95,BG);c.line([(425,910),(577,1090)],BLUE,36)
   c.circle(885,625,56,CORAL);c.line([(125,1080),(580,610),(1030,480)],CORAL,8)
   c.text(88,1120,'TENNIS  /  CAREER ATLAS',24,MUTED)
  else:
   c.rect(0,0,1800,16,CORAL);c.text(112,122,'郑钦文',132,INK,True);c.text(112,292,'冠军之外',132,CORAL,True)
   c.text(120,525,'从巴黎到北京，看见起伏与突破',44,INK)
   court(c,1250,100,390,580,BLUE);c.circle(1275,290,85,CORAL);c.circle(1100,405,135,PURPLE);c.circle(1110,400,89,BG);c.line([(1150,510),(1260,676)],BLUE,25)
   c.text(120,680,'TENNIS  /  CAREER ATLAS',26,MUTED)
  c.save('封面_方版' if square else '封面_横版模板')

if __name__=='__main__':
 ranks();titles();olympics();slams();beijing();covers()
 print('Created 5 charts and 2 editable covers (PNG + SVG).')
