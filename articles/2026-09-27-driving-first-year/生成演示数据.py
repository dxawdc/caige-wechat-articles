"""生成可复现的虚构驾车卡片，供 Plotly 绘图练习。"""

from __future__ import annotations

import calendar
import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "数据" / "演示行程.csv"
FIELDS = [
    "date", "time", "origin", "destination", "distance_km_display",
    "distance_km_est", "duration", "average_speed_kmh", "max_speed_kmh",
    "travel_mode", "data_kind",
]


def main() -> None:
    rng = random.Random(20260927)
    routes = [
        ("示例点 A", "示例点 B"),
        ("示例点 B", "示例点 A"),
        ("示例点 A", "示例点 C"),
        ("示例点 C", "示例点 D"),
        ("示例点 D", "示例点 A"),
    ]
    rows = []
    for year, month in [(2025, m) for m in range(10, 13)] + [
        (2026, m) for m in range(1, 10)
    ]:
        last_day = min(calendar.monthrange(year, month)[1], 26 if month == 9 else 31)
        for _ in range(15):
            day = rng.randint(1, last_day)
            hour = rng.choice([8, 9, 10, 11, 17, 18, 19, 20])
            minute = rng.choice([0, 10, 20, 30, 40, 50])
            origin, destination = rng.choices(routes, weights=[5, 5, 2, 1, 1])[0]
            km = round(rng.uniform(0.5, 14.0), 1)
            average_speed = rng.randint(12, 31)
            seconds = round(km / average_speed * 3600)
            rows.append({
                "date": f"{year:04d}.{month:02d}.{day:02d}",
                "time": f"{hour:02d}:{minute:02d}",
                "origin": origin,
                "destination": destination,
                "distance_km_display": "<1" if km < 1 else f"{km:.1f}",
                "distance_km_est": 0.5 if km < 1 else km,
                "duration": f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}",
                "average_speed_kmh": average_speed,
                "max_speed_kmh": average_speed + rng.randint(8, 27),
                "travel_mode": "driving",
                "data_kind": "synthetic_demo",
            })
    rows.sort(key=lambda row: (row["date"], row["time"]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"已生成 {len(rows)} 条虚构行程：{OUTPUT}")


if __name__ == "__main__":
    main()
