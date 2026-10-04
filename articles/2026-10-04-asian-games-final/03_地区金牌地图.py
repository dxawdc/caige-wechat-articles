import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Patch
from 图表工具 import D, plt, albers, map_features, draw_feature, map_view, finish

df = pd.read_csv(D / '地区奖牌底表.csv').set_index('adcode')
features = map_features()
norm = Normalize(vmin=0, vmax=df.gold.max())
cmap = plt.get_cmap('YlOrRd')
fig = plt.figure(figsize=(10, 9))
ax = fig.add_axes([.02, .22, .96, .61])
for feature in features:
    code = feature['properties']['adcode']
    value = df.loc[code, 'gold'] if code in df.index else float('nan')
    color = '#D9E1E8' if pd.isna(value) else cmap(norm(value))
    draw_feature(ax, feature, color, edge='#82929E', lw=.45)
    if code in df.index and pd.notna(value):
        center = feature['properties'].get('centroid') or feature['properties']['center']
        x, y = albers([center])[0]
        if code not in [810000, 820000]:
            ax.text(x, y, f'{df.loc[code,"region"]}\n{int(value)}',
                    ha='center', va='center', fontsize=11,
                    color='white' if value >= 25 else '#283746')
map_view(ax)
# 南海及港澳放大图均使用同一份真实 GeoJSON、相同色阶。
for rect, sw, ne, title in [([.76,.245,.2,.21],(105,3),(125,24),'南海'),
                            ([.07,.23,.2,.15],(113.4,22.05),(114.55,22.65),'港澳放大')]:
    inset = fig.add_axes(rect)
    inset.set_facecolor('#F5F8FA')
    for feature in features:
        code=feature['properties']['adcode']
        value=df.loc[code,'gold'] if code in df.index else float('nan')
        draw_feature(inset,feature,'#D9E1E8' if pd.isna(value) else cmap(norm(value)),edge='#82929E',lw=.4)
    map_view(inset,sw,ne)
    inset.set_title(title,fontsize=10)
    if title=='港澳放大':
        for code in [810000,820000]:
            f=next(f for f in features if f['properties']['adcode']==code)
            x,y=albers([f['properties']['center']])[0]
            inset.annotate(f'{df.loc[code,"region"]} {int(df.loc[code,"gold"])}',(x,y),
                           xytext=(0,-13 if code==820000 else 12),textcoords='offset points',
                           ha='center',fontsize=9)
bar = fig.add_axes([.3,.18,.4,.02])
fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=bar,orientation='horizontal',label='金牌数 / 地方金牌项目贡献')
fig.legend(handles=[Patch(facecolor='#D9E1E8',label='暂无数据')],loc='lower center',bbox_to_anchor=(.5,.085),frameon=False,fontsize=11)
fig.text(.05,.94,'地区金牌分布',fontsize=25,weight='bold')
fig.text(.05,.89,'内地：注册/培养项目贡献；港澳台：独立代表团金牌数',fontsize=13)
fig.text(.05,.065,'内地：注册/培养贡献；港澳台：各代表团奖牌数。色阶相同，统计口径分开说明。',fontsize=10)
finish(fig,'03_地区金牌地图','DataV公开GeoJSON · 球面Albers等积投影 · 制图示例')
