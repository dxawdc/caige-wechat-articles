from matplotlib.patches import Patch
from 图表工具 import plt, albers, map_features, finish
from 代表团地图工具 import mapping, draw_delegations, CMAP, NORM, COLORS, LABELS

data = mapping()  # 显式使用NOC代码映射，不把它当作ISO国家代码。
fig = plt.figure(figsize=(12, 9))
ax = fig.add_axes([.02, .24, .96, .60])
draw_delegations(ax, data)

# 只给重点代表团标注数值，完整数据保留在CSV和前面的榜单中。
positions = {'CHN': (104, 35), 'JPN': (140, 39), 'KOR': (130, 34),
             'PRK': (130, 44), 'IND': (79, 23), 'UZB': (63, 40),
             'IRI': (53, 32), 'THA': (101, 16), 'KAZ': (68, 49),
             'MAS': (112, 4), 'INA': (116, -5), 'PHI': (125, 14)}
for noc, location in positions.items():
    row = data.loc[noc]
    x, y = albers([location])[0]
    ax.text(x, y, f'{row.name_zh}\n{int(row.gold)}', ha='center', va='center',
            fontsize=11, color='#263849', zorder=6,
            bbox=dict(facecolor='white', edgecolor='none', alpha=.86, pad=2))

# 港澳台直接标在地图上：用引导线连接真实位置，错开相邻标签。
centers = {f['properties']['adcode']:
           f['properties'].get('centroid') or f['properties'].get('center')
           for f in map_features()}
callouts = {'HKG': (810000, (146, 24)),
            'MAC': (820000, (144, 18)),
            'TPE': (710000, (148, 30))}
for noc, (adcode, label_position) in callouts.items():
    row = data.loc[noc]
    anchor = albers([centers[adcode]])[0]
    label = albers([label_position])[0]
    ax.annotate(f'{row.name_zh}\n{int(row.gold)}金', xy=anchor, xytext=label,
                ha='center', va='center', fontsize=12, weight='bold',
                color='#263849', zorder=8,
                bbox=dict(facecolor='white', edgecolor='none', alpha=.94, pad=3),
                arrowprops=dict(arrowstyle='-', color='#526675', lw=1.1))

small = ['HKG', 'TPE', 'MAC', 'SGP', 'BRN', 'QAT', 'MDV']
for i, noc in enumerate(small):
    row = data.loc[noc]
    x = .08 + i * .14
    fig.text(x, .185, row.name_zh, ha='center', fontsize=10, color='#607482')
    fig.text(x, .145, str(int(row.gold)), ha='center', fontsize=18, weight='bold')
fig.legend(handles=[Patch(facecolor=c, label=t) for c, t in zip(COLORS, LABELS)],
           loc='lower center', bbox_to_anchor=(.5, .065), ncol=7,
           frameon=False, fontsize=11, title='代表团金牌数（分级色阶）')
fig.text(.04, .94, '亚运会金牌，分布在哪里？', fontsize=27, weight='bold')
fig.text(.04, .895, '国家或地区代表团金牌地图 · 中国169，日本83，韩国39', fontsize=14)
fig.text(.04, .045, '圆点：小面积地区或群岛国位置；灰色：非本届参赛背景。亚洲难民队0金，无对应地域。', fontsize=9)
finish(fig, '07_代表团金牌地图', '赛事官方奖牌榜 · ECharts / DataV边界 · Google定位数据 · 制图示例')
