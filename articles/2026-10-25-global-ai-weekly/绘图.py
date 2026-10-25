"""本周AI要闻配图：一周时间线、芯片股本周涨跌幅。时间线来自公开报道，手工录入；行情数据由 采集数据.py 生成。

画布宽8英寸、130dpi（约1040px），正文字号15pt以上，保证手机端缩放后仍可读。
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '配图'
OUT.mkdir(exist_ok=True)
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyh.ttc')
font_manager.fontManager.addfont(r'C:\Windows\Fonts\msyhbd.ttc')
plt.rcParams.update({'font.family': 'Microsoft YaHei', 'axes.unicode_minus': False})

# 视觉轮换方案（2026-10-25起）：暖白、深青/陶土/灰紫；A股习惯下跌用绿色
BG, INK, MUTED, GRID = '#F9F7F2', '#213638', '#697775', '#E3E0D8'
INDIGO, CORAL, VIOLET, DOWN = '#166B72', '#BD5B42', '#75628E', '#13895E'
BRAND = '可以叫我才哥'
W, DPI = 8, 130


def finish(fig, title, sub, note, h):
    """标题区固定高度（英寸），换算为画布比例。"""
    fig.text(0.05, 1 - 0.5 / h, title, color=INK, fontsize=22, weight='bold', va='center')
    fig.text(0.05, 1 - 0.95 / h, sub, color=MUTED, fontsize=13, va='center')
    fig.text(0.05, 0.28 / h, note, color=MUTED, fontsize=10.5, va='center')
    fig.text(0.95, 0.28 / h, BRAND, color=MUTED, fontsize=11, ha='right', weight='bold', va='center')


def clean(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, colors=MUTED)


def fig_timeline():
    """竖版时间线：行为日期，列为三条主线。"""
    days = ['10/19 周一', '10/20 周二', '10/21 周三', '10/22 周四', '10/23 周五']
    lanes = [('模型', INDIGO), ('监管', CORAL), ('资本·基建', VIOLET)]
    events = [
        (0,0,'MiniMax\nM3.1 Flash'),(0,1,'DeepSeek采购\n限制公开'),(0,2,'Tenstorrent\n融资15亿美元'),
        (1,0,'DeepInfer\n框架开源'),(1,1,'OpenAI监控\n事件报告更新'),
        (2,0,'OpenAI宣布\n接入谷歌云'),(2,1,'微软披露\nAI辅助攻击'),(2,2,'英伟达发布\nDSX POD'),
        (3,0,'Skills标准\n移交AAIF'),(3,0,'Claude新增\n云托管选项'),
        (4,0,'Kimi Code\n上线K3.1 Pro'),(4,2,'软银周跌\n13.51%'),
    ]
    h = 11.5
    fig, ax = plt.subplots(figsize=(W, h), dpi=DPI, facecolor=BG)
    clean(ax)
    # 每天的行高按当天单条主线最多事件数分配
    per_day = [max(sum(1 for e in events if e[0] == d and e[1] == l) for l in range(3)) or 1 for d in range(len(days))]
    tops, y = [], 0
    for n in per_day:
        tops.append(y)
        y += n * 0.9 + 0.25
    total = y
    ax.set_xlim(-0.05, 3.0)
    ax.set_ylim(total, -0.75)
    for i, (name, c) in enumerate(lanes):
        ax.add_patch(FancyBboxPatch((i + 0.04, -0.7), 0.92, total + 0.6, boxstyle='round,pad=0,rounding_size=0.05',
                                    fc=c, alpha=.06, ec='none', zorder=0))
        ax.text(i + 0.5, -0.38, name, ha='center', va='center', fontsize=17, color=c, weight='bold')
    for d, label in enumerate(days):
        mid = tops[d] + per_day[d] * 0.45
        ax.axhline(tops[d] - 0.12, color=GRID, lw=1, zorder=0)
        ax.text(-0.04, mid, label.replace(' ', '\n'), ha='right', va='center', fontsize=14, color=INK, linespacing=1.4)
    count = {}
    for d, lane, txt in events:
        j = count.get((d, lane), 0)
        count[(d, lane)] = j + 1
        c = lanes[lane][1]
        y0 = tops[d] + j * 0.9
        ax.add_patch(FancyBboxPatch((lane + 0.1, y0 + 0.04), 0.8, 0.78, boxstyle='round,pad=0,rounding_size=0.06',
                                    fc='white', ec=c, lw=2, zorder=3))
        ax.text(lane + 0.5, y0 + 0.43, txt, ha='center', va='center', fontsize=14, color=INK, zorder=5, linespacing=1.35)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.subplots_adjust(top=1 - 1.35 / h, bottom=0.6 / h, left=.17, right=.97)
    finish(fig, '一周AI大事时间线', '10月19—25日选题，按本周公开/更新日期排列',
           '来源：各厂商公告、DHS通知；研究彩蛋见正文', h)
    fig.savefig(OUT / '图1_一周时间线.png', facecolor=BG)
    plt.close(fig)


def fig_chips():
    """固定10只AI产业链观察样本；颜色只表示方向，SOXX用文字标识。"""
    import pandas as pd
    df=pd.read_csv(ROOT/'数据/芯片股本周涨跌幅.csv').sort_values('周涨跌幅%')
    h=9.8
    fig,ax=plt.subplots(figsize=(W,h),dpi=DPI,facecolor=BG)
    clean(ax)
    for i,(_,r) in enumerate(df.iterrows()):
        v=r['周涨跌幅%'];c=DOWN if v<0 else CORAL if v>0 else MUTED
        ax.barh(i,v,color=c,height=.58,alpha=.9)
        if v==0:ax.plot(0,i,'o',color=MUTED,ms=5)
        ax.text(v-.25 if v<0 else v+.25,i,f'{v:+.2f}%' if v else '0.00%',ha='right' if v<0 else 'left',va='center',fontsize=15,color=c,weight='bold')
    labels=[n.replace('半导体ETF（SOXX）','SOXX ETF').replace('台积电ADR','台积电 ADR') for n in df['名称']]
    ax.set_yticks(range(len(df)));ax.set_yticklabels(labels,fontsize=14,color=INK)
    ax.invert_yaxis();ax.set_xlim(-18.8,5.0);ax.axvline(0,color=GRID,lw=1.2);ax.set_xticks([])
    fig.subplots_adjust(top=1-1.55/h,bottom=.9/h,left=.25,right=.97)
    finish(fig,'AI产业链：7跌、2涨、1平','10月19—23日周涨跌幅；绿跌、陶土红涨、灰平','数据：Yahoo Finance；10月23日 / 10月16日收盘 − 1',h)
    fig.text(.05,.65/h,'固定观察样本，含软银投资集团；未复权，不含分红及汇率变化',fontsize=11,color=MUTED)
    fig.savefig(OUT/'图3_芯片股本周涨跌幅.png',facecolor=BG);plt.close(fig)

if __name__=='__main__':
    fig_timeline();fig_chips();print('图表已生成')
