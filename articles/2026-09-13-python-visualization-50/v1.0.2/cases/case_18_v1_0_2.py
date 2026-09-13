"""案例 18：甘特图把开始时间与工期分开编码 | v1.0.2 | 才哥AGI | 全部为模拟数据。"""

from common_v1_0_2 import *

import matplotlib.dates as mdates

rng, fig, ax = start(18, "")
df = pd.DataFrame(
    {
        "任务": ["需求", "数据", "开发", "测试", "上线"],
        "开始": pd.to_datetime(
            [
                "2026-09-01",
                "2026-09-04",
                "2026-09-08",
                "2026-09-17",
                "2026-09-24",
            ]
        ),
        "天数": [5, 8, 12, 7, 2],
    }
)
df["结束"] = df.开始 + pd.to_timedelta(df.天数, unit="D")
ax.barh(
    df.任务, df.天数, left=mdates.date2num(df.开始), height=0.55
)
ax.xaxis_date()
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
ax.invert_yaxis()
ax.set_xlabel("日历日期；区间为 [开始, 结束)")
finish(18, "甘特图把开始时间与工期分开编码", fig, df)
