# -*- coding: utf-8 -*-
"""从 film 渲染成片生成公众号演示 GIF。

用法：python 生成演示GIF.py <成片.mp4> <输出.gif> [--start 2] [--dur 4] [--width 480] [--fps 15]
依赖：ffmpeg 在 PATH。两段式 palettegen/paletteuse 保证色彩质量。
体积偏大时降 width / fps / 用 --small 走 360px + 12fps + 128 色压缩参数。
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def build_filter(width: int, fps: int, small: bool) -> str:
    scale = f"scale={width}:-1:flags=lanczos"
    if small:
        palette = "palettegen=max_colors=128"
        use = "paletteuse=dither=bayer"
    else:
        palette, use = "palettegen", "paletteuse"
    return f"fps={fps},{scale},split[s0][s1];[s0]{palette}[p];[s1][p]{use}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("output")
    ap.add_argument("--start", type=float, default=2.0, help="起始秒，默认 2（避开第 0 帧全黑）")
    ap.add_argument("--dur", type=float, default=4.0)
    ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--fps", type=int, default=15)
    ap.add_argument("--small", action="store_true", help="压缩模式：12fps + 128 色 bayer 抖动")
    args = ap.parse_args()

    cmd = ["ffmpeg", "-y", "-ss", str(args.start), "-t", str(args.dur), "-i", args.video,
           "-vf", build_filter(args.width, args.fps, args.small), "-loop", "0", args.output]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-2000:], file=sys.stderr)
        sys.exit(result.returncode)
    print("完成:", args.output)


if __name__ == "__main__":
    main()
