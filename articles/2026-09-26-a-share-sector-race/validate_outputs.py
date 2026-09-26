"""Validate the current racing videos and refresh their acceptance manifest."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np

from palette import BOARD_COLORS
from render_videos import (ROOT, VIDEOS, VIDEO_FPS, TWEEN_FRAMES, PORTRAIT_SIZE,
                           PORTRAIT_TWEEN_FRAMES, PORTRAIT_INTRO_SECONDS,
                           PORTRAIT_OUTRO_SECONDS, load, rolling_returns, values)


WINDOWS = (
    ("2024-09-24", "2024年9月24日至今"),
    ("2026-01-01", "2026年初至今"),
    ("20d", "滚动20个交易日"),
)
FPS = VIDEO_FPS
SIZE = (1440, 1300)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def validate_video(path: Path, trading_days: int, size: tuple[int, int] = SIZE,
                   tween_frames: int = TWEEN_FRAMES,
                   intro_frames: int = FPS // 2, outro_frames: int = FPS) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    probe = json.loads(run(
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,avg_frame_rate,nb_frames",
        "-show_entries", "format=duration", "-of", "json", str(path),
    ).stdout)
    stream = probe["streams"][0]
    frames = int(stream["nb_frames"])
    expected_frames = intro_frames + (trading_days - 1) * tween_frames + outro_frames
    assert stream["codec_name"] == "h264", path
    assert (stream["width"], stream["height"]) == size, path
    assert Fraction(stream["avg_frame_rate"]) == FPS, path
    assert frames == expected_frames, (path, frames, expected_frames)
    run("ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-f", "null", "-")
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "file": path.relative_to(ROOT).as_posix(),
        "codec": stream["codec_name"],
        "width": stream["width"],
        "height": stream["height"],
        "fps": FPS,
        "frames": frames,
        "duration_seconds": round(float(probe["format"]["duration"]), 3),
        "size_bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
        "decoded_successfully": True,
    }


def validate_html(days: list[str], pairs: list[tuple[str, str]], prices: dict,
                  axis_follow: bool = False) -> dict:
    suffix = "_动态坐标轴" if axis_follow else ""
    path = ROOT / f"A股板块轮动赛马图{suffix}.html"
    html = path.read_text(encoding="utf-8")
    match = re.search(r'<script id="race-data" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise ValueError("Missing embedded chart data")
    data = json.loads(match.group(1))
    assert data["asOf"] == days[-1]
    assert bool(data.get("axisFollow", False)) == axis_follow
    assert [(item["code"], item["name"]) for item in data["boards"]] == pairs
    assert data["colors"] == list(BOARD_COLORS)
    assert len(data["modes"]) == 3
    for mode in data["modes"]:
        if mode["id"] == "20d":
            dates, starts, arr = rolling_returns(days, pairs, prices)
            assert mode["windowStarts"] == starts
        else:
            dates, arr, _ = values(days, pairs, prices, mode["id"])
            assert mode["windowStarts"] is None
        assert mode["dates"] == dates
        expected = [[round(float(value), 4) if np.isfinite(value) else None for value in row] for row in arr]
        assert mode["series"] == expected, mode["id"]
    assert "/*__INLINE_CSS__*/" not in html and "/*__INLINE_JS__*/" not in html
    assert all(label not in html for label in ("板块有值", "缺少此区间", "个主题"))
    if axis_follow:
        assert "坐标轴随曲线伸展" in html
    return {
        "file": path.relative_to(ROOT).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "boards": len(pairs),
        "modes": [mode["id"] for mode in data["modes"]],
        "embedded_data_verified": True,
        "axis_follow": axis_follow,
    }


def main() -> None:
    days, pairs, prices = load()
    rolling_days, rolling_starts, rolling_arr = rolling_returns(days, pairs, prices)
    first_dates = {
        code: next(day for day in days if (day, code) in prices)
        for code, _ in pairs
    }
    manifest = {
        "as_of": days[-1],
        "source": "Eastmoney board-index daily K-line, fqt=0",
        "boards": len(pairs),
        "reference_trading_days": len(days),
        "daily_rows": len(prices),
        "late_start_boards": {
            code: f"{name}，{first_dates[code]}起"
            for code, name in pairs if first_dates[code] > days[0]
        },
        "animation": {
            "canvas": f"{SIZE[0]}x{SIZE[1]}",
            "fps": FPS,
            "tween_frames_per_trading_day": TWEEN_FRAMES,
            "playback_speed_relative_to_previous": 0.75,
            "bars": "all boards with a valid return at each date",
            "visual_reference": "https://mp.weixin.qq.com/s/OlQ6ORGaG-0B-qrNO1XeMQ",
        },
        "rolling_20": {
            "first_window_start": rolling_starts[0],
            "first_window_end": rolling_days[0],
            "last_window_start": rolling_starts[-1],
            "last_window_end": rolling_days[-1],
            "last_reference_close": days[-21],
            "ending_trading_days": len(rolling_days),
            "boards_at_first_end": int(np.isfinite(rolling_arr[:, 0]).sum()),
            "boards_at_last_end": int(np.isfinite(rolling_arr[:, -1]).sum()),
        },
        "videos": [],
    }
    for key, label in WINDOWS:
        window = rolling_days if key == "20d" else values(days, pairs, prices, key)[0]
        video = VIDEOS / f"{label}_累计涨跌幅.mp4"
        manifest["videos"].append(validate_video(video, len(window)))
        print(f"Validated {video.name}", flush=True)
    manifest["html"] = validate_html(days, pairs, prices)
    print("Validated A股板块轮动赛马图.html", flush=True)
    manifest["axis_follow_videos"] = []
    for key, label in WINDOWS:
        window = rolling_days if key == "20d" else values(days, pairs, prices, key)[0]
        video = VIDEOS / f"{label}_累计涨跌幅_动态坐标轴.mp4"
        manifest["axis_follow_videos"].append(validate_video(video, len(window)))
        print(f"Validated {video.name}", flush=True)
    manifest["axis_follow_html"] = validate_html(days, pairs, prices, axis_follow=True)
    print("Validated A股板块轮动赛马图_动态坐标轴.html", flush=True)
    portrait = VIDEOS / "2024年9月24日至今_累计涨跌幅_动态坐标轴_手机竖屏.mp4"
    portrait_days = values(days, pairs, prices, "2024-09-24")[0]
    manifest["portrait_video"] = validate_video(
        portrait, len(portrait_days), size=PORTRAIT_SIZE,
        tween_frames=PORTRAIT_TWEEN_FRAMES,
        intro_frames=FPS * PORTRAIT_INTRO_SECONDS,
        outro_frames=FPS * PORTRAIT_OUTRO_SECONDS,
    )
    manifest["portrait_video"]["axis_follow"] = True
    manifest["portrait_video"]["transition_frames_per_day"] = PORTRAIT_TWEEN_FRAMES
    print(f"Validated {portrait.name}", flush=True)
    portrait_preview = VIDEOS / "预览_2024年9月24日至今_手机竖屏.png"
    run("ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i",
        str(portrait), "-frames:v", "1", str(portrait_preview))
    with portrait_preview.open("rb") as file:
        assert file.read(8) == b"\x89PNG\r\n\x1a\n", portrait_preview
    manifest["portrait_preview"] = portrait_preview.relative_to(ROOT).as_posix()
    preview = VIDEOS / "预览_滚动20日.png"
    run("ffmpeg", "-v", "error", "-y", "-sseof", "-1", "-i",
        str(VIDEOS / "滚动20个交易日_累计涨跌幅.mp4"),
        "-frames:v", "1", str(preview))
    with preview.open("rb") as file:
        assert file.read(8) == b"\x89PNG\r\n\x1a\n", preview
    follow_preview = VIDEOS / "预览_动态坐标轴_滚动20日.png"
    run("ffmpeg", "-v", "error", "-y", "-sseof", "-1", "-i",
        str(VIDEOS / "滚动20个交易日_累计涨跌幅_动态坐标轴.mp4"),
        "-frames:v", "1", str(follow_preview))
    with follow_preview.open("rb") as file:
        assert file.read(8) == b"\x89PNG\r\n\x1a\n", follow_preview
    output = ROOT / "验收结果.json"
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {output}", flush=True)


if __name__ == "__main__":
    main()
