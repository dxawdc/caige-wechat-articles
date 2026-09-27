"""从高德驾车轨迹卡片 CSV 生成公众号配图与匿名统计。

用法：
    python 绘制图表.py --csv "本机的驾车行程_页面采集.csv"
    python 绘制图表.py --csv 数据/演示行程.csv --output 演示输出
"""

from __future__ import annotations

import argparse
import calendar
from io import BytesIO
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.io import to_html
from PIL import Image


ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "配图"
DATA_DIR = ROOT / "数据"
FONT = "Microsoft YaHei, PingFang SC, Noto Sans CJK SC, Arial"
INK = "#30483E"
ORANGE = "#CC9172"
BLUE = "#719D8B"
TEAL = "#A9C9B9"
GRAY = "#CCD6CE"
PALE = "#E8EEE7"
PAPER = "#FFF9F1"
IMAGE_WIDTH = 900
CALENDAR_START = pd.Timestamp("2025-10-01")
CALENDAR_END = pd.Timestamp("2026-09-27")


def read_trips(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype={"date": str, "time": str})
    required = {
        "date", "time", "origin", "destination", "distance_km_display",
        "distance_km_est", "duration", "average_speed_kmh", "max_speed_kmh",
        "travel_mode",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"CSV 缺少字段：{', '.join(sorted(missing))}")
    df = df.loc[df["travel_mode"].eq("driving")].copy()
    df["date_iso"] = pd.to_datetime(df["date"], format="%Y.%m.%d")
    df = df.loc[(df["date_iso"] >= "2025-09-27") & (df["date_iso"] < "2026-09-28")].copy()
    df["month"] = df["date_iso"].dt.strftime("%Y-%m")
    df["weekday"] = df["date_iso"].dt.weekday
    df["hour"] = pd.to_datetime(df["time"], format="%H:%M").dt.hour
    df["day_type"] = df["weekday"].map(lambda x: "周末" if x >= 5 else "工作日")
    df["distance_km"] = pd.to_numeric(df["distance_km_est"], errors="raise")
    df["average_speed"] = pd.to_numeric(df["average_speed_kmh"], errors="raise")
    df["max_speed"] = pd.to_numeric(df["max_speed_kmh"], errors="raise")
    parts = df["duration"].str.split(":", expand=True).astype(int)
    df["duration_min"] = parts[0] * 60 + parts[1] + parts[2] / 60
    df["route"] = df["origin"].astype(str) + " → " + df["destination"].astype(str)
    if df.empty:
        raise ValueError("分析时间范围内没有驾车记录")
    return df


def style(fig: go.Figure, title: str, height: int = 580, subtitle: str = "") -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0.055, "y": 0.96, "font": {"size": 31, "color": INK}},
        width=IMAGE_WIDTH, height=height,
        margin={"l": 90, "r": 72, "t": 105, "b": 100},
        paper_bgcolor=PAPER, plot_bgcolor=PAPER,
        font={"family": FONT, "size": 22, "color": INK},
        hoverlabel={"font": {"family": FONT, "size": 17}},
        legend={"orientation": "h", "y": -0.18, "x": 0, "font": {"size": 19}},
    )
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont={"size": 19}, title_font={"size": 21})
    fig.update_yaxes(gridcolor=PALE, zeroline=False, tickfont={"size": 19}, title_font={"size": 21})
    if subtitle:
        fig.add_annotation(
            x=0, y=1.08, xref="paper", yref="paper", text=subtitle,
            showarrow=False, xanchor="left", font={"size": 18, "color": "#5A7264"},
        )
    fig.add_annotation(
        x=1, y=-0.13, xref="paper", yref="paper", text="可以叫我才哥",
        showarrow=False, xanchor="right", font={"size": 17, "color": "#5A7264"},
    )
    return fig


def build_calendar(df: pd.DataFrame) -> go.Figure:
    """按月绘制每日可见卡片里程；空白日不推断为零里程。"""
    daily = df.groupby("date_iso")["distance_km"].sum()
    months = pd.period_range("2025-10", "2026-09", freq="M")
    colors = ["#F0EEE9", "#E4EFEC", "#C9DFD8", "#A0C4B8", "#3F746F"]
    calendar_ink = "#284B48"
    color_scale = []
    for level, color in enumerate(colors):
        color_scale.extend([(level / 5, color), ((level + 1) / 5, color)])
    fig = make_subplots(
        rows=2, cols=6, subplot_titles=[f"{m.year}.{m.month:02d}" for m in months],
        horizontal_spacing=0.024, vertical_spacing=0.19,
    )
    for index, month in enumerate(months):
        days = calendar.monthcalendar(month.year, month.month)
        days += [[0] * 7 for _ in range(6 - len(days))]
        levels, labels, hover = [], [], []
        for week in days:
            week_levels, week_labels, week_hover = [], [], []
            for day in week:
                date = pd.Timestamp(month.year, month.month, day) if day else None
                if date is None or not CALENDAR_START <= date <= CALENDAR_END:
                    week_levels.append(None)
                    week_labels.append("")
                    week_hover.append("")
                    continue
                km = daily.get(date)
                level = (0 if pd.isna(km) else 1 if km < 5 else
                         2 if km < 10 else 3 if km < 20 else 4)
                week_levels.append(level)
                week_labels.append(str(day))
                week_hover.append(
                    f"{date:%Y-%m-%d}<br>" +
                    ("无可见记录" if pd.isna(km) else f"可见里程 {km:.1f} km")
                )
            levels.append(week_levels)
            labels.append(week_labels)
            hover.append(week_hover)
        row, col = divmod(index, 6)
        fig.add_trace(go.Heatmap(
            z=levels, x=list(range(7)), y=list(range(6)),
            customdata=hover, hovertemplate="%{customdata}<extra></extra>",
            colorscale=color_scale, zmin=0, zmax=5,
            xgap=3, ygap=3, showscale=False,
        ), row=row + 1, col=col + 1)
        points = [
            (column, week, labels[week][column],
             "#FFFDF8" if levels[week][column] == 4 else calendar_ink)
            for week in range(6) for column in range(7)
            if labels[week][column]
        ]
        fig.add_trace(go.Scatter(
            x=[p[0] for p in points], y=[p[1] for p in points],
            text=[p[2] for p in points], mode="text",
            textfont={"family": FONT, "size": 18, "color": [p[3] for p in points]},
            hoverinfo="skip", showlegend=False,
        ), row=row + 1, col=col + 1)
        fig.update_xaxes(
            tickmode="array", tickvals=list(range(7)),
            ticktext=["一", "二", "三", "四", "五", "六", "日"],
            tickfont={"size": 17, "color": "#73817B"},
            side="top", range=[-0.5, 6.5],
            showgrid=False, zeroline=False, ticks="", row=row + 1, col=col + 1,
        )
        fig.update_yaxes(
            visible=False, autorange="reversed", range=[5.5, -0.5],
            row=row + 1, col=col + 1,
        )
    fig.update_layout(
        width=1800, height=890,
        paper_bgcolor="#FBF9F5", plot_bgcolor="#FBF9F5",
        margin={"l": 56, "r": 56, "t": 220, "b": 125},
        font={"family": FONT, "size": 20, "color": calendar_ink},
        title={"text": "一年开车日历", "x": 0.031, "y": 0.962,
               "font": {"size": 38, "color": calendar_ink}},
    )
    fig.add_annotation(
        text="2025.10.01—2026.09.27  /  每格为当天可见卡片的估算里程",
        x=0, y=1.27, xref="paper", yref="paper", xanchor="left",
        showarrow=False, font={"size": 20, "color": "#71837D"},
    )
    for annotation in fig.layout.annotations[:12]:
        annotation.update(font={"size": 23, "color": calendar_ink}, yshift=28)
    legend = [
        ("无可见记录", colors[0]), ("<5 km", colors[1]),
        ("5–<10 km", colors[2]), ("10–<20 km", colors[3]),
        ("≥20 km", colors[4]),
    ]
    for i, (label, color) in enumerate(legend):
        x = 0.20 + i * 0.145
        fig.add_shape(type="rect", xref="paper", yref="paper",
                      x0=x, x1=x + 0.014, y0=-0.088, y1=-0.047,
                      line_width=0, fillcolor=color)
        fig.add_annotation(text=label, x=x + 0.019, y=-0.067,
                           xref="paper", yref="paper", xanchor="left",
                           showarrow=False, font={"size": 17, "color": calendar_ink})
    fig.add_annotation(text="浅灰仅表示无可见记录", x=0, y=-0.15,
                       xref="paper", yref="paper", xanchor="left",
                       showarrow=False, font={"size": 17, "color": "#71837D"})
    fig.add_annotation(text="可以叫我才哥", x=1, y=-0.15,
                       xref="paper", yref="paper", xanchor="right",
                       showarrow=False, font={"size": 17, "color": "#71837D"})
    return fig


def build_cumulative(df: pd.DataFrame) -> go.Figure:
    """按自然日累计页面可见卡片的估算里程。"""
    days = pd.date_range("2025-09-27", "2026-09-26", freq="D")
    daily = df.groupby("date_iso")["distance_km"].sum().reindex(days, fill_value=0)
    cumulative = daily.cumsum()
    frames_at = sorted(set(range(0, len(days), 10)) | {len(days) - 1})
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days[:1], y=cumulative.iloc[:1], mode="lines",
        line={"color": BLUE, "width": 5},
        fill="tozeroy", fillcolor="rgba(113,157,139,0.13)",
        hovertemplate="%{x|%Y-%m-%d}<br>累计 %{y:,.1f} km<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[days[0]], y=[cumulative.iloc[0]], mode="markers+text",
        marker={"size": 14, "color": ORANGE, "line": {"color": PAPER, "width": 2}},
            text=[""], textposition="top left",
        textfont={"size": 20, "color": INK}, showlegend=False,
        hovertemplate="%{x|%Y-%m-%d}<br>累计 %{y:,.1f} km<extra></extra>",
    ))
    fig.frames = [
        go.Frame(
            name=str(index), traces=[0, 1],
            data=[
                go.Scatter(x=days[:index + 1], y=cumulative.iloc[:index + 1]),
                go.Scatter(x=[days[index]], y=[cumulative.iloc[index]],
                           text=[f"{cumulative.iloc[index]:,.1f} km"
                                 if cumulative.iloc[index] > 0 else ""]),
            ],
        )
        for index in frames_at
    ]
    style(fig, "累计里程，怎样走到今天？", 600,
          "每日可见卡片的估算里程逐日累加；曲线按时间推进")
    fig.update_xaxes(title_text="日期", range=[days[0], days[-1]],
                     tickformat="%m月", dtick="M1")
    fig.update_yaxes(title_text="累计估算里程（km）",
                     range=[0, float(cumulative.max()) * 1.12])
    fig.update_layout(
        showlegend=False,
        updatemenus=[{
            "type": "buttons", "x": 0.01, "y": -0.23,
            "buttons": [
                {"label": "播放", "method": "animate",
                 "args": [None, {"frame": {"duration": 110, "redraw": True},
                                 "transition": {"duration": 0}, "fromcurrent": True}]},
                {"label": "暂停", "method": "animate",
                 "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                   "mode": "immediate"}]},
            ],
        }],
    )
    return fig


def export_animation(fig: go.Figure, path: Path) -> None:
    """用同一套 Plotly 图形生成可在公众号正文播放的 GIF。"""
    still = go.Figure(fig)
    still.frames = ()
    still.layout.updatemenus = ()
    images = []
    for frame in fig.frames:
        for target, source in zip(still.data, frame.data):
            target.x = source.x
            target.y = source.y
            if source.text is not None:
                target.text = source.text
        png = still.to_image(format="png", width=900, height=600, scale=1)
        image = Image.open(BytesIO(png)).convert("RGB")
        images.append(image.quantize(colors=96, method=Image.Quantize.FASTOCTREE))
    images[0].save(
        path, save_all=True, append_images=images[1:],
        duration=[110] * (len(images) - 1) + [1600],
        loop=0, optimize=True, disposal=2,
    )
    print(f"导出 {path.name}（{len(images)} 帧）")


def build_figures(df: pd.DataFrame, calendar_df: pd.DataFrame) -> list[tuple[str, go.Figure]]:
    is_demo = "data_kind" in df and df["data_kind"].eq("synthetic_demo").all()
    partial_months = set() if is_demo else {"2025-11", "2026-09"}
    figures: list[tuple[str, go.Figure]] = [
        ("图01_年度驾驶日历.png", build_calendar(calendar_df)),
        ("图02_累计里程动态曲线.gif", build_cumulative(df)),
    ]

    monthly = df.groupby("month", sort=True).agg(
        records=("distance_km", "size"), km=("distance_km", "sum")
    ).reset_index()
    monthly["month_label"] = monthly["month"].str.slice(2)
    peak_month = str(monthly.loc[monthly["km"].idxmax(), "month"])
    colors = [
        GRAY if m in partial_months else ORANGE if m == peak_month else BLUE
        for m in monthly["month"]
    ]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15)
    fig.add_trace(go.Bar(
        x=monthly["month_label"], y=monthly["records"], name="记录数",
        marker_color=colors, text=monthly["records"], textposition="outside",
        textfont={"size": 17}, cliponaxis=False,
        hovertemplate="%{x}<br>%{y} 条记录<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=monthly["month_label"], y=monthly["km"], name="估算里程",
        mode="lines+markers", line={"color": BLUE, "width": 5},
        marker={"size": 12, "color": [ORANGE if m == peak_month else BLUE for m in monthly["month"]]},
        text=monthly["km"].round(1),
        hovertemplate="%{x}<br>%{y:.1f} km<extra></extra>",
    ), row=2, col=1)
    under_one = int(df["distance_km_display"].astype(str).eq("<1").sum())
    style(fig, "月度记录与里程", 720,
          f"里程包含 {under_one} 条 <1 km 的估算" +
          ("；灰色柱为部分月份" if partial_months else ""))
    fig.update_xaxes(type="category", row=1, col=1)
    fig.update_xaxes(type="category", row=2, col=1)
    fig.update_yaxes(title_text="记录数（条）", row=1, col=1)
    fig.update_yaxes(title_text="里程（km）", row=2, col=1)
    fig.update_layout(showlegend=False, margin={"l": 95, "r": 65, "t": 105, "b": 85})
    figures.append(("图03_月度记录与里程.png", fig))

    hourly = df.groupby(["hour", "day_type"]).size().unstack(fill_value=0).reindex(
        index=range(24), fill_value=0
    )
    fig = go.Figure()
    for day_type, color in [("工作日", BLUE), ("周末", TEAL)]:
        fig.add_trace(go.Bar(
            x=hourly.index, y=hourly.get(day_type, pd.Series(0, index=hourly.index)),
            name=day_type, marker_color=color,
            hovertemplate="%{x}:00<br>%{y} 条<extra>" + day_type + "</extra>",
        ))
    fig.update_layout(barmode="stack", bargap=0.2)
    peak_hours = hourly.sum(axis=1).nlargest(2).index.tolist()
    style(fig, "一天里，什么时候出发？", 590,
          f"{peak_hours[0]} 点与 {peak_hours[1]} 点是可见记录的两个高峰")
    fig.update_xaxes(title_text="开始小时", tickmode="array", tickvals=list(range(0, 24, 2)))
    fig.update_yaxes(title_text="记录数（条）")
    for hour in peak_hours:
        fig.add_vrect(x0=hour - 0.5, x1=hour + 0.5,
                      fillcolor=ORANGE, opacity=0.12, line_width=0)
    figures.append(("图04_一天出发时间分布.png", fig))

    matrix = df.groupby(["weekday", "hour"]).size().unstack(fill_value=0).reindex(
        index=range(7), columns=range(24), fill_value=0
    )
    fig = go.Figure(go.Heatmap(
        z=matrix.values, x=[f"{h:02d}" for h in range(24)],
        y=["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
        colorscale=[[0, "#F0F4EC"], [0.45, "#A8CBB8"], [1, "#578875"]],
        zmin=0, zmax=int(matrix.values.max()),
        xgap=3, ygap=5,
        colorbar={"title": {"text": "条"}, "tickfont": {"size": 18}, "len": 0.78},
        hovertemplate="%{y} %{x}:00<br>%{z} 条<extra></extra>",
    ))
    style(fig, "星期 × 小时：通勤节律", 560, "颜色越深，当前星期与小时的轨迹卡片越多")
    fig.update_xaxes(title_text="开始小时", tickmode="array",
                     tickvals=[f"{h:02d}" for h in range(0, 24, 2)])
    fig.update_yaxes(autorange="reversed")
    figures.append(("图05_星期小时热力图.png", fig))

    band_labels = ["<1", "1–<5", "5–<10", "10–<20", "≥20"]
    distances = df["distance_km"]
    band_counts = [
        int(df["distance_km_display"].astype(str).eq("<1").sum()),
        int(((distances >= 1) & (distances < 5)).sum()),
        int(((distances >= 5) & (distances < 10)).sum()),
        int(((distances >= 10) & (distances < 20)).sum()),
        int((distances >= 20).sum()),
    ]
    fig = go.Figure(go.Bar(
        x=band_labels, y=band_counts,
        marker_color=[TEAL, BLUE, ORANGE, GRAY, GRAY],
        text=[f"{n} 条<br>{n / len(df):.1%}" for n in band_counts],
        textposition="outside", textfont={"size": 21}, cliponaxis=False,
        hovertemplate="%{x} km<br>%{y} 条<extra></extra>",
    ))
    style(fig, "短途占了大多数", 580,
          f"{sum(band_counts[:3])} / {len(df)} 条记录短于 10 km")
    fig.update_xaxes(title_text="单次估算里程（km）")
    fig.update_yaxes(title_text="记录数（条）", range=[0, max(band_counts) * 1.2])
    figures.append(("图06_单次里程分布.png", fig))

    top_routes = df["route"].value_counts().head(8)
    aliases = [f"线路 {i:02d}" for i in range(1, len(top_routes) + 1)]
    fig = go.Figure(go.Bar(
        x=top_routes.values, y=aliases, orientation="h",
        marker_color=[ORANGE, ORANGE] + [GRAY] * max(0, len(top_routes) - 2),
        text=top_routes.values, textposition="outside",
        textfont={"size": 21}, cliponaxis=False,
        hovertemplate="%{y}<br>%{x} 条<extra></extra>",
    ))
    style(fig, "常走的线路，重复度有多高？", 620, "起终点按页面原文精确匹配；具体地名已匿名")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title_text="轨迹卡片数（条）",
                     range=[0, float(top_routes.iloc[0]) * 1.2])
    figures.append(("图07_常见线路匿名排行.png", fig))

    if len(top_routes) >= 2:
        fig = go.Figure()
        peak_labels = []
        for alias, route, color in [
            ("线路 01", top_routes.index[0], ORANGE),
            ("线路 02", top_routes.index[1], BLUE),
        ]:
            route_hours = df.loc[df["route"].eq(route), "hour"].value_counts().reindex(
                range(24), fill_value=0
            )
            peak_hour = int(route_hours.idxmax())
            peak_labels.append(f"{alias} 在 {peak_hour} 点有 {int(route_hours.max())} 条")
            fig.add_trace(go.Bar(
                x=route_hours.index, y=route_hours.values, name=alias,
                marker_color=color,
                hovertemplate="%{x}:00<br>%{y} 条<extra>" + alias + "</extra>",
            ))
        fig.update_layout(barmode="group", bargap=0.22, bargroupgap=0.06)
        style(fig, "两条高频线路，分别在何时出发？", 590, "；".join(peak_labels))
        fig.update_xaxes(title_text="开始小时", tickmode="array", tickvals=list(range(0, 24, 2)))
        fig.update_yaxes(title_text="记录数（条）")
        figures.append(("图08_高频线路出发小时.png", fig))

    fig = go.Figure(go.Scatter(
        x=df["distance_km"], y=df["average_speed"], mode="markers",
        marker={"size": 10, "opacity": 0.8, "color": df["duration_min"],
                "colorscale": [[0, "#BCD4C2"], [0.5, "#8DB59D"], [1, "#578875"]],
                "colorbar": {"title": {"text": "时长<br>分钟"}, "tickfont": {"size": 17}}},
        customdata=df[["duration_min"]].to_numpy(),
        hovertemplate="里程 %{x:.1f} km<br>均速 %{y:.0f} km/h<br>时长 %{customdata[0]:.1f} 分钟<extra></extra>",
    ))
    style(fig, "里程 × 平均速度 × 时长", 600, "横轴里程，纵轴均速，颜色表示记录时长")
    fig.update_xaxes(title_text="估算里程（km）", range=[0, 55])
    fig.update_yaxes(title_text="平均速度（km/h）",
                     range=[0, float(df["average_speed"].max()) * 1.12])
    figures.append(("图09_里程速度时长散点.png", fig))

    monthly_speed = df.groupby("month", sort=True).agg(
        mean_speed=("average_speed", "mean"), records=("average_speed", "size")
    ).reset_index()
    monthly_speed["label"] = monthly_speed["month"].str.slice(2)
    compare_months = set() if is_demo else {"2025-12", "2026-08"}
    speed_colors = [
        GRAY if month in partial_months else
        ORANGE if month in compare_months else BLUE
        for month in monthly_speed["month"]
    ]
    fig = go.Figure(go.Scatter(
        x=monthly_speed["label"], y=monthly_speed["mean_speed"],
        mode="lines+markers+text",
        line={"color": BLUE, "width": 5},
        marker={"size": 14, "color": speed_colors,
                "line": {"color": PAPER, "width": 2}},
        text=[f"{speed:.1f}" if month in compare_months else ""
              for month, speed in zip(monthly_speed["month"], monthly_speed["mean_speed"])],
        textposition="top center", textfont={"size": 19, "color": INK},
        customdata=monthly_speed[["records"]].to_numpy(),
        hovertemplate="%{x}<br>卡片均速均值 %{y:.1f} km/h<br>%{customdata[0]} 条记录<extra></extra>",
    ))
    style(fig, "月度平均速度", 580,
          "每张卡片页面均速的算术平均" +
          ("；灰色点为部分月份" if partial_months else ""))
    fig.update_xaxes(title_text="月份", type="category")
    fig.update_yaxes(title_text="卡片均速均值（km/h）", range=[10, 21], dtick=2)
    fig.update_layout(showlegend=False)
    figures.append(("图10_月度平均速度.png", fig))
    return figures


def write_outputs(
    df: pd.DataFrame, figures: list[tuple[str, go.Figure]], output_dir: Path
) -> None:
    image_dir = output_dir / "配图"
    data_dir = output_dir / "数据"
    image_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename, fig in figures:
        if filename.endswith(".gif"):
            export_animation(fig, image_dir / filename)
        else:
            fig.write_image(image_dir / filename, width=fig.layout.width or IMAGE_WIDTH, scale=2)
            print(f"导出 {filename}")
    monthly_km = df.groupby("month", sort=True)["distance_km"].sum()
    cover = go.Figure(go.Scatter(
        x=list(range(len(monthly_km))), y=monthly_km.values, mode="lines+markers",
        line={"color": "#CB9071", "width": 5}, marker={"size": 10},
        fill="tozeroy", fillcolor="rgba(203,144,113,0.14)",
        hoverinfo="skip",
    ))
    cover.update_layout(
        width=900, height=383, paper_bgcolor="#EAF2E8", plot_bgcolor="#EAF2E8",
        margin={"l": 25, "r": 25, "t": 15, "b": 15},
        font={"family": FONT}, showlegend=False,
        xaxis={"domain": [0.57, 0.98], "visible": False},
        yaxis={"domain": [0.17, 0.82], "visible": False, "range": [0, 500]},
    )
    for text, x, y, size, color in [
        ("拿驾照一年", 0.04, 0.78, 38, INK),
        ("开车记录藏着什么？", 0.04, 0.60, 38, INK),
        ("Plotly · 多维数据可视化", 0.04, 0.38, 22, "#4B725F"),
        (f"{len(df)} 条记录  /  {df['distance_km'].sum():,.0f} km", 0.04, 0.23, 23, "#986049"),
        ("可以叫我才哥", 0.04, 0.08, 17, "#5A7264"),
    ]:
        cover.add_annotation(
            text=text, x=x, y=y, xref="paper", yref="paper", xanchor="left",
            showarrow=False, font={"size": size, "color": color, "family": FONT},
        )
    cover.write_image(image_dir / "封面.png", width=900, height=383, scale=2)
    print("导出 封面.png")
    sections = []
    for index, (filename, fig) in enumerate(figures):
        sections.append(f"<section><h2>{filename[3:-4]}</h2>" + to_html(
            fig, full_html=False, include_plotlyjs="inline" if index == 0 else False,
            config={"responsive": True, "displaylogo": False},
        ) + "</section>")
    is_demo = "data_kind" in df and df["data_kind"].eq("synthetic_demo").all()
    source_note = (
        "本页使用独立生成的虚构驾车卡片；路线以示例点编号表示。"
        if is_demo else "本页使用高德页面可见驾车卡片；线路以编号表示。"
    )
    html = (
        "<!doctype html><html lang='zh-CN'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<link rel='icon' href='data:,'>"
        "<title>驾照一周年 · Plotly 交互图表</title>"
        "<style>body{font-family:Microsoft YaHei,Arial,sans-serif;max-width:980px;margin:auto;"
        "padding:20px;color:#30483E;background:#FFF9F1}section{margin:28px 0;border:1px solid #DFE9DE;"
        "border-radius:18px;overflow-x:auto;overflow-y:hidden}h1,h2{padding:0 22px}h2{font-size:20px}"
        ".note{color:#5A7264;font-size:14px;line-height:1.6}</style>"
        "<h1>驾照一周年 · Plotly 交互图表</h1>"
        f"<p class='note'>{source_note}"
        "图表可悬停查看数值；手机上可左右滑动图表。</p>"
        + "".join(sections) + "</html>"
    )
    (output_dir / "Plotly交互图表.html").write_text(html, encoding="utf-8")

    top = df["route"].value_counts()
    hours = df["hour"].value_counts()
    summary = {
        "period_start": "2025-09-27", "period_end_exclusive": "2026-09-27",
        "visible_start": df["date_iso"].min().strftime("%Y-%m-%d"),
        "visible_end": df["date_iso"].max().strftime("%Y-%m-%d"),
        "records": int(len(df)), "active_dates": int(df["date_iso"].nunique()),
        "estimated_km": round(float(df["distance_km"].sum()), 1),
        "recorded_hours": round(float(df["duration_min"].sum() / 60), 1),
        "median_distance_km": float(df["distance_km"].median()),
        "under_10_km": int((df["distance_km"] < 10).sum()),
        "weekday_records": int(df["weekday"].lt(5).sum()),
        "weekend_records": int(df["weekday"].ge(5).sum()),
        "hour_10": int(hours.get(10, 0)), "hour_20": int(hours.get(20, 0)),
        "top_two_route_records": int(top.iloc[:2].sum()),
        "top_route_counts_anonymous": {f"线路{i:02d}": int(n)
                                       for i, n in enumerate(top.iloc[:8], 1)},
        "longest_record_km": float(df["distance_km"].max()),
        "under_one_count": int(df["distance_km_display"].astype(str).eq("<1").sum()),
        "monthly": [
            {"month": str(row.month), "records": int(row.records),
             "estimated_km": round(float(row.km), 1),
             "mean_page_speed_kmh": round(float(row.mean_speed), 2),
             "median_page_speed_kmh": float(row.median_speed)}
            for row in df.groupby("month", sort=True).agg(
                records=("distance_km", "size"), km=("distance_km", "sum"),
                mean_speed=("average_speed", "mean"),
                median_speed=("average_speed", "median")
            ).reset_index().itertuples()
        ],
    }
    (data_dir / "匿名统计摘要.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("统计验收", json.dumps({
        key: summary[key] for key in ["records", "active_dates", "estimated_km",
                                      "recorded_hours", "hour_10", "hour_20"]
    }, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="用 Plotly 绘制驾照一周年驾驶数据")
    parser.add_argument("--csv", required=True, type=Path, help="本地私人驾车行程 CSV 路径")
    parser.add_argument("--output", type=Path, default=ROOT, help="图表输出目录")
    args = parser.parse_args()
    calendar_df = read_trips(args.csv)
    df = calendar_df.loc[calendar_df["date_iso"] < "2026-09-27"].copy()
    write_outputs(df, build_figures(df, calendar_df), args.output)


if __name__ == "__main__":
    main()
