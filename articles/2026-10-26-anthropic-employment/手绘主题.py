"""方格笔记纸、钢笔字与彩铅排线；数据坐标和柱形端点保持原值。"""
import re
import numpy as np
from matplotlib import colors as mc
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import matplotlib.patheffects as pe

PAPER='#FFFCF2'
INK='#303D4B'
BLUE='#356798'
ORANGE='#B9683D'
MUTED='#627380'
RULE='#C5D9E3'
AVAILABLE={f.name for f in fm.fontManager.ttflist}
HAND=next((f for f in ['KaiTi','STKaiti','LXGW WenKai','Noto Sans CJK SC','Microsoft YaHei'] if f in AVAILABLE),'sans-serif')
DIGITS='Comic Sans MS' if 'Comic Sans MS' in AVAILABLE else HAND

def line(ax, xs, ys, color=INK, lw=1.6, **kw):
    artist,=ax.plot(xs,ys,color=color,lw=lw,**kw)
    artist.set_sketch_params(scale=1.1,length=145,randomness=2.2)
    return artist

def paper(ax,w,h):
    ax._handdrawn=True
    # Decorative notebook ruling is much lighter than the quantitative axes.
    for x in np.arange(42,w,38):
        ax.plot([x,x],[0,h],color=RULE,lw=.45,alpha=.35,zorder=-5)
    for y in np.arange(24,h,38):
        ax.plot([0,w],[y,y],color=RULE,lw=.45,alpha=.35,zorder=-5)
    ax.plot([35,35],[0,h],color='#D78A7B',lw=.85,alpha=.42,zorder=-4)
    # One little ink asterisk makes the page read as a notebook, not a dashboard.
    cx,cy=w-65,65
    for angle in [0,np.pi/3,2*np.pi/3]:
        line(ax,[cx-13*np.cos(angle),cx+13*np.cos(angle)],
             [cy-13*np.sin(angle),cy+13*np.sin(angle)],ORANGE,1.8,zorder=2)

def text(ax,x,y,value,size,color,weight,**kw):
    enabled=getattr(ax,'_handdrawn',False)
    family=[DIGITS,HAND] if enabled else ['Microsoft YaHei','sans-serif']
    if enabled:
        color=MUTED if color=='#667474' else color
        # Increase small descriptive labels, while keeping title and numeric hierarchy.
        if 22<=size<=30: size+=2
    artist=ax.text(x,y,value,fontsize=size,color=color,weight='normal' if enabled else weight,va='center',fontfamily=family,**kw)
    if enabled and weight=='bold':
        artist.set_path_effects([pe.withStroke(linewidth=.65,foreground=color)])
    if enabled and y<=90 and x<=90:
        width=min(len(value)*size*.9,ax.get_xlim()[1]-150)
        accent=line(ax,[x+1,x+width],[y+33,y+31],'#D8B346',6,alpha=.5,zorder=0)
        accent.set_sketch_params(scale=2,length=240,randomness=1.7)
    if enabled and size>=32 and re.fullmatch(r'[+−\-]?\d+(?:\.\d+)?(?:%|倍|∶1)',value):
        artist.set_bbox(dict(boxstyle='round,pad=.10,rounding_size=.32',facecolor=PAPER,edgecolor=color,linewidth=.9))
        artist.get_bbox_patch().set_sketch_params(scale=1.4,length=180,randomness=2)
    return artist

def pencil_bar(ax,patch,seed):
    color=mc.to_rgb(patch.get_facecolor())
    x,y=patch.get_xy(); w,h=patch.get_width(),patch.get_height()
    # The fill outline and endpoints remain tied to exact data coordinates.
    wash=tuple(.78*np.array(mc.to_rgb(PAPER))+.22*np.array(color))
    patch.set_facecolor(wash)
    patch.set_edgecolor(color)
    patch.set_linewidth(1.2)
    patch.set_sketch_params(scale=.8,length=160,randomness=1.6)
    rng=np.random.default_rng(seed)
    segments=[]
    for sx in np.arange(x-h,x+w+6,6.5):
        jitter=rng.uniform(-1.5,1.5)
        dx=h*.7+jitter
        lo=max(0,(x-sx)/dx)
        hi=min(1,(x+w-sx)/dx)
        if lo<hi:
            segments.append([(sx+lo*dx,y+h-lo*h),(sx+hi*dx,y+h-hi*h)])
    strokes=LineCollection(segments,colors=[color],linewidths=.9,alpha=.5,zorder=patch.get_zorder()+.1)
    strokes.set_clip_path(Rectangle((x,y),w,h,transform=ax.transData))
    strokes.set_sketch_params(scale=.5,length=180,randomness=1.8)
    ax.add_collection(strokes)

def finish(ax):
    if not getattr(ax,'_handdrawn',False): return
    for i,patch in enumerate(list(ax.patches)):
        if isinstance(patch,Rectangle) and not isinstance(patch,FancyBboxPatch):
            hex_color=mc.to_hex(patch.get_facecolor())
            if hex_color.lower() in ['#ece9e2','#e3e0d8']:
                patch.set_visible(False)
            elif patch.get_width()>0 and patch.get_height()>0 and patch.get_facecolor()[3]>0:
                pencil_bar(ax,patch,1026+i)
        elif isinstance(patch,FancyBboxPatch):
            patch.set_facecolor('#FFFDF6')
            patch.set_edgecolor(INK)
            patch.set_linewidth(1.25)
            patch.set_sketch_params(scale=1.6,length=180,randomness=2.5)
        elif isinstance(patch,Circle):
            patch.set_sketch_params(scale=1.1,length=160,randomness=2.2)
    for artist in ax.lines:
        if artist.get_zorder()>=0:
            artist.set_sketch_params(scale=1.05,length=160,randomness=2.2)
