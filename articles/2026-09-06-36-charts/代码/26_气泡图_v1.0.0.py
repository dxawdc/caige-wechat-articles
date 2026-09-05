"""v1.0.0 | 2026-09-06 | 26 气泡图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('预算、订单与客户数', '预算（千元）', '订单数（笔）')
area = customers/customers.max()*(24*72/100)**2
ax.scatter(budget, sales, s=area, color=BLUE, alpha=.45, edgecolors='none')
for n in [50,100,150]:
    ax.scatter([],[],s=n/customers.max()*(24*72/100)**2,color=BLUE,alpha=.45,label=f'{n} 人')
ax.legend(title='客户数（面积）',loc='upper left',fontsize=8,title_fontsize=8)
ax.set(xlim=(0,110), ylim=(0,550))

# Plotly：实际执行的完整绘图段
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

finish(26, '气泡图', mfig, pfig)
