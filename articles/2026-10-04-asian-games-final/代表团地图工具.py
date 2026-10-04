"""按官方代表团代码连接真实地图边界；小地区另加定位圆点。"""
import json
import pandas as pd
from matplotlib.colors import ListedColormap, BoundaryNorm
from 图表工具 import D, plt, albers, map_features, draw_feature, map_view

COLORS = ['#FFFBEA', '#FEE5AD', '#FDBE68', '#F28A43', '#DB5039', '#A91F32', '#711D35']
BOUNDS = [0, 1, 5, 10, 20, 40, 80, 170]
LABELS = ['0', '1—4', '5—9', '10—19', '20—39', '40—79', '80—169']
CMAP = ListedColormap(COLORS)
NORM = BoundaryNorm(BOUNDS, CMAP.N)

def mapping():
    medals = pd.read_csv(D / '国家地区奖牌榜.csv')
    keys = pd.read_csv(D / '代表团地图映射.csv')
    result = keys.merge(medals[['noc', 'name_zh', 'gold']], on='noc',
                        how='outer', validate='one_to_one', indicator=True)
    assert result['_merge'].eq('both').all(), '代表团与地图映射必须完整匹配'
    assert result.gold.notna().all() and result.gold.sum() == 470
    return result.drop(columns='_merge').set_index('noc')

def draw_delegations(ax, data):
    world = json.loads((D / '世界边界.geojson').read_text(encoding='utf-8'))['features']
    names = {f['properties']['name']: f for f in world if f['properties']['name']}
    # 灰色只用于非本届参赛范围的背景；0金牌有独立的浅黄色。
    for feature in world:
        if feature['properties']['name'] != 'China':
            draw_feature(ax, feature, '#E4E9EE', edge='#FFFFFF', lw=.45)
    provincial = map_features()
    special = {710000: 'TPE', 810000: 'HKG', 820000: 'MAC'}
    for feature in provincial:
        code = feature['properties']['adcode']
        noc = special.get(code, 'CHN')
        color = CMAP(NORM(data.loc[noc, 'gold']))
        draw_feature(ax, feature, color, edge=color, lw=.12)
    for noc, row in data.iterrows():
        if row.geometry_type == 'world_polygon':
            assert row.world_name in names, (noc, row.world_name)
            draw_feature(ax, names[row.world_name], CMAP(NORM(row.gold)), lw=.55)
    # 圆点强调小面积地区和群岛国位置，不编码面积或奖牌数量。
    for noc in ['HKG', 'MAC', 'SGP', 'BRN', 'QAT', 'MDV']:
        row = data.loc[noc]
        x, y = albers([[row.longitude, row.latitude]])[0]
        ax.scatter(x, y, s=45, color=CMAP(NORM(row.gold)), edgecolor='#21374A', linewidth=.7, zorder=5)
    map_view(ax, (28, -12), (153, 62))
