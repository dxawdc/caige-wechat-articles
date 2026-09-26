"""Render sector-return racing videos from verified daily closes."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter
from matplotlib.ticker import FuncFormatter, MaxNLocator
from matplotlib.transforms import blended_transform_factory

from palette import BOARD_COLORS
from prepare_data import AS_OF, OUT, calendar, themes

ROOT = Path(__file__).resolve().parent
VIDEOS = ROOT / "videos"
VIDEO_FPS = 36
TWEEN_FRAMES = 8
PORTRAIT_SIZE = (1080, 1920)
PORTRAIT_TWEEN_FRAMES = 12
PORTRAIT_INTRO_SECONDS = 1
PORTRAIT_OUTRO_SECONDS = 3


def load() -> tuple[list[str], list[tuple[str, str]], dict[tuple[str, str], float]]:
    if not OUT.exists():
        raise FileNotFoundError(f"Verified data not found: {OUT}. Run prepare_data.py first.")
    pairs = themes()
    names = dict(pairs)
    days = calendar()
    prices = {}
    with OUT.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            day, code = row["date"], row["code"]
            if code not in names or day not in days:
                raise ValueError(f"Unexpected row: {code} {day}")
            value = float(row["close"])
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid close: {code} {day}")
            prices[day, code] = value
    for code in names:
        present = [day for day in days if (day, code) in prices]
        if not present or present[-1] != AS_OF:
            raise ValueError(f"Incomplete board: {code}")
        if any((day, code) not in prices for day in days if present[0] <= day <= present[-1]):
            raise ValueError(f"Trading-day gap: {code}")
    return days, pairs, prices


def values(days: list[str], pairs: list[tuple[str, str]], prices: dict, start: str):
    window = [day for day in days if day >= start]
    if not window:
        raise ValueError(f"No trading days from {start}")
    codes = [code for code, _ in pairs]
    arr = np.full((len(codes), len(window)), np.nan)
    omitted = []
    for i, code in enumerate(codes):
        base_days = [day for day in days if day < start and (day, code) in prices]
        if not base_days:
            omitted.append(code)
            continue
        base = prices[base_days[-1], code]
        for j, day in enumerate(window):
            if (day, code) in prices:
                arr[i, j] = (prices[day, code] / base - 1) * 100
    return window, arr, omitted


def rolling_returns(days: list[str], pairs: list[tuple[str, str]], prices: dict, length: int = 20):
    """Return one trailing-window return per board and ending trading day."""
    if len(days) <= length:
        raise ValueError(f"At least {length + 1} trading days are required")
    ending_days = days[length:]
    window_starts = []
    arr = np.full((len(pairs), len(ending_days)), np.nan)
    for col, end_index in enumerate(range(length, len(days))):
        base_day = days[end_index - length]
        window = days[end_index - length + 1:end_index + 1]
        window_starts.append(window[0])
        for row, (code, _) in enumerate(pairs):
            if (base_day, code) in prices and all((day, code) in prices for day in window):
                arr[row, col] = (prices[window[-1], code] / prices[base_day, code] - 1) * 100
    return ending_days, window_starts, arr


def monotone_slope(previous: float, current: float, following: float) -> float:
    incoming, outgoing = current - previous, following - current
    if incoming * outgoing <= 0:
        return 0.0
    return 2 * incoming * outgoing / (incoming + outgoing)


def smooth_value(previous: float | None, start: float, end: float,
                 following: float | None, fraction: float) -> float:
    delta = end - start
    first = delta if previous is None else monotone_slope(previous, start, end)
    last = delta if following is None else monotone_slope(start, end, following)
    t, t2, t3 = fraction, fraction ** 2, fraction ** 3
    return ((2 * t3 - 3 * t2 + 1) * start + (t3 - 2 * t2 + t) * first
            + (-2 * t3 + 3 * t2) * end + (t3 - t2) * last)


def draw_video_smooth(window, pairs, arr, start, target, rolling_starts=None,
                      fps: int = VIDEO_FPS, tween_frames: int = TWEEN_FRAMES,
                      axis_follow: bool = False, portrait: bool = False,
                      preview_at: int | None = None):
    """Animate line endpoints and all available bars between actual trading days."""
    plt.rcParams.update({
        "font.family": "Microsoft YaHei", "axes.unicode_minus": False,
        "figure.facecolor": "#f0f3f1", "axes.facecolor": "#ffffff",
        "text.color": "#263841", "axes.labelcolor": "#607276",
        "xtick.color": "#819093", "ytick.color": "#819093",
    })
    if portrait:
        fig = plt.figure(figsize=(10.8, 19.2), dpi=100)
        ax = fig.add_axes([.095, .655, .83, .18])
        race = fig.add_axes([.225, .045, .70, .535])
    else:
        fig = plt.figure(figsize=(14.4, 13), dpi=100)
        ax = fig.add_axes([.075, .625, .85, .245])
        race = fig.add_axes([.18, .05, .745, .49])
    rolling = rolling_starts is not None
    heading = "A股主题板块轮动｜滚动20日涨跌幅" if rolling else "A股主题板块轮动｜累计涨跌幅"
    subtitle = (f"{start} 至 {AS_OF}  ·  最近20交易日累计收益" if rolling
                else f"{start} 至 {AS_OF}  ·  东方财富板块指数")
    if axis_follow:
        subtitle += "  ·  动态坐标轴"
    if portrait:
        fig.text(.095, .978, "9·24之后，谁跑在前面？", fontsize=31, weight="bold")
        fig.text(.095, .947,
                 f"{start.replace('-', '.')}—{AS_OF.replace('-', '.')} · 东方财富主题板块指数",
                 fontsize=14.5, color="#718083")
        date_artist = fig.text(.095, .910, "", ha="left", fontsize=30,
                               weight="bold", color="#a86b43")
        note_artist = fig.text(.925, .910, "", ha="right", fontsize=12.5,
                               color="#718083")
        fig.text(.095, .881, "累计涨跌幅 · 动态坐标轴" if axis_follow else "累计涨跌幅 · 固定坐标轴",
                 fontsize=13.5, color="#718083")
    else:
        fig.text(.075, .952, heading, fontsize=24, weight="bold")
        fig.text(.075, .919, subtitle, fontsize=11, color="#718083")
        date_artist = fig.text(.925, .952, "", ha="right", fontsize=21, weight="bold", color="#a86b43")
        note_artist = fig.text(.925, .919, "", ha="right", fontsize=11, color="#718083")

    n = len(pairs)
    names = [name for _, name in pairs]
    hues = BOARD_COLORS
    finite = arr[np.isfinite(arr)]
    if not len(finite):
        raise ValueError(f"No valid returns from {start}")
    lo, hi = float(np.min(finite)), float(np.max(finite))
    pad = max((hi - lo) * .07, 4)
    if not axis_follow:
        ax.set_xlim(0, max(1, len(window) - 1))
        ax.set_ylim(min(0, lo - pad), max(0, hi + pad))
        ticks = np.linspace(0, len(window) - 1, min(6, len(window)), dtype=int)
        ax.set_xticks(ticks, [window[k][2:7] for k in ticks])
    else:
        ax.set_xlim(0, min(max(10, 1), len(window) - 1))
    ax.axhline(0, color="#89969a", linewidth=1.1)
    ax.grid(axis="y", color="#e7ebe9", linewidth=.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylabel("涨跌幅 %", fontsize=13 if portrait else 10)
    if portrait:
        ax.tick_params(axis="both", labelsize=12, pad=7)
    curve_title = "滚动20日涨跌幅曲线" if rolling else "板块累计涨跌幅曲线"
    ax.set_title(curve_title, loc="left", fontsize=19 if portrait else 14,
                 weight="bold", pad=16 if portrait else 12)
    lines = [ax.plot([], [], color=hues[i], linewidth=1, alpha=.3, zorder=2)[0] for i in range(n)]
    cursor = ax.axvline(0, color="#9da9aa", linewidth=1, alpha=.47)

    race.set_ylim(n - .45, -.6)
    race.set_yticks([])
    race.xaxis.set_ticks_position("top")
    race.tick_params(axis="x", labeltop=True, labelbottom=False,
                     labelsize=13 if portrait else 10, pad=6 if portrait else 5)
    race.xaxis.set_major_locator(MaxNLocator(nbins=7))
    race.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}%"))
    race.grid(axis="x", linestyle="--", color="#e5eae8", linewidth=.8)
    race.set_axisbelow(True)
    race.axvline(0, color="#778587", linewidth=1.2)
    race.spines[["top", "right", "bottom", "left"]].set_visible(False)
    ranking_title = "当前20日涨跌幅排名" if rolling else "当前累计涨跌幅排名"
    fig.text(.095 if portrait else .075, .618 if portrait else .565,
             ranking_title, fontsize=19 if portrait else 14, weight="bold")
    for rank in range(1, n, 2):
        race.axhspan(rank - .5, rank + .5, color="#f7f9f8", zorder=0)
    name_transform = blended_transform_factory(
        fig.transFigure if portrait else race.transAxes, race.transData)
    bars, name_artists, value_artists = [], [], []
    for i in range(n):
        bars.append(race.barh(i, 0, height=.72, color=hues[i], edgecolor="white", linewidth=.35)[0])
        name_artists.append(race.text(.095 if portrait else -.012, i, names[i],
                                      ha="left" if portrait else "right", va="center",
                                      transform=name_transform, fontsize=19 if portrait else 10.5,
                                      color="#293b42"))
        value_artists.append(race.text(0, i, "", ha="left", va="center",
                                         fontsize=17 if portrait else 9.5, color="#42525a"))

    def ranks(values):
        order = sorted(range(n), key=lambda i: (not np.isfinite(values[i]),
                                                 -float(values[i]) if np.isfinite(values[i]) else 0, i))
        positions = np.empty(n, dtype=float)
        for rank, index in enumerate(order):
            positions[index] = rank
        return positions

    rank_matrix = np.stack([ranks(arr[:, day]) for day in range(len(window))])
    prefix_min = np.zeros(len(window), dtype=float)
    prefix_max = np.zeros(len(window), dtype=float)
    for day in range(len(window)):
        valid = arr[:, day]
        valid = valid[np.isfinite(valid)]
        prefix_min[day] = min(0, prefix_min[day - 1] if day else 0,
                              float(np.min(valid)) if len(valid) else 0)
        prefix_max[day] = max(0, prefix_max[day - 1] if day else 0,
                              float(np.max(valid)) if len(valid) else 0)
    axis_bounds = None
    line_bounds = None

    def update(day_index: int, fraction: float) -> None:
        nonlocal axis_bounds, line_bounds
        previous_index = max(0, day_index - 1)
        before, after = arr[:, previous_index], arr[:, day_index]
        current = np.zeros(n, dtype=float)
        visibility = np.zeros(n, dtype=float)
        for i in range(n):
            old_ok, new_ok = np.isfinite(before[i]), np.isfinite(after[i])
            if old_ok and new_ok:
                prior = arr[i, previous_index - 1] if previous_index > 0 else np.nan
                following = arr[i, day_index + 1] if day_index + 1 < len(window) else np.nan
                current[i] = smooth_value(
                    float(prior) if np.isfinite(prior) else None,
                    float(before[i]), float(after[i]),
                    float(following) if np.isfinite(following) else None, fraction,
                )
                visibility[i] = 1
            elif new_ok:
                current[i] = float(after[i])
                visibility[i] = fraction * fraction * (3 - 2 * fraction)
            elif old_ok:
                current[i] = float(before[i])
                visibility[i] = 1 - fraction
        visible_values = current[visibility > .001]
        min_value = min(0, float(np.min(visible_values))) if len(visible_values) else 0
        max_value = max(0, float(np.max(visible_values))) if len(visible_values) else 0
        if axis_follow:
            seen_lo = min(float(prefix_min[previous_index]), min_value)
            seen_hi = max(float(prefix_max[previous_index]), max_value)
            line_pad = max((seen_hi - seen_lo) * .07, 4)
            target_line = (seen_lo - line_pad, seen_hi + line_pad)
            if line_bounds is None:
                line_bounds = target_line
            else:
                blend = 1 - math.exp(-(1000 / fps) / 270)
                line_bounds = (
                    min(line_bounds[0] + (target_line[0] - line_bounds[0]) * blend,
                        seen_lo - line_pad * .2),
                    max(line_bounds[1] + (target_line[1] - line_bounds[1]) * blend,
                        seen_hi + line_pad * .2),
                )
            ax.set_ylim(*line_bounds)
            progress = previous_index + fraction if day_index else 0
            latest_tick = min(len(window) - 1, max(10, math.floor(progress)))
            ax.set_xlim(0, min(len(window) - 1, max(10, progress)))
            ticks = np.unique(np.rint(np.linspace(0, latest_tick, 6)).astype(int))
            tick_format = (lambda k: window[k][5:]) if latest_tick < 120 else (lambda k: window[k][2:7])
            ax.set_xticks(ticks, [tick_format(int(k)) for k in ticks])
        bar_pad = max((max_value - min_value) * .15, .7)
        current_lo, current_hi = min_value - bar_pad, max_value + bar_pad
        future = arr[:, day_index:min(day_index + 3, len(window))]
        future = future[np.isfinite(future)]
        future_min = min(min_value, float(np.min(future))) if len(future) else min_value
        future_max = max(max_value, float(np.max(future))) if len(future) else max_value
        future_pad = max((future_max - future_min) * .15, .7)
        target_lo, target_hi = future_min - future_pad, future_max + future_pad
        if axis_bounds is None:
            axis_bounds = (target_lo, target_hi)
        else:
            blend = 1 - math.exp(-(1000 / fps) / 270)
            axis_bounds = (min(axis_bounds[0] + (target_lo - axis_bounds[0]) * blend, current_lo),
                           max(axis_bounds[1] + (target_hi - axis_bounds[1]) * blend, current_hi))
        race.set_xlim(*axis_bounds)
        label_pad = max((max_value - min_value) * .015, .1)
        moving_ranks = np.empty(n, dtype=float)
        for i in range(n):
            prior_rank = rank_matrix[previous_index - 1, i] if previous_index > 0 else None
            following_rank = rank_matrix[day_index + 1, i] if day_index + 1 < len(window) else None
            moving_ranks[i] = smooth_value(prior_rank, rank_matrix[previous_index, i],
                                           rank_matrix[day_index, i], following_rank, fraction)
        clearance = np.ones(n, dtype=float)
        sorted_ranks = sorted((moving_ranks[i], i) for i in range(n))
        for index, (position, board_index) in enumerate(sorted_ranks):
            gap_before = position - sorted_ranks[index - 1][0] if index else 1
            gap_after = sorted_ranks[index + 1][0] - position if index + 1 < n else 1
            gap = min(gap_before, gap_after)
            clearance[board_index] = max(0, min(1, (gap - .25) / .6))
        for i in range(n):
            rank = moving_ranks[i]
            value = current[i]
            bar = bars[i]
            bar.set_y(rank - .36)
            bar.set_x(min(0, value))
            bar.set_width(abs(value))
            prominence = max(0, min(1, (5 - rank) / 5))
            bar.set_alpha((.77 + .23 * prominence) * (.72 if value < 0 else 1) * visibility[i])
            name_artists[i].set_y(rank)
            name_artists[i].set_alpha(visibility[i] * clearance[i])
            value_artists[i].set_position((value + label_pad if value >= 0 else value - label_pad, rank))
            value_artists[i].set_text(f"{value:+.1f}%" if visibility[i] > .001 else "")
            value_artists[i].set_ha("left" if value >= 0 else "right")
            value_artists[i].set_alpha(visibility[i] * clearance[i])
            if day_index == 0:
                xdata = np.array([0.0])
                ydata = np.array([after[i]])
            else:
                xdata = np.arange(day_index + 1, dtype=float)
                xdata[-1] = day_index - 1 + fraction
                ydata = arr[i, :day_index + 1].copy()
                ydata[-1] = value if visibility[i] > .001 else np.nan
            line = lines[i]
            line.set_data(xdata, ydata)
            focus = max(0, min(1, (7 - rank) / 4))
            line.set_alpha((.17 + .75 * focus) * visibility[i])
            line.set_linewidth((1.25 + 1.65 * focus) if portrait else (.9 + 1.35 * focus))
        cursor.set_xdata([previous_index + fraction] * 2)
        if day_index > 0 and fraction < 1:
            date_artist.set_text(window[previous_index])
            note_artist.set_text(f"过渡至 {window[day_index]}" if not rolling else
                                 f"窗口 {rolling_starts[previous_index]} 至 {window[previous_index]} · 过渡至 {window[day_index]}")
        else:
            date_artist.set_text(window[day_index])
            note_artist.set_text(f"当前窗口 {rolling_starts[day_index]} 至 {window[day_index]}" if rolling else "")

    if preview_at is not None:
        update(preview_at, 1)
        fig.savefig(target, dpi=100)
        plt.close(fig)
        return

    writer = FFMpegWriter(fps=fps, codec="libx264", bitrate=4800 if portrait else 5600,
                          extra_args=["-preset", "veryfast", "-pix_fmt", "yuv420p",
                                      "-movflags", "+faststart"])
    with writer.saving(fig, str(target), dpi=100):
        for day_index in range(len(window)):
            if day_index == 0:
                update(0, 1)
                for _ in range(fps * PORTRAIT_INTRO_SECONDS if portrait else max(1, fps // 2)):
                    writer.grab_frame()
            else:
                for step in range(1, tween_frames + 1):
                    update(day_index, step / tween_frames)
                    writer.grab_frame()
        for _ in range(fps * PORTRAIT_OUTRO_SECONDS if portrait else fps):
            update(len(window) - 1, 1)
            writer.grab_frame()
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", "--start", dest="window", choices=("2026-01-01", "2024-09-24", "20d"),
                        help="Render one window; by default render all three")
    parser.add_argument("--axis-follow", action="store_true",
                        help="Write a separate version whose line axes expand with observed history")
    parser.add_argument("--portrait", action="store_true",
                        help="Render a 1080x1920 phone video with a slower 2024-09-24 timeline")
    args = parser.parse_args()
    if args.portrait and args.window != "2024-09-24":
        parser.error("--portrait requires --window 2024-09-24")
    days, pairs, prices = load()
    if len(days) < 21:
        raise ValueError("At least 21 trading days are needed for a 20-day return window")
    VIDEOS.mkdir(exist_ok=True)
    for key, label in (("2026-01-01", "2026年初至今"),
                       ("2024-09-24", "2024年9月24日至今"),
                       ("20d", "滚动20个交易日")):
        if args.window and key != args.window:
            continue
        if key == "20d":
            window, rolling_starts, arr = rolling_returns(days, pairs, prices)
            start = window[0]
        else:
            start = key
            window, arr, _ = values(days, pairs, prices, start)
            rolling_starts = None
        suffix = "_动态坐标轴" if args.axis_follow else ""
        if args.portrait:
            suffix += "_手机竖屏"
        target = VIDEOS / f"{label}_累计涨跌幅{suffix}.mp4"
        temp = target.with_name(target.stem + ".tmp.mp4")
        frames = PORTRAIT_TWEEN_FRAMES if args.portrait else TWEEN_FRAMES
        print(f"Rendering {target.name}: {len(window)} dates, {frames} transition frames per day", flush=True)
        draw_video_smooth(window, pairs, arr, start, temp, rolling_starts,
                          tween_frames=frames, axis_follow=args.axis_follow,
                          portrait=args.portrait)
        temp.replace(target)
        print(f"Saved {target}", flush=True)


if __name__ == "__main__":
    main()
