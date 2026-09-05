"""v1.0.0 | 2026-09-06 | 31 雷达图。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({k:v for k,v in shared.items() if not k.startswith('__')})

# Matplotlib：实际执行的完整绘图段
mfig, ax = new_m('两个示例方案的五维评分',polar=True)
theta=np.r_[angles,angles[0]]
ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
for a,label,color,style in [(radar_a,'方案 A',BLUE,'-'),(radar_b,'方案 B',ORANGE,'--')]:
    ax.plot(theta,np.r_[a,a[0]],label=label,color=color,linestyle=style,marker='o')
    ax.fill(theta,np.r_[a,a[0]],color=color,alpha=.08)
ax.set(xticks=angles,xticklabels=radar_labels,ylim=(0,5),yticks=[1,2,3,4,5])
ax.legend(loc='upper right',bbox_to_anchor=(1.32,1.08),fontsize=8)

# Plotly：实际执行的完整绘图段
pfig = new_p('两个示例方案的五维评分')
for a,label,color,dash in [(radar_a,'方案 A',BLUE,'solid'),(radar_b,'方案 B',ORANGE,'dash')]:
    pfig.add_trace(go.Scatterpolar(r=np.r_[a,a[0]],theta=radar_labels+[radar_labels[0]],
                                  mode='lines+markers',name=label,line=dict(color=color,dash=dash)))
pfig.update_layout(showlegend=True,polar=dict(radialaxis=dict(range=[0,5],dtick=1),
                     angularaxis=dict(rotation=90,direction='clockwise')))

finish(31, '雷达图', mfig, pfig)
