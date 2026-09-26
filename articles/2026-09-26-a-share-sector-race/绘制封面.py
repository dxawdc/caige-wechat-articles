"""用已校验的2026年收益曲线绘制公众号封面。"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from render_videos import load, values

ROOT = Path(__file__).resolve().parent
days, pairs, prices = load()
window, returns, _ = values(days, pairs, prices, "2024-09-24")
names = [name for _, name in pairs]

plt.rcParams.update({"font.family": "Microsoft YaHei", "axes.unicode_minus": False})
fig = plt.figure(figsize=(9, 3.83), dpi=160, facecolor="#f0f3f1")
fig.text(.055, .88, "MARKET DATA  /  9·24", fontsize=11, weight="bold", color="#ab704b")
fig.text(.055, .68, "“9·24”之后", fontsize=28, weight="bold", color="#203942")
fig.text(.055, .49, "谁跑在前面？", fontsize=29, weight="bold", color="#203942")
fig.text(.055, .31, "30个A股主题 · 板块轮动赛马图", fontsize=11, color="#65777d")
fig.text(.055, .13, "可以叫我才哥", fontsize=12, weight="bold", color="#ab704b")

ax = fig.add_axes([.59, .17, .36, .64], facecolor="#ffffff")
for name, color in [("CPO", "#397e78"), ("存储", "#b88a50"), ("半导体", "#8a7ba3")]:
    series = returns[names.index(name)]
    ax.plot(range(len(window)), series, lw=2.2, color=color, label=name)
    ax.scatter([len(window) - 1], [series[-1]], s=26, color=color, zorder=3)
ax.axhline(0, lw=.8, color="#b5c0c1")
ax.grid(axis="y", color="#e6ebea", lw=.7)
ax.set_xlim(0, len(window) + 3)
ax.set_ylim(-25, 670)
ax.set_xticks([0, len(window) - 1], ["2024-09", "2026-09"])
ax.set_yticks([0, 300, 600], ["0%", "300%", "600%"])
ax.tick_params(labelsize=8, colors="#71848a", length=0)
ax.spines[:].set_visible(False)
ax.legend(loc="upper left", frameon=False, fontsize=9, ncol=3, columnspacing=.8, handlelength=1.3)
fig.savefig(ROOT / "配图" / "00-封面.png", facecolor=fig.get_facecolor(), dpi=160)
plt.close(fig)
