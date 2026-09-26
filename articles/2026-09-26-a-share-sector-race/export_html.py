"""Export a self-contained interactive HTML from the verified Eastmoney closes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from palette import BOARD_COLORS
from render_videos import ROOT, load, rolling_returns, values


SOURCE = ROOT / "html_src"
TARGET = ROOT / "A股板块轮动赛马图.html"


def serialise(arr: np.ndarray) -> list[list[float | None]]:
    return [
        [round(float(value), 4) if np.isfinite(value) else None for value in row]
        for row in arr
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--axis-follow", action="store_true",
                        help="Write a separate HTML whose line axes expand with observed history")
    args = parser.parse_args()
    days, pairs, prices = load()
    modes = []
    for key, label in (
        ("2026-01-01", "2026 年初至今"),
        ("2024-09-24", "2024 年 9 月 24 日至今"),
        ("20d", "滚动 20 个交易日"),
    ):
        if key == "20d":
            dates, starts, arr = rolling_returns(days, pairs, prices)
        else:
            dates, arr, _ = values(days, pairs, prices, key)
            starts = None
        modes.append({
            "id": key,
            "label": label,
            "dates": dates,
            "windowStarts": starts,
            "series": serialise(arr),
        })
    data = {
        "asOf": days[-1],
        "axisFollow": args.axis_follow,
        "boards": [{"code": code, "name": name} for code, name in pairs],
        "colors": BOARD_COLORS,
        "modes": modes,
        "source": "东方财富主题板块日 K 线（fqt=0）",
    }
    payload = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace("&", "\\u0026")
    template = (SOURCE / "template.html").read_text(encoding="utf-8")
    if args.axis_follow:
        template = (template.replace("<title>A股主题板块轮动赛马图</title>",
                                     "<title>A股主题板块轮动赛马图 · 动态坐标轴</title>")
                    .replace("曲线随日期推进", "坐标轴随曲线伸展"))
    css = (SOURCE / "style.css").read_text(encoding="utf-8")
    javascript = (SOURCE / "app.js").read_text(encoding="utf-8")
    html = (template.replace("/*__INLINE_CSS__*/", css)
            .replace("__EMBEDDED_DATA__", payload)
            .replace("/*__INLINE_JS__*/", javascript))
    if any(marker in html for marker in ("/*__INLINE_CSS__*/", "__EMBEDDED_DATA__", "/*__INLINE_JS__*/")):
        raise ValueError("Unreplaced HTML template marker")
    target = ROOT / "A股板块轮动赛马图_动态坐标轴.html" if args.axis_follow else TARGET
    target.write_text(html, encoding="utf-8")
    print(f"Saved {target} ({target.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
