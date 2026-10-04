"""从官方奖金数据独立绘制1600×680公众号横版封面。"""
from pathlib import Path
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parent
BG, INK, MUTED, GOLD, BLUE = '#FAF8F3', '#18323D', '#687A80', '#BE8B35', '#236A88'

def generate_cover():
    font = FontProperties(fname=os.environ.get('NOBEL_CN_FONT', r'C:\Windows\Fonts\msyh.ttc'))
    history = pd.read_csv(ROOT/'数据/整理/奖金历史.csv')
    assert len(history) == 125 and history.year.iloc[0] == 1901
    assert history.year.iloc[-1] == 2025
    fig = plt.figure(figsize=(16, 6.8), dpi=100, facecolor=BG)
    def text(x, y, value, size, color=INK, **kwargs):
        return fig.text(x, y, value, fontproperties=font, fontsize=size, color=color, **kwargs)
    nominal_ratio = history.nominal_sek.iloc[-1] / history.nominal_sek.iloc[0]
    real_ratio = history.real_2025_sek.iloc[-1] / history.real_2025_sek.iloc[0]
    text(.065, .865, '扣除物价变化，奖金并没涨73倍', 34, weight='bold')
    text(.065, .797, '诺贝尔奖金 · 1901—2025 · 每个完整奖项', 18, MUTED)
    text(.938, .872, f'购买力≈{real_ratio:.3f}倍', 27, BLUE, ha='right', weight='bold')
    text(.938, .797, f'名义金额≈{nominal_ratio:.2f}倍', 18, MUTED, ha='right')
    ax = fig.add_axes([.075, .2, .86, .51], facecolor=BG)
    x, y = history.year, history.nominal_sek / 10000
    real = history.real_2025_sek / 10000
    ax.plot(x, real, color=BLUE, linewidth=4, solid_capstyle='round', label='按2025年币值折算')
    ax.plot(x, y, color=GOLD, linewidth=3.5, solid_capstyle='round', label='当年名义奖金')
    ax.scatter([1901, 2001, 2025], [real.iloc[0], real[history.year==2001].iloc[0], real.iloc[-1]], s=55, color=BLUE, zorder=5)
    ax.set_xlim(1900, 2028)
    ax.set_ylim(0, 1800)
    ax.set_xticks([1901, 1925, 1950, 1975, 2000, 2025])
    ax.set_yticks([0, 500, 1000, 1500])
    ax.tick_params(axis='both', length=0, pad=12, labelsize=17, colors=MUTED)
    ax.grid(axis='y', color='#E1E4E1', linewidth=1)
    ax.set_axisbelow(True)
    for spine in ax.spines.values(): spine.set_visible(False)
    for label in ax.get_xticklabels()+ax.get_yticklabels(): label.set_fontproperties(font); label.set_fontsize(17)
    ax.annotate('1901年：约1,083万', xy=(1901, real.iloc[0]), xytext=(1907, 1390),
                fontproperties=font, fontsize=18, color=BLUE,
                arrowprops={'arrowstyle':'-', 'color':MUTED, 'lw':1.3})
    ax.annotate('2001年：约1,555万', xy=(2001, real[history.year==2001].iloc[0]), xytext=(1975, 1690),
                fontproperties=font, fontsize=18, color=BLUE,
                arrowprops={'arrowstyle':'-', 'color':MUTED, 'lw':1.3})
    ax.annotate('2025年：1,100万', xy=(2025, real.iloc[-1]), xytext=(2025, 620),
                fontproperties=font, fontsize=18, color=INK, ha='right',
                arrowprops={'arrowstyle':'-', 'color':MUTED, 'lw':1.3})
    ax.legend(loc='lower left', bbox_to_anchor=(.17, 1.025), ncol=2, frameon=False, prop=FontProperties(fname=font.get_file(), size=17), borderaxespad=0, handlelength=2.1, columnspacing=1.6)
    text(.075, .738, '万元（SEK）', 15, MUTED)
    text(.065, .067, '来源：诺贝尔基金会官方奖金历史表（按2025年币值折算）', 15, MUTED)
    text(.938, .067, '可以叫我才哥', 16, '#236A88', ha='right')
    target = ROOT/'配图/封面.png'
    fig.savefig(target, dpi=100, facecolor=BG)
    plt.close(fig)
    print('已生成独立封面：1600×680，约2.35:1')
    return target

if __name__ == '__main__': generate_cover()
