"""v1.0.0 | 2026-09-06 | 生成 36 个可单独运行的脚本及文章素材。"""
from pathlib import Path
import json
import os
import runpy
import textwrap
import sys

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / '代码'
CHARTS = []

def add(name, group, intro, caution, comparison, mpl, plotly):
    CHARTS.append(dict(id=len(CHARTS)+1, name=name, group=group, intro=intro,
                       caution=caution, comparison=comparison,
                       mpl=textwrap.dedent(mpl).strip(), plotly=textwrap.dedent(plotly).strip()))

add('折线图', '趋势',
    '看一个指标如何随时间变化。这里把 12 个月的订单连起来，适合观察趋势、拐点和季节性。',
    '时间顺序不能打乱；缺失月份应留空或解释，不能直接连线假装连续。',
    '两边都是一条线加数据点。Matplotlib 的静态报告很直接，Plotly 的 HTML 可以悬停查看月份和订单。',
    r'''
    mfig, ax = new_m('月度订单趋势', '月份', '订单数（笔）')
    ax.plot(months, orders, marker='o', color=BLUE, linewidth=2)
    ax.set(xticks=months, xlim=(.5, 12.5), ylim=(0, 320))
    ''', r'''
    pfig = new_p('月度订单趋势', '月份', '订单数（笔）')
    pfig.add_trace(go.Scatter(x=months, y=orders, mode='lines+markers', line_color=BLUE))
    pfig.update_xaxes(dtick=1, range=[.5, 12.5])
    pfig.update_yaxes(range=[0, 320])
    ''')

add('阶梯图', '趋势',
    '价格档位、库存状态、会员等级这类数值，常常在某一时点跳变，其余时间保持不变。阶梯图能把这个过程说清楚。',
    '先约定变化发生在区间开始还是结束。这里采用后置阶梯：本月值一直保持到下一个月。',
    'Matplotlib 的 where="post" 对应本例 Plotly 的 line_shape="hv"。方向没对齐，图看起来相似，含义却会错开。',
    r'''
    mfig, ax = new_m('月度配置容量', '月份', '容量（个）')
    ax.step(months, orders, where='post', color=BLUE, linewidth=2)
    ax.plot(months, orders, 'o', color=BLUE)
    ax.set(xticks=months, xlim=(.5, 12.5), ylim=(0, 320))
    ''', r'''
    pfig = new_p('月度配置容量', '月份', '容量（个）')
    pfig.add_trace(go.Scatter(x=months, y=orders, mode='lines+markers',
                             line_shape='hv', line_color=BLUE))
    pfig.update_xaxes(dtick=1, range=[.5, 12.5])
    pfig.update_yaxes(range=[0, 320])
    ''')

add('面积图', '趋势',
    '在折线下方填充颜色，突出数量随时间的变化。这里仍然使用月度订单，方便和折线图对照。',
    '面积依赖基线判断大小，本例从 0 开始。多个系列互相覆盖时，后面的区域很容易被挡住。',
    'Matplotlib 用 fill_between，Plotly 用 fill="tozeroy"。只有一个系列时，实现都很短。',
    r'''
    mfig, ax = new_m('月度订单规模', '月份', '订单数（笔）')
    ax.fill_between(months, orders, color=BLUE, alpha=.25)
    ax.plot(months, orders, color=BLUE, linewidth=2)
    ax.set(xticks=months, xlim=(1, 12), ylim=(0, 320))
    ''', r'''
    pfig = new_p('月度订单规模', '月份', '订单数（笔）')
    pfig.add_trace(go.Scatter(x=months, y=orders, fill='tozeroy',
                             fillcolor='rgba(50,105,180,.25)', line_color=BLUE))
    pfig.update_xaxes(dtick=1, range=[1, 12])
    pfig.update_yaxes(range=[0, 320])
    ''')

add('堆叠面积图', '趋势',
    '既想看总量，又想知道总量由哪些来源组成，可以把各来源沿时间堆起来。这里三种来源每月相加，刚好等于总订单。',
    '上层区域没有共同的水平基线，不适合精确比较上层系列之间的差距。负值也不宜直接套这个例子。',
    'Matplotlib 一次 stackplot 接收多个系列；Plotly 给多个 Scatter 相同的 stackgroup。顺序一致，堆叠关系才一致。',
    r'''
    mfig, ax = new_m('订单来源随月份变化', '月份', '订单数（笔）')
    ax.stackplot(months, trend_parts, labels=trend_names, colors=COLORS[:3], alpha=.85)
    ax.legend(ncol=3, loc='upper left', fontsize=8)
    ax.set(xticks=months, xlim=(1, 12), ylim=(0, 350))
    ''', r'''
    pfig = new_p('订单来源随月份变化', '月份', '订单数（笔）')
    for label, row, color in zip(trend_names, trend_parts, COLORS):
        pfig.add_trace(go.Scatter(x=months, y=row, name=label,
                                 stackgroup='orders', line_color=color))
    pfig.update_layout(showlegend=True)
    pfig.update_xaxes(dtick=1, range=[1, 12])
    pfig.update_yaxes(range=[0, 350])
    ''')

add('区间带图', '趋势',
    '一条中心线加上下边界，适合同时展示估计值和不确定范围。本例仅设置中心值上下各 20 笔的模拟区间。',
    '这里的色带不是统计推导出的置信区间。真实分析要说明它到底是置信区间、预测区间，还是人为设定的范围。',
    'Matplotlib 直接给上下边界；Plotly 先画下界，再画上界并向前一条线填充，trace 顺序不能反。',
    r'''
    mfig, ax = new_m('订单中心值与模拟区间', '月份', '订单数（笔）')
    ax.fill_between(months, orders-20, orders+20, color=BLUE, alpha=.18, label='模拟范围 ±20')
    ax.plot(months, orders, color=BLUE, linewidth=2, label='中心值')
    ax.legend(loc='upper left', fontsize=8)
    ax.set(xticks=months, xlim=(1, 12), ylim=(0, 340))
    ''', r'''
    pfig = new_p('订单中心值与模拟区间', '月份', '订单数（笔）')
    pfig.add_trace(go.Scatter(x=months, y=orders-20, line_width=0, showlegend=False))
    pfig.add_trace(go.Scatter(x=months, y=orders+20, line_width=0, fill='tonexty',
                             fillcolor='rgba(50,105,180,.18)', name='模拟范围 ±20'))
    pfig.add_trace(go.Scatter(x=months, y=orders, line_color=BLUE, name='中心值'))
    pfig.update_layout(showlegend=True)
    pfig.update_xaxes(dtick=1, range=[1, 12])
    pfig.update_yaxes(range=[0, 340])
    ''')

add('柱状图', '比较',
    '比较不同类别的数量，柱状图通常是第一选择。这里比较四个渠道的订单，柱子长度就是订单多少。',
    '数量柱从 0 起步。类别较多或标签很长时，可以改成下一种条形图。',
    'ax.bar 与 go.Bar 都能直接接收类别和数值。静态输出的主要差异来自默认间距和文字位置，可以显式控制。',
    r'''
    mfig, ax = new_m('各渠道订单', '渠道', '订单数（笔）')
    bars = ax.bar(channels, values, color=BLUE, width=.6)
    ax.bar_label(bars, padding=4)
    ax.set_ylim(0, 500)
    ''', r'''
    pfig = new_p('各渠道订单', '渠道', '订单数（笔）')
    pfig.add_trace(go.Bar(x=channels, y=values, marker_color=BLUE,
                         text=values, textposition='outside', width=.6))
    pfig.update_yaxes(range=[0, 500])
    ''')

add('条形图', '比较',
    '把柱子横过来，长类别名会更好读。渠道排名、产品排行和问卷选项，都很适合这种表达。',
    '排行图通常按数值排序；如果类别本身有业务顺序，就保留那个顺序。本例从上到下按订单递减。',
    'Matplotlib 用 barh 并反转纵轴；Plotly 使用 orientation="h"，再明确类别顺序。',
    r'''
    mfig, ax = new_m('各渠道订单排名', '订单数（笔）', '渠道')
    bars = ax.barh(channels, values, color=BLUE, height=.6)
    ax.bar_label(bars, padding=5)
    ax.invert_yaxis()
    ax.grid(False)
    ax.grid(axis='x', color='#E8ECF2')
    ax.set_xlim(0, 500)
    ''', r'''
    pfig = new_p('各渠道订单排名', '订单数（笔）', '渠道')
    pfig.add_trace(go.Bar(x=values, y=channels, orientation='h', marker_color=BLUE,
                         text=values, textposition='outside', width=.6))
    pfig.update_xaxes(range=[0, 500], showgrid=True)
    pfig.update_yaxes(autorange='reversed', categoryorder='array', categoryarray=channels, showgrid=False)
    ''')

add('分组柱状图', '比较',
    '同一个季度里，把不同渠道的订单并排摆放，可以同时比较季度和渠道。这里使用三季度、四渠道的数据。',
    '系列太多就会挤成一排小牙签。要比较几十个系列时，分面或热力图通常更清楚。',
    'Matplotlib 需要计算每组柱子的横向偏移；Plotly 设置 barmode="group" 会处理分组位置。',
    r'''
    mfig, ax = new_m('季度与渠道订单对比', '季度', '订单数（笔）')
    x = np.arange(3)
    for j, label in enumerate(channels):
        ax.bar(x+(j-1.5)*.18, matrix[:, j], width=.18, color=COLORS[j], label=label)
    ax.set(xticks=x, xticklabels=periods, ylim=(0, 205))
    ax.legend(ncol=4, loc='upper left', fontsize=8)
    ''', r'''
    pfig = new_p('季度与渠道订单对比', '季度', '订单数（笔）')
    for j, label in enumerate(channels):
        pfig.add_trace(go.Bar(x=periods, y=matrix[:, j], name=label, marker_color=COLORS[j]))
    pfig.update_layout(barmode='group', showlegend=True)
    pfig.update_yaxes(range=[0, 205])
    ''')

add('堆叠柱状图', '比较',
    '把同一季度的渠道订单叠起来，看总订单变化，同时保留各渠道的构成。每根柱子的总高度是该季度订单总数。',
    '只有最底层共享基线。要精确比较某个上层渠道，分组柱状图或单独的折线图更合适。',
    'Matplotlib 逐层累计 bottom；Plotly 使用 barmode="stack"。这一步比较的是数量，别混入百分比。',
    r'''
    mfig, ax = new_m('季度订单及来源构成', '季度', '订单数（笔）')
    bottom = np.zeros(3)
    for j, label in enumerate(channels):
        ax.bar(periods, matrix[:, j], bottom=bottom, color=COLORS[j], label=label, width=.6)
        bottom += matrix[:, j]
    ax.legend(ncol=4, loc='upper left', fontsize=8)
    ax.set_ylim(0, 580)
    ''', r'''
    pfig = new_p('季度订单及来源构成', '季度', '订单数（笔）')
    for j, label in enumerate(channels):
        pfig.add_trace(go.Bar(x=periods, y=matrix[:, j], name=label, marker_color=COLORS[j], width=.6))
    pfig.update_layout(barmode='stack', showlegend=True)
    pfig.update_yaxes(range=[0, 580])
    ''')

add('百分比堆叠柱状图', '比较',
    '把每个季度的订单总量都归一到 100%，重点观察渠道结构是否变化。分母是各自季度的全部渠道订单。',
    '100% 堆叠会隐藏总量差异。即便结构相同，两个季度的订单规模也可能差很远。',
    '先在 NumPy 里统一算好百分比，再交给两套库绘图，避免一个按季度、另一个按渠道归一化。',
    r'''
    mfig, ax = new_m('季度渠道占比', '季度', '占本季度订单（%）')
    bottom = np.zeros(3)
    for j, label in enumerate(channels):
        ax.bar(periods, percent[:, j], bottom=bottom, color=COLORS[j], label=label, width=.6)
        for i in range(3):
            ax.text(i, bottom[i]+percent[i,j]/2, f'{percent[i,j]:.1f}%', ha='center', va='center', color='white', fontsize=8)
        bottom += percent[:, j]
    ax.set_ylim(0, 100)
    ax.set_title('季度渠道占比', loc='left', pad=36)
    ax.legend(ncol=4, loc='lower left', bbox_to_anchor=(0, 1.0), fontsize=8)
    ''', r'''
    pfig = new_p('季度渠道占比', '季度', '占本季度订单（%）')
    for j, label in enumerate(channels):
        pfig.add_trace(go.Bar(x=periods, y=percent[:, j], name=label, marker_color=COLORS[j],
                             text=[f'{v:.1f}%' for v in percent[:,j]], textposition='inside', textfont_color='white'))
    pfig.update_layout(barmode='stack', showlegend=True)
    pfig.update_yaxes(range=[0, 100])
    ''')

add('棒棒糖图', '比较',
    '一根细线加一个圆点，也能表达类别数值。在类别不多、想让版面轻一点时，可以作为条形图的替代。',
    '圆点的位置表示数量，圆点大小在这里没有额外含义。线仍然从 0 开始，避免放大差异。',
    '两边都由线段和散点组合而成。Plotly 的多段线用 None 隔开，避免不同类别之间被连起来。',
    r'''
    mfig, ax = new_m('各渠道订单：棒棒糖表达', '订单数（笔）', '渠道')
    y = np.arange(4)
    ax.hlines(y, 0, values, color=BLUE, linewidth=2)
    ax.scatter(values, y, s=70, color=BLUE, zorder=3)
    ax.set(yticks=y, yticklabels=channels, xlim=(0, 500), ylim=(3.5, -.5))
    ax.grid(False)
    ''', r'''
    pfig = new_p('各渠道订单：棒棒糖表达', '订单数（笔）', '渠道')
    xs, ys = [], []
    for i, value in enumerate(values):
        xs += [0, int(value), None]; ys += [i, i, None]
    pfig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', line_color=BLUE))
    pfig.add_trace(go.Scatter(x=values, y=np.arange(4), mode='markers', marker=dict(color=BLUE, size=11)))
    pfig.update_xaxes(range=[0, 500])
    pfig.update_yaxes(tickvals=list(range(4)), ticktext=channels, range=[3.5, -.5], showgrid=False)
    ''')

# 文件中各组的声明位置不影响正式编号。

# 后续注册内容放在文件末尾，编号最终按下方固定清单重新排列。
add('饼图', '构成',
    '看一个整体由哪些部分组成。这里四个渠道相加是全部订单，每个扇区表示一个渠道的占比。',
    '类别要互斥、完整，数值要非负。类别太多或占比接近时，条形图比扇区角度更容易比较。',
    '两边都能直接生成扇区和百分比；显式指定排序、起始角度和方向，避免只是默认设置造成视觉差异。',
    r'''
    mfig, ax = new_m('订单来源占比')
    ax.pie(values, labels=channels, autopct='%.1f%%', startangle=90, counterclock=False,
           colors=COLORS[:4], textprops={'fontsize': 9}, wedgeprops={'edgecolor':'white'})
    ax.set_aspect('equal')
    ''', r'''
    pfig = new_p('订单来源占比')
    pfig.add_trace(go.Pie(labels=channels, values=values, sort=False, direction='clockwise',
                         rotation=0, marker_colors=COLORS[:4], textinfo='label+percent',
                         textposition='inside'))
    ''')

add('环形图', '构成',
    '环形图是中间留空的饼图，适合在中心补充总量。这里中心显示四个渠道合计的订单数。',
    '中心数字必须与扇区分母一致。留空不会让占比比较变得更精确，类别过多的问题仍然存在。',
    'Matplotlib 控制扇区 width；Plotly 控制 hole。中心文字在 Matplotlib 是 text，在 Plotly 是 annotation。',
    r'''
    mfig, ax = new_m('订单来源与总量')
    ax.pie(values, labels=channels, autopct='%.1f%%', pctdistance=.8, startangle=90,
           counterclock=False, colors=COLORS[:4], wedgeprops={'width':.4,'edgecolor':'white'},
           textprops={'fontsize':9})
    ax.text(0, 0, f'{values.sum():,}\n总订单', ha='center', va='center', fontsize=15)
    ax.set_aspect('equal')
    ''', r'''
    pfig = new_p('订单来源与总量')
    pfig.add_trace(go.Pie(labels=channels, values=values, hole=.6, sort=False, direction='clockwise',
                         rotation=0, marker_colors=COLORS[:4], textinfo='label+percent'))
    pfig.add_annotation(x=.5, y=.5, text=f'{values.sum():,}<br>总订单', showarrow=False, font_size=21)
    ''')

add('矩形树图', '构成',
    '用矩形面积表示各部分的量，适合在有限空间里展示构成。本例先用单层渠道预算份额演示，进一步也可以组织层级。',
    '面积适合看大致结构，不适合读出微小差异。本例数值合计为 100，既是模拟份额，也是面积权重。',
    'Plotly 有 Treemap trace；Matplotlib 本例借助 squarify 计算矩形布局。这项额外依赖要算进实现成本。',
    r'''
    mfig, ax = new_m('渠道预算构成（%）')
    squarify.plot(sizes=tree_values, label=[f'{k}\n{v}%' for k,v in zip(tree_labels,tree_values)],
                  color=COLORS, ax=ax, pad=True, text_kwargs={'color':'white','fontsize':11})
    ax.axis('off')
    ''', r'''
    pfig = new_p('渠道预算构成（%）')
    pfig.add_trace(go.Treemap(labels=tree_labels, parents=['']*5, values=tree_values,
                             marker_colors=COLORS, texttemplate='%{label}<br>%{value}%',
                             textfont=dict(color='white', size=18), tiling_pad=3,
                             pathbar_visible=False))
    ''')

add('旭日图', '构成',
    '内圈是父类，外圈是子类，适合看层级构成。这里把渠道分成“付费”和“自有”，再展开五个细分来源。',
    '父节点的数值必须与子节点合计一致。层级过深、标签过长时，圆环很快就会读不清。',
    'Plotly 原生支持父子关系；Matplotlib 本例用两层 pie 手工拼装。两层相同颜色对应同一父类，不是另外增加系列。',
    r'''
    mfig, ax = new_m('渠道预算层级（%）')
    ax.pie([60,40], radius=.65, labels=['付费 60%','自有 40%'], labeldistance=.45,
           startangle=90, counterclock=False, colors=[BLUE,ORANGE],
           wedgeprops={'width':.65,'edgecolor':'white'}, textprops={'color':'white','fontsize':9})
    ax.pie(tree_values, radius=1, labels=[f'{k} {v}%' for k,v in zip(tree_labels,tree_values)],
           labeldistance=1.05, startangle=90, counterclock=False,
           colors=[BLUE,BLUE,ORANGE,ORANGE,ORANGE],
           wedgeprops={'width':.35,'edgecolor':'white'}, textprops={'fontsize':8})
    ax.set_aspect('equal')
    ''', r'''
    pfig = new_p('渠道预算层级（%）')
    pfig.add_trace(go.Sunburst(labels=['付费','自有']+tree_labels,
                             parents=['','','付费','付费','自有','自有','自有'],
                             values=[60,40]+tree_values, branchvalues='total', sort=False,
                             marker_colors=[BLUE,ORANGE,BLUE,BLUE,ORANGE,ORANGE,ORANGE],
                             texttemplate='%{label}<br>%{value}%', insidetextorientation='radial'))
    ''')

add('瀑布图', '构成',
    '从期初到期末，哪些因素让数值增加，哪些让它减少，可以用瀑布图逐项拆开。示例从 100 万元，经四次变动，到 125 万元。',
    '增量与总量要区分。本例橙色表示减少、蓝色表示增加，首尾总量用灰色，不能把期末再当成一个增量相加。',
    'Plotly 的 Waterfall 自带 relative/total 语义；Matplotlib 需要计算每根浮动柱的底部和高度。',
    r'''
    mfig, ax = new_m('期初到期末的金额变化', '项目', '金额（万元）')
    labels = ['期初','新增','退款','复购','成本','期末']
    delta = [30,-15,20,-10]
    level = 100
    ax.bar(0, level, color='#778392', width=.6)
    for i, change in enumerate(delta, 1):
        ax.plot([i-1+.3,i-.3], [level,level], color='#AAB4C0', linewidth=1)
        ax.bar(i, abs(change), bottom=min(level,level+change), color=BLUE if change>0 else ORANGE, width=.6)
        ax.text(i, max(level,level+change)+4, f'{change:+}', ha='center', fontsize=9)
        level += change
    ax.plot([4.3,4.7],[level,level],color='#AAB4C0',linewidth=1)
    ax.bar(5, level, color='#778392', width=.6)
    ax.set(xticks=range(6), xticklabels=labels, ylim=(0,160))
    ''', r'''
    pfig = new_p('期初到期末的金额变化', '项目', '金额（万元）')
    pfig.add_trace(go.Waterfall(x=['期初','新增','退款','复购','成本','期末'],
                              y=[100,30,-15,20,-10,0], measure=['absolute']+['relative']*4+['total'],
                              text=['100','+30','-15','+20','-10','125'], textposition='outside',
                              increasing_marker_color=BLUE, decreasing_marker_color=ORANGE,
                              totals_marker_color='#778392', connector_line_color='#AAB4C0'))
    pfig.update_yaxes(range=[0,160])
    ''')

add('漏斗图', '构成',
    '看同一批用户经过各步骤后还剩多少。示例从 10000 名访问用户开始，最后有 1500 名支付用户，整体转化率为 15%。',
    '要有同一批对象、同一时间窗和明确的步骤顺序。不同来源、不同统计期的数量直接拼在一起，不等于转化漏斗。',
    'Plotly 有 Funnel trace，并能展示相对首步的百分比；Matplotlib 用居中的横条实现。本例两边都以首步为分母。',
    r'''
    mfig, ax = new_m('同批用户的转化漏斗', '人数（人）', '')
    y = np.arange(5)
    ax.barh(y, funnel_values, left=-funnel_values/2, color=BLUE, height=.7)
    for i,v in enumerate(funnel_values):
        ax.text(0,i,f'{v:,} / {v/funnel_values[0]:.0%}',ha='center',va='center',color='white',fontsize=8)
    ax.set(yticks=y, yticklabels=funnel_names, xlim=(-5500,5500), ylim=(4.6,-.6))
    ax.set_xticks([])
    ax.set_xlabel('条宽表示人数；百分比以首步为分母')
    ax.grid(False)
    ''', r'''
    pfig = new_p('同批用户的转化漏斗')
    pfig.add_trace(go.Funnel(y=funnel_names, x=funnel_values, marker_color=BLUE,
                            textinfo='value+percent initial', textposition='inside',
                            textfont=dict(color='white',size=13), connector=dict(line_width=0,fillcolor='rgba(0,0,0,0)')))
    pfig.update_layout(margin_l=115)
    pfig.update_xaxes(showticklabels=False, title='条宽表示人数；百分比以首步为分母')
    ''')

add('直方图', '分布',
    '看一组数值主要集中在哪个区间，有没有偏斜或长尾。这里统计 160 个样本的使用时长，每 5 分钟分一箱。',
    '分箱宽度不同，形状就可能不同。本例先用同一组边界计算频数，再交给两套库；最后一个箱包含右端点。',
    '为锁定统计口径，这里画的是“同一份预计算频数”，而不是让两边各自自动分箱。真正的区别在呈现和交互。',
    r'''
    mfig, ax = new_m('使用时长分布：每箱 5 分钟', '使用时长（分钟）', '样本数（个）')
    ax.bar(bins[:-1], hist_counts, width=np.diff(bins), align='edge', color=BLUE, edgecolor='white')
    ax.set(xlim=(0,80), ylim=(0,55))
    ''', r'''
    pfig = new_p('使用时长分布：每箱 5 分钟', '使用时长（分钟）', '样本数（个）')
    pfig.add_trace(go.Bar(x=(bins[:-1]+bins[1:])/2, y=hist_counts,
                         width=np.diff(bins), marker=dict(color=BLUE,line=dict(color='white',width=1))))
    pfig.update_xaxes(range=[0,80])
    pfig.update_yaxes(range=[0,55])
    ''')

add('核密度图', '分布',
    '把一组样本平滑成一条分布曲线，适合观察峰的位置和分布形状。纵轴是概率密度，不是人数，也不是某个点的概率。',
    '带宽控制平滑程度。这里统一使用 SciPy gaussian_kde，bw_method=0.3；有限横轴可能截去极小的尾部面积。',
    '密度估计只做一次，两套库都画同一个网格上的结果。这样不会把统计算法的差别误认为绘图库的差别。',
    r'''
    mfig, ax = new_m('使用时长的核密度估计', '使用时长（分钟）', '概率密度（1/分钟）')
    ax.plot(density_grid, density, color=BLUE, linewidth=2)
    ax.fill_between(density_grid, density, color=BLUE, alpha=.2)
    ax.set(xlim=(0,80), ylim=(0,.065))
    ''', r'''
    pfig = new_p('使用时长的核密度估计', '使用时长（分钟）', '概率密度（1/分钟）')
    pfig.add_trace(go.Scatter(x=density_grid, y=density, line_color=BLUE,
                             fill='tozeroy', fillcolor='rgba(50,105,180,.2)'))
    pfig.update_xaxes(range=[0,80])
    pfig.update_yaxes(range=[0,.065])
    ''')

add('箱线图', '分布',
    '用中位数、四分位数和须，概括多组数值的分布。本例比较三种方案的使用时长，每组各 160 个样本。',
    '须不一定是最小值和最大值。本例须落在 1.5×IQR 范围内最远的观测值，之外单独标点；这些点也不自动等于错误数据。',
    '四分位数统一用 NumPy 的 linear 方法预计算。Matplotlib 的 bxp 和 Plotly 的预计算 Box 共用结果，避免默认算法差异。',
    r'''
    mfig, ax = new_m('三种方案的使用时长：箱线图', '方案', '使用时长（分钟）')
    ax.bxp(box_stats, positions=[0,1,2], widths=.5, patch_artist=True,
           boxprops={'facecolor':'#D6E3F4','edgecolor':BLUE}, medianprops={'color':BLUE,'linewidth':2},
           whiskerprops={'color':BLUE}, capprops={'color':BLUE}, flierprops={'marker': 'o','markersize':4})
    ax.set_ylim(0,85)
    ''', r'''
    pfig = new_p('三种方案的使用时长：箱线图', '方案', '使用时长（分钟）')
    for i, s in enumerate(box_stats):
        pfig.add_trace(go.Box(x=[i], q1=[s['q1']], median=[s['med']], q3=[s['q3']],
                             lowerfence=[s['whislo']], upperfence=[s['whishi']],
                             width=.5, boxpoints=False, fillcolor='#D6E3F4', line_color=BLUE, name=s['label']))
        pfig.add_trace(go.Scatter(x=[i]*len(s['fliers']), y=s['fliers'], mode='markers', marker=dict(color=BLUE,size=6)))
    pfig.update_xaxes(tickvals=[0,1,2], ticktext=group_names, range=[-.6,2.6])
    pfig.update_yaxes(range=[0,85])
    ''')

add('小提琴图', '分布',
    '把密度曲线左右镜像，哪里更宽，哪里的样本分布就更密集。它比箱线图保留了更多形状信息，例如是否可能有多个峰。',
    '本例每组宽度归一到同一个最大值，不能用宽度比较样本量。平滑结果依赖带宽，小样本时不要过度解读形状。',
    '两库都有原生小提琴接口；为严格对齐带宽、网格和宽度归一化，本例用共享 KDE 手工绘制轮廓，并标出中位数。',
    r'''
    mfig, ax = new_m('三种方案的使用时长：小提琴图', '方案', '使用时长（分钟）')
    for i, (a, d) in enumerate(zip(samples, violin_densities)):
        w = .38*d/d.max()
        ax.fill_betweenx(density_grid, i-w, i+w, facecolor='#D6E3F4', edgecolor=BLUE)
        ax.plot([i-.15,i+.15], [np.median(a)]*2, color=BLUE, linewidth=2)
    ax.set(xticks=[0,1,2], xticklabels=group_names, xlim=(-.6,2.6), ylim=(0,85))
    ''', r'''
    pfig = new_p('三种方案的使用时长：小提琴图', '方案', '使用时长（分钟）')
    for i, (a, d) in enumerate(zip(samples, violin_densities)):
        w = .38*d/d.max()
        pfig.add_trace(go.Scatter(x=np.r_[i-w,(i+w)[::-1]], y=np.r_[density_grid,density_grid[::-1]],
                                 fill='toself', fillcolor='#D6E3F4', line=dict(color=BLUE,width=1)))
        pfig.add_trace(go.Scatter(x=[i-.15,i+.15], y=[np.median(a)]*2, mode='lines',line_color=BLUE))
    pfig.update_xaxes(tickvals=[0,1,2], ticktext=group_names, range=[-.6,2.6])
    pfig.update_yaxes(range=[0,85])
    ''')

add('经验累积分布图', '分布',
    '回答“有多少比例的样本不超过某个数值”。比如沿横轴找到 40 分钟，再读纵轴，就能知道时长不超过 40 分钟的比例。',
    'ECDF 的值是累计比例，从 0 到 1 单调不减。它不需要分箱，也不需要选择 KDE 带宽。',
    '先排序，再计算 rank/n；左右补上 0 和 1 的延伸段。两边都采用后置阶梯，确保跳变位置一致。',
    r'''
    mfig, ax = new_m('使用时长的经验累积分布', '使用时长（分钟）', '累计比例')
    sx = np.r_[0, np.sort(dist), 80]
    sy = np.r_[0, np.arange(1,len(dist)+1)/len(dist), 1]
    ax.step(sx, sy, where='post', color=BLUE, linewidth=2)
    ax.set(xlim=(0,80), ylim=(0,1.02))
    from matplotlib.ticker import PercentFormatter
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ''', r'''
    pfig = new_p('使用时长的经验累积分布', '使用时长（分钟）', '累计比例')
    sx = np.r_[0, np.sort(dist), 80]
    sy = np.r_[0, np.arange(1,len(dist)+1)/len(dist), 1]
    pfig.add_trace(go.Scatter(x=sx, y=sy, line_shape='hv', line_color=BLUE))
    pfig.update_xaxes(range=[0,80])
    pfig.update_yaxes(range=[0,1.02], tickformat='.0%')
    ''')

add('带状散点图', '分布',
    '每个点保留一条原始观测，再在类别方向加一点抖动，减少重叠。样本量不太大时，可以直观看出各组的离散程度。',
    '横向抖动只为了看清点，不是额外测量值。这里固定随机种子，保证两张图的每个点都落在同样的位置。',
    '两边都能用 scatter 实现。Plotly 的悬停适合查点，Matplotlib 可以进一步和箱线图等统计摘要叠加。',
    r'''
    mfig, ax = new_m('三种方案的原始样本', '方案（横向抖动无业务含义）', '使用时长（分钟）')
    for i, a in enumerate(samples):
        ax.scatter(i+jitter[i], a, s=15, color=BLUE, alpha=.45, edgecolors='none')
    ax.set(xticks=[0,1,2], xticklabels=group_names, xlim=(-.6,2.6), ylim=(0,85))
    ''', r'''
    pfig = new_p('三种方案的原始样本', '方案（横向抖动无业务含义）', '使用时长（分钟）')
    for i, a in enumerate(samples):
        pfig.add_trace(go.Scatter(x=i+jitter[i], y=a, mode='markers',name=group_names[i],
                                 marker=dict(color=BLUE,size=5,opacity=.45)))
    pfig.update_xaxes(tickvals=[0,1,2], ticktext=group_names, range=[-.6,2.6])
    pfig.update_yaxes(range=[0,85])
    ''')

add('散点图', '关系',
    '两个数值变量一条记录对应一个点，适合观察关系、聚集和离群点。这里展示 140 条模拟预算与订单记录。',
    '点的趋势只能说明样本中的关系，不能直接证明因果。大量重叠时可调透明度，或者换二维直方图。',
    'Matplotlib 用 scatter，Plotly 用 markers 模式的 Scatter。两边固定同一坐标范围，避免缩放带来的误判。',
    r'''
    mfig, ax = new_m('预算与订单的关系', '预算（千元）', '订单数（笔）')
    ax.scatter(budget, sales, s=24, color=BLUE, alpha=.65, edgecolors='none')
    ax.set(xlim=(0,110), ylim=(0,550))
    ''', r'''
    pfig = new_p('预算与订单的关系', '预算（千元）', '订单数（笔）')
    pfig.add_trace(go.Scatter(x=budget, y=sales, mode='markers',marker=dict(color=BLUE,size=7,opacity=.65)))
    pfig.update_xaxes(range=[0,110])
    pfig.update_yaxes(range=[0,550])
    ''')

add('气泡图', '关系',
    '在散点图基础上，用面积再编码一个变量。本例横轴是预算，纵轴是订单，气泡面积代表客户数。',
    '面积与客户数成正比，不是半径与客户数成正比。大点可能挡住小点，要控制最大面积并明确大小含义。',
    'Matplotlib 的 s 单位是点平方；Plotly 设置 sizemode="area" 和 sizeref。两边统一最大直径约 24 像素，HTML 悬停可看客户数。',
    r'''
    mfig, ax = new_m('预算、订单与客户数', '预算（千元）', '订单数（笔）')
    area = customers/customers.max()*(24*72/100)**2
    ax.scatter(budget, sales, s=area, color=BLUE, alpha=.45, edgecolors='none')
    for n in [50,100,150]:
        ax.scatter([],[],s=n/customers.max()*(24*72/100)**2,color=BLUE,alpha=.45,label=f'{n} 人')
    ax.legend(title='客户数（面积）',loc='upper left',fontsize=8,title_fontsize=8)
    ax.set(xlim=(0,110), ylim=(0,550))
    ''', r'''
    pfig = new_p('预算、订单与客户数', '预算（千元）', '订单数（笔）')
    pfig.add_trace(go.Scatter(x=budget, y=sales, mode='markers',customdata=customers,
                             marker=dict(color=BLUE,size=customers,sizemode='area',
                                         sizeref=2*customers.max()/24**2,opacity=.45),
                             hovertemplate='预算 %{x:.1f} 千元<br>订单 %{y:.1f}<br>客户 %{customdata} 人<extra></extra>'))
    for n in [50,100,150]:
        pfig.add_trace(go.Scatter(x=[None],y=[None],mode='markers',name=f'{n} 人',showlegend=True,
                                 marker=dict(color=BLUE,size=[n],sizemode='area',
                                             sizeref=2*customers.max()/24**2,opacity=.45)))
    pfig.update_layout(showlegend=True,legend_title_text='客户数（面积）',legend_itemsizing='trace')
    pfig.data[0].showlegend=False
    pfig.update_xaxes(range=[0,110])
    pfig.update_yaxes(range=[0,550])
    ''')

add('回归散点图', '关系',
    '在散点上加一条拟合线，帮助概括两个变量的线性关系。本例用普通最小二乘拟合，图中标出这批模拟样本的 R²。',
    '拟合线不是因果结论，也不是未来预测保证。这里只画样本内拟合，没有把置信区间或预测区间混进来。',
    '两边共用 SciPy linregress 的参数，再各自画点和线，得到相同斜率、截距和 R²。',
    r'''
    mfig, ax = new_m('预算与订单：线性拟合', '预算（千元）', '订单数（笔）')
    ax.scatter(budget, sales, s=22, color=BLUE, alpha=.5, edgecolors='none')
    ax.plot(fit_x, fit_y, color=ORANGE, linewidth=2, label=f'线性拟合 R²={rvalue**2:.3f}')
    ax.legend(loc='upper left',fontsize=9)
    ax.set(xlim=(0,110), ylim=(0,550))
    ''', r'''
    pfig = new_p('预算与订单：线性拟合', '预算（千元）', '订单数（笔）')
    pfig.add_trace(go.Scatter(x=budget, y=sales, mode='markers',marker=dict(color=BLUE,size=6,opacity=.5),showlegend=False))
    pfig.add_trace(go.Scatter(x=fit_x,y=fit_y,mode='lines',line_color=ORANGE,name=f'线性拟合 R²={rvalue**2:.3f}'))
    pfig.update_layout(showlegend=True)
    pfig.update_xaxes(range=[0,110])
    pfig.update_yaxes(range=[0,550])
    ''')

add('二维直方图', '关系',
    '把二维空间切成小格，用颜色深浅表示每格有多少记录。点大量重叠时，比一团散点更容易看到密集区域。',
    '横纵轴边界、格子尺寸、颜色范围都要固定。空格子代表计数为 0，不是缺失数据。',
    '先用 histogram2d 生成同一计数矩阵。Matplotlib 的 pcolormesh 和 Plotly 的 Heatmap 都使用转置后的矩阵，防止横纵轴互换。',
    r'''
    mfig, ax = new_m('预算与订单的二维频数', '预算（千元）', '订单数（笔）')
    mesh = ax.pcolormesh(xedges,yedges,hist2d.T,cmap=CMAP,vmin=0,vmax=hist2d.max(),shading='flat')
    mfig.colorbar(mesh,ax=ax,label='样本数（个）')
    ax.set(xlim=(0,110),ylim=(0,550))
    ax.grid(False)
    ''', r'''
    pfig = new_p('预算与订单的二维频数', '预算（千元）', '订单数（笔）')
    pfig.add_trace(go.Heatmap(x=(xedges[:-1]+xedges[1:])/2,y=(yedges[:-1]+yedges[1:])/2,
                             z=hist2d.T,zmin=0,zmax=hist2d.max(),colorscale=SEQUENTIAL,
                             colorbar=dict(title='样本数',thickness=14)))
    pfig.update_xaxes(range=[0,110])
    pfig.update_yaxes(range=[0,550],showgrid=False)
    ''')

add('相关矩阵热力图', '关系',
    '把多个数值变量两两之间的相关系数排成矩阵。本例使用 Pearson 相关，蓝色偏正相关、橙色偏负相关。',
    '色标固定为 -1 到 1；相关不等于因果。非线性关系、异常值和缺失值处理都会影响解读。',
    '同一 corrcoef 矩阵，分别交给 imshow 与 Heatmap。单元格同时写数值，避免只靠颜色判断。',
    r'''
    mfig, ax = new_m('五项指标的 Pearson 相关')
    im=ax.imshow(corr,cmap=DCMAP,vmin=-1,vmax=1)
    ax.set(xticks=range(5),xticklabels=metric_names,yticks=range(5),yticklabels=metric_names)
    for i in range(5):
        for j in range(5):
            ax.text(j,i,f'{corr[i,j]:.2f}',ha='center',va='center',color='white' if abs(corr[i,j])>.6 else '#263445',fontsize=9)
    mfig.colorbar(im,ax=ax,label='Pearson r')
    ax.grid(False)
    ''', r'''
    pfig = new_p('五项指标的 Pearson 相关')
    pfig.add_trace(go.Heatmap(x=metric_names,y=metric_names,z=corr,zmin=-1,zmax=1,
                             colorscale=DIVERGING,colorbar=dict(title='Pearson r',thickness=14)))
    for i in range(5):
        for j in range(5):
            pfig.add_annotation(x=metric_names[j],y=metric_names[i],text=f'{corr[i,j]:.2f}',showarrow=False,
                                font=dict(size=13,color='white' if abs(corr[i,j])>.6 else '#263445'))
    pfig.update_yaxes(autorange='reversed',showgrid=False)
    ''')

add('等高线图', '关系',
    '两个输入共同决定一个连续数值时，可以用等高线展示响应面。这里画的是预先定义的模拟函数，曲线连接响应值相同的位置。',
    '这是一张函数示意图，不是由真实实验推断出的最优参数。对离散观测插值时，需要另外解释方法与覆盖范围。',
    '两边使用同一网格和 10 为间隔的等级。Matplotlib 分别画填色与线；Plotly 的 Contour 在一个 trace 中完成。',
    r'''
    mfig, ax = new_m('两个输入与模拟响应值', '输入 X（无量纲）', '输入 Y（无量纲）')
    cf=ax.contourf(gx,gy,ZZ,levels=contour_levels,cmap=CMAP,vmin=0,vmax=100)
    lines=ax.contour(gx,gy,ZZ,levels=[20,40,60,80],colors='#536D8D',linewidths=.6)
    ax.clabel(lines,fmt='%d',fontsize=8)
    mfig.colorbar(cf,ax=ax,label='模拟响应值')
    ax.grid(False)
    ''', r'''
    pfig = new_p('两个输入与模拟响应值', '输入 X（无量纲）', '输入 Y（无量纲）')
    pfig.add_trace(go.Contour(x=gx,y=gy,z=ZZ,zmin=0,zmax=100,colorscale=SEQUENTIAL,
                             contours=dict(start=0,end=100,size=10,showlabels=True,coloring='fill'),
                             line=dict(width=.6,color='#536D8D'),colorbar=dict(title='响应值',thickness=14)))
    pfig.update_xaxes(range=[0,10])
    pfig.update_yaxes(range=[0,8],showgrid=False)
    ''')

add('雷达图', '业务与多维',
    '把少量维度放在放射轴上，对照两个方案的轮廓。示例是人为设定的五维评分，统一使用 0—5 分，越高越好。',
    '维度顺序会改变多边形外观；量纲或方向不一致时不能直接连起来。本例评分不代表对两套绘图库的测评。',
    'Matplotlib 使用极坐标轴，Plotly 使用 Scatterpolar。两边从顶部起始并顺时针排列，且重复首点闭合。',
    r'''
    mfig, ax = new_m('两个示例方案的五维评分',polar=True)
    theta=np.r_[angles,angles[0]]
    ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
    for a,label,color,style in [(radar_a,'方案 A',BLUE,'-'),(radar_b,'方案 B',ORANGE,'--')]:
        ax.plot(theta,np.r_[a,a[0]],label=label,color=color,linestyle=style,marker='o')
        ax.fill(theta,np.r_[a,a[0]],color=color,alpha=.08)
    ax.set(xticks=angles,xticklabels=radar_labels,ylim=(0,5),yticks=[1,2,3,4,5])
    ax.legend(loc='upper right',bbox_to_anchor=(1.32,1.08),fontsize=8)
    ''', r'''
    pfig = new_p('两个示例方案的五维评分')
    for a,label,color,dash in [(radar_a,'方案 A',BLUE,'solid'),(radar_b,'方案 B',ORANGE,'dash')]:
        pfig.add_trace(go.Scatterpolar(r=np.r_[a,a[0]],theta=radar_labels+[radar_labels[0]],
                                      mode='lines+markers',name=label,line=dict(color=color,dash=dash)))
    pfig.update_layout(showlegend=True,polar=dict(radialaxis=dict(range=[0,5],dtick=1),
                         angularaxis=dict(rotation=90,direction='clockwise')))
    ''')

add('极坐标柱状图', '业务与多维',
    '一天中的时段、方位等具有周期或方向含义的数据，可以沿圆周排列。这里每根柱对应一个三小时时段，柱高表示访问次数。',
    '数值编码在径向长度上，不是扇区面积上。极坐标适合强调周期结构，精确比较大小时直角坐标条形图往往更好读。',
    'Matplotlib 在 polar 轴上调用 bar；Plotly 用 Barpolar。固定角度顺序和径向范围，确保午夜在顶部。',
    r'''
    mfig, ax = new_m('一天内各时段访问量',polar=True)
    theta=hours/24*2*np.pi
    ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
    ax.bar(theta,hour_values,width=2*np.pi/8*.8,color=BLUE)
    ax.set(xticks=theta,xticklabels=[f'{h:02d}时' for h in hours],ylim=(0,60),yticks=[20,40,60])
    ax.set_xlabel('径向刻度：访问次数',labelpad=15)
    ''', r'''
    pfig = new_p('一天内各时段访问量')
    pfig.add_trace(go.Barpolar(r=hour_values,theta=hours/24*360,width=36,marker_color=BLUE))
    pfig.update_layout(polar=dict(radialaxis=dict(range=[0,60],dtick=20),
                         angularaxis=dict(rotation=90,direction='clockwise',tickvals=hours/24*360,
                                          ticktext=[f'{h:02d}时' for h in hours])))
    pfig.add_annotation(x=.5,y=-.12,xref='paper',yref='paper',text='径向刻度：访问次数',showarrow=False)
    ''')

add('桑基图', '业务与多维',
    '看流量从哪里来、又流向哪里。示例三种来源流入一个汇总节点，总量为 160，再分成 100 和 60 两种去向。',
    '节点处的流入流出要守恒，边宽表示流量。复杂路径还要检查是否重复累计，不能把同一批对象在不同环节的数量随意相加。',
    'Matplotlib 自带 Sankey，适合这种单个平衡系统，但布局与 Plotly 的节点—连边结构差别明显。这里比较同一流量关系，不强求外形一致。',
    r'''
    mfig, ax = new_m('来源 → 汇总 → 去向（单位：人）')
    Sankey(ax=ax,scale=.004,offset=.15,head_angle=120,format='%.0f',unit=' 人').add(
        flows=[60,55,45,-100,-60],labels=['搜索','推荐','社群','完成','流失'],
        orientations=[1,0,-1,0,-1],pathlengths=[.3,.35,.3,.35,.3],
        trunklength=1.1,facecolor=BLUE,edgecolor='white').finish()
    ax.set_aspect('equal',adjustable='box'); ax.axis('off')
    ''', r'''
    pfig = new_p('来源 → 汇总 → 去向（单位：人）')
    pfig.add_trace(go.Sankey(arrangement='fixed',
        node=dict(label=['搜索 60','推荐 55','社群 45','汇总 160','完成 100','流失 60'],
                  x=[.02,.02,.02,.5,.98,.98],y=[.08,.42,.77,.45,.25,.8],
                  color=[BLUE,BLUE,BLUE,BLUE,BLUE,ORANGE],pad=22,thickness=16),
        link=dict(source=[0,1,2,3,3],target=[3,3,3,4,5],value=[60,55,45,100,60],
                  color=['rgba(50,105,180,.25)']*4+['rgba(216,137,54,.3)'])))
    ''')

add('甘特图', '业务与多维',
    '把任务的开始和结束时间画成横条，适合看项目排期、任务重叠和阶段跨度。示例是一份五任务的模拟排期。',
    '这里区间按“开始日包含、结束日不包含”计算。条形重叠只代表时间重叠，本例没有编码前后依赖、进度或关键路径。',
    'Matplotlib 用日期坐标上的 barh；Plotly Express 的 timeline 接收开始、结束列，再套统一样式。',
    r'''
    mfig, ax = new_m('五项任务的模拟排期', '日期（2026 年 1 月）', '')
    ax.barh(tasks['任务'],(tasks['结束']-tasks['开始']).dt.days,
            left=mdates.date2num(tasks['开始']),height=.55,color=BLUE)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.set_xlim(mdates.date2num(pd.Timestamp('2026-01-01')),mdates.date2num(pd.Timestamp('2026-01-23')))
    ax.invert_yaxis(); ax.grid(False)
    ax.grid(axis='x',color='#E8ECF2')
    ''', r'''
    pfig = new_p('五项任务的模拟排期', '日期（2026 年 1 月）', '')
    timeline=px.timeline(tasks,x_start='开始',x_end='结束',y='任务',color_discrete_sequence=[BLUE])
    pfig.add_traces(timeline.data)
    pfig.update_xaxes(type='date',range=['2026-01-01','2026-01-23'],tickformat='%m-%d',dtick=3*86400000,showgrid=True)
    pfig.update_yaxes(autorange='reversed',categoryorder='array',categoryarray=tasks['任务'],showgrid=False)
    pfig.update_layout(margin_l=100)
    ''')

add('K线图', '业务与多维',
    '同一时间段内，同时展示开盘、最高、最低和收盘四个价格。这里用 12 个连续自然日的模拟 OHLC 数据演示结构。',
    '最高价要不低于开收盘，最低价要不高于开收盘。本例蓝色表示上涨、橙色表示下跌；真实市场还需处理交易日、复权与时区。',
    'Plotly 原生 Candlestick；Matplotlib 本例用竖线画高低价、矩形画开收盘。本文只讲绘图，不据此提出交易判断。',
    r'''
    mfig, ax = new_m('模拟 OHLC 价格', '日期（2026 年 1 月）', '模拟价格（元）')
    x=mdates.date2num(ohlc_dates)
    for i,(o,h,l,c) in enumerate(zip(open_prices,high_prices,low_prices,close_prices)):
        color=BLUE if c>=o else ORANGE
        ax.vlines(x[i],l,h,color=color,linewidth=1.2)
        ax.add_patch(Rectangle((x[i]-.3,min(o,c)),.6,max(abs(c-o),.01),facecolor=color,edgecolor=color))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.set(xlim=(x[0]-1,x[-1]+1),ylim=(low_prices.min()-2,high_prices.max()+2))
    ''', r'''
    pfig = new_p('模拟 OHLC 价格', '日期（2026 年 1 月）', '模拟价格（元）')
    pfig.add_trace(go.Candlestick(x=ohlc_dates,open=open_prices,high=high_prices,low=low_prices,close=close_prices,
                                 increasing=dict(line_color=BLUE,fillcolor=BLUE),
                                 decreasing=dict(line_color=ORANGE,fillcolor=ORANGE)))
    pfig.update_xaxes(rangeslider_visible=False,range=[ohlc_dates[0]-pd.Timedelta(days=1),ohlc_dates[-1]+pd.Timedelta(days=1)],
                     tickformat='%m-%d',dtick=2*86400000)
    pfig.update_yaxes(range=[low_prices.min()-2,high_prices.max()+2])
    ''')

add('帕累托图', '业务与多维',
    '先把问题按频数降序排列，再叠加累计占比。适合定位“先处理哪几类问题，能覆盖较多案例”。',
    '左轴是问题数量，右轴是累计百分比；两者不能按同一数值单位读。80/20 不是所有数据必然满足的规律。',
    'Matplotlib 用 twinx，Plotly 把累计曲线放到 y2。示例前三类累计刚好覆盖 80%，这是这份模拟数据的结果。',
    r'''
    mfig, ax = new_m('问题数量与累计占比', '问题类型', '问题数（个）')
    ax.bar(issues,issue_counts,color=BLUE,width=.6)
    ax.set_ylim(0,60)
    right=ax.twinx()
    right.plot(issues,cumulative,color=ORANGE,marker='o',linewidth=2)
    right.set(ylim=(0,105),ylabel='累计占比（%）')
    right.grid(False)
    right.spines['right'].set_visible(True)
    ''', r'''
    pfig = new_p('问题数量与累计占比', '问题类型', '问题数（个）')
    pfig.add_trace(go.Bar(x=issues,y=issue_counts,marker_color=BLUE,width=.6,name='问题数'))
    pfig.add_trace(go.Scatter(x=issues,y=cumulative,mode='lines+markers',line_color=ORANGE,
                             yaxis='y2',name='累计占比'))
    pfig.update_layout(margin_r=75,yaxis2=dict(title='累计占比（%）',overlaying='y',side='right',range=[0,105],showgrid=False))
    pfig.update_yaxes(range=[0,60],selector=dict(anchor='x'))
    pfig.layout.yaxis.range=[0,60]
    pfig.layout.yaxis2.range=[0,105]
    pfig.layout.yaxis2.tickvals=[0,20,40,60,80,100]
    ''')

add('哑铃图', '比较',
    '每个类别放两个点，中间用线连接，适合比较调整前后、去年今年，或者目标与实际。这里展示各渠道前后两期订单。',
    '两个点的口径必须一致。连接线只表达数值差距，本身不能证明某个动作带来了因果效果。',
    'Matplotlib 的 hlines 可以一次画多条连接线；Plotly 用分段 Scatter。用圆点和菱形区分前后，降低对颜色的依赖。',
    r'''
    mfig, ax = new_m('渠道订单前后对比', '订单数（笔）', '渠道')
    y = np.arange(4)
    ax.hlines(y, before, after, color='#B9C4D2', linewidth=3)
    ax.scatter(before, y, color=ORANGE, marker='o', s=65, label='前期', zorder=3)
    ax.scatter(after, y, color=BLUE, marker='D', s=55, label='后期', zorder=3)
    ax.set(yticks=y, yticklabels=channels, xlim=(0, 420), ylim=(3.5, -.5))
    ax.legend(loc='lower right', fontsize=8)
    ax.grid(False)
    ''', r'''
    pfig = new_p('渠道订单前后对比', '订单数（笔）', '渠道')
    xs, ys = [], []
    for i in range(4):
        xs += [int(before[i]), int(after[i]), None]; ys += [i, i, None]
    pfig.add_trace(go.Scatter(x=xs, y=ys, mode='lines', line_color='#B9C4D2', showlegend=False))
    for a, label, color, symbol in [(before,'前期',ORANGE,'circle'),(after,'后期',BLUE,'diamond')]:
        pfig.add_trace(go.Scatter(x=a, y=np.arange(4), mode='markers', name=label,
                                 marker=dict(color=color, symbol=symbol, size=11)))
    pfig.update_layout(showlegend=True)
    pfig.update_xaxes(range=[0, 420])
    pfig.update_yaxes(tickvals=list(range(4)), ticktext=channels, range=[3.5, -.5], showgrid=False)
    ''')
