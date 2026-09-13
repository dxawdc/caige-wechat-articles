"""案例 35：散点与回归线，不把相关写成因果 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

from scipy.stats import linregress

rng, fig, ax = start(35, "")
x = rng.uniform(1, 12, 180)
y = 22 + 4.2 * x + rng.normal(0, 9, 180)
df = pd.DataFrame({"练习小时": x, "成绩": y})
fit = linregress(x, y)
ax.scatter(x, y, s=25, alpha=0.55)
xx = np.array([x.min(), x.max()])
ax.plot(
    xx,
    fit.intercept + fit.slope * xx,
    color=COLORS[2],
    label=f"线性拟合，r={fit.rvalue:.2f}",
)
ax.set(
    xlabel="每周练习时长（小时）", ylabel="模拟测验成绩（分）"
)
ax.legend()
finish(
    35,
    "散点与回归线，不把相关写成因果",
    fig,
    df,
    {
        "Pearson_r": fit.rvalue,
        "斜率": fit.slope,
        "说明": "生成机制预设正相关，非实验因果结论",
    },
)
