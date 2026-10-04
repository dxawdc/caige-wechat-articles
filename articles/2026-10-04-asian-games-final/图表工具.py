"""统一字体、配色、导出及球面 Albers 等积投影。"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch

ROOT = Path(__file__).resolve().parent
D = ROOT / '数据'
OUT = ROOT / '配图'
OUT.mkdir(exist_ok=True)
GOLD, SILVER, BRONZE = '#E7AD35', '#A8B7C9', '#B87854'
BLUE, RED, INK = '#247DA5', '#C7413D', '#21374A'
for candidate in ['Microsoft YaHei', 'Noto Sans CJK SC', 'SimHei']:
    if any(f.name == candidate for f in font_manager.fontManager.ttflist):
        plt.rcParams['font.family'] = candidate
        break
plt.rcParams.update({'axes.unicode_minus':False, 'font.size':13,
    'axes.spines.top':False, 'axes.spines.right':False,
    'axes.labelcolor':INK, 'text.color':INK, 'svg.fonttype':'path',
    'figure.facecolor':'#FFFFFF', 'axes.facecolor':'#FFFFFF'})

def finish(fig, name, note):
    fig.text(.04,.027,note,fontsize=9,color='#697C8A')
    fig.text(.96,.027,'可以叫我才哥',ha='right',fontsize=9,color='#697C8A')
    for ext in ['png','svg']:
        fig.savefig(OUT/f'{name}.{ext}',dpi=180,facecolor=fig.get_facecolor())
    plt.close(fig)

def albers(points):
    """经纬度 -> 球面 Albers 千米坐标；标准纬线25°/47°，中央经线105°。"""
    lon,lat=np.asarray(points,dtype=float).T[:2]
    p1,p2=np.deg2rad([25,47])
    n=(np.sin(p1)+np.sin(p2))/2
    c=np.cos(p1)**2+2*n*np.sin(p1)
    rho=6371*np.sqrt(c-2*n*np.sin(np.deg2rad(lat)))/n
    rho0=6371*np.sqrt(c)/n
    theta=n*np.deg2rad(lon-105)
    return np.column_stack((rho*np.sin(theta),rho0-rho*np.cos(theta)))

def map_features():
    return json.loads((D/'中国省级边界.geojson').read_text(encoding='utf-8'))['features']

def draw_feature(ax, feature, color, edge='#FFFFFF', lw=.7):
    geometry=feature['geometry']
    polygons=geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
    for polygon in polygons:
        # 外环逆时针，内环顺时针，保留孔洞；每个环分别关闭。
        vertices=[]; codes=[]
        for i,ring in enumerate(polygon):
            xy=albers(ring)
            area=np.sum(xy[:-1,0]*xy[1:,1]-xy[1:,0]*xy[:-1,1])
            if (area>0)!=(i==0):xy=xy[::-1]
            vertices.extend(xy)
            codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(xy)-2)+[MPath.CLOSEPOLY])
        ax.add_patch(PathPatch(MPath(vertices,codes),facecolor=color,edgecolor=edge,lw=lw))

def map_view(ax, southwest=(73,18), northeast=(136,54)):
    # 以完整外接范围设置投影后的视野，避免裁掉东北、西藏和南部岛屿。
    lon=np.linspace(southwest[0],northeast[0],100)
    lat=np.linspace(southwest[1],northeast[1],100)
    corners=np.vstack([np.column_stack([lon,np.full(100,lat[0])]),
        np.column_stack([lon,np.full(100,lat[-1])]),
        np.column_stack([np.full(100,lon[0]),lat]),
        np.column_stack([np.full(100,lon[-1]),lat])])
    xy=albers(corners)
    ax.set_xlim(xy[:,0].min(),xy[:,0].max())
    ax.set_ylim(xy[:,1].min(),xy[:,1].max())
    ax.set_aspect('equal'); ax.set_axis_off()
