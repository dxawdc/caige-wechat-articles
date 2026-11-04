# -*- coding: utf-8 -*-
"""把识图草稿的墙体和作者给的标准答案逐点对账，输出偏差分位。

用法：
  python 对比墙体偏差.py draft.json example-spec.json

思路：沿草稿每面墙取 21 个点，算每个点到「最近的一条标准墙中线」的距离，
再统计中位数、P90、P99 与超差比例。门窗洞会让墙断开，所以只比距离，不比墙数。
"""
from __future__ import annotations

import json
import math
import statistics
import sys


def sample(a, b, n=20):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def point_to_segment(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def main():
    draft_path, ref_path = sys.argv[1], sys.argv[2]
    draft = json.load(open(draft_path, encoding="utf-8"))
    ref = json.load(open(ref_path, encoding="utf-8"))
    ref_segments = [(w["a"], w["b"]) for w in ref["walls"]]

    dists, per_wall = [], []
    for wall in draft["walls"]:
        ds = [min(point_to_segment(p, a, b) for a, b in ref_segments)
              for p in sample(wall["a"], wall["b"])]
        per_wall.append({
            "id": wall.get("id"),
            "max_mm": round(max(ds), 1),
            "mean_mm": round(statistics.mean(ds), 1),
        })
        dists.extend(ds)

    dists.sort()

    def pct(q):
        return dists[min(len(dists) - 1, int(len(dists) * q))]

    summary = {
        "draft_walls": len(draft["walls"]),
        "ref_walls": len(ref["walls"]),
        "samples": len(dists),
        "median_mm": round(pct(0.5), 1),
        "p90_mm": round(pct(0.9), 1),
        "p99_mm": round(pct(0.99), 1),
        "max_mm": round(max(dists), 1),
        "share_within_10mm": round(100 * sum(1 for d in dists if d <= 10) / len(dists), 1),
        "share_within_30mm": round(100 * sum(1 for d in dists if d <= 30) / len(dists), 1),
        "per_wall": per_wall,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
