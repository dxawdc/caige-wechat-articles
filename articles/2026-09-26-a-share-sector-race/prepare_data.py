"""Collect and validate the exact 30 Eastmoney board daily closes."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
THEMES_JS = ROOT.parent / "环球行情板块小程序" / "data" / "themes.js"
DATA = ROOT / "data"
THEMES_CSV = DATA / "板块清单.csv"
CALENDAR_SOURCE = DATA / "交易日历.csv"
OUT = DATA / "行情.csv"
API = "https://91.push2his.eastmoney.com/api/qt/stock/kline/get"
FIRST = "2024-09-23"  # reference close for the September 24 window
AS_OF = "2026-09-24"  # latest verified close when this project was created


def themes() -> list[tuple[str, str]]:
    with THEMES_CSV.open(encoding="utf-8-sig", newline="") as file:
        pairs = [(row["东方财富代码"], row["板块名称"]) for row in csv.DictReader(file)]
    if len(pairs) != 30 or len({code for code, _ in pairs}) != 30:
        raise ValueError("Expected exactly 30 distinct Eastmoney board codes in 板块清单.csv")
    if THEMES_JS.exists():
        source = THEMES_JS.read_text(encoding="utf-8")
        rows = re.findall(r"\{ id: '[^']+', name: '([^']+)',.*?a: '90\.(BK\d+)'", source)
        if pairs != [(code, name) for name, code in rows]:
            raise ValueError("Local board list differs from the mini-program themes.js")
    return pairs


def calendar() -> list[str]:
    if not CALENDAR_SOURCE.exists():
        raise FileNotFoundError(f"Comparison calendar unavailable: {CALENDAR_SOURCE}")
    with CALENDAR_SOURCE.open(encoding="utf-8-sig", newline="") as file:
        days = sorted({r["date"] for r in csv.DictReader(file) if FIRST <= r["date"] <= AS_OF})
    if not days or days[0] != FIRST or days[-1] != AS_OF:
        raise ValueError(f"Calendar does not span {FIRST} through {AS_OF}")
    return days


def fetch(code: str) -> list[dict]:
    query = urllib.parse.urlencode({
        "secid": f"90.{code}", "klt": "101", "fqt": "0",
        "beg": FIRST.replace("-", ""), "end": AS_OF.replace("-", ""), "lmt": "2000",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    })
    request = urllib.request.Request(API + "?" + query, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=18) as response:
                body = json.load(response)
            payload = body.get("data") or {}
            if body.get("rc") != 0 or payload.get("code") != code or not payload.get("klines"):
                raise ValueError(f"Invalid or empty Eastmoney response: {code}")
            result = []
            for line in payload["klines"]:
                fields = line.split(",")
                result.append({"date": fields[0], "code": code, "close": fields[2]})
            return result
        except Exception as exc:
            error = exc
            time.sleep(attempt + 1)
    raise RuntimeError(f"Failed to fetch {code}: {error}")


def import_csvs(folder: Path) -> list[dict]:
    files = sorted(folder.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {folder}")
    aliases = {
        "date": ("date", "日期", "交易日期", "trade_date"),
        "code": ("code", "板块代码", "代码", "secid"),
        "close": ("close", "收盘", "收盘价", "收盘点位"),
    }
    result = []
    for path in files:
        text = None
        for encoding in ("utf-8-sig", "gb18030"):
            try:
                text = path.read_text(encoding=encoding)
                break
            except UnicodeError:
                pass
        if text is None:
            raise ValueError(f"Cannot decode {path}")
        rows = csv.DictReader(text.splitlines())
        headers = rows.fieldnames or []
        columns = {key: next((name for name in names if name in headers), None) for key, names in aliases.items()}
        if not columns["date"] or not columns["close"]:
            raise ValueError(f"Missing date/close columns in {path.name}: {headers}")
        fallback_code = re.search(r"BK\d+", path.name, re.IGNORECASE)
        for row in rows:
            code = row[columns["code"]] if columns["code"] else (fallback_code.group().upper() if fallback_code else "")
            raw_day = row[columns["date"]].strip().replace("/", "-")[:10]
            day = f"{raw_day[:4]}-{raw_day[4:6]}-{raw_day[6:8]}" if re.fullmatch(r"\d{8}", raw_day) else raw_day
            result.append({"date": day,
                           "code": code.replace("90.", "").upper().strip(),
                           "close": row[columns["close"]].replace(",", "").strip()})
    return result


def validate(rows: list[dict], names: dict[str, str], days: list[str]) -> list[dict]:
    seen: dict[tuple[str, str], float] = {}
    expected = set(days)
    for row in rows:
        code, day = row["code"], row["date"]
        if code not in names or day not in expected:
            raise ValueError(f"Unexpected board/date: {code} {day}")
        try:
            close = float(row["close"])
        except ValueError as exc:
            raise ValueError(f"Invalid close: {code} {day}") from exc
        if not math.isfinite(close) or close <= 0:
            raise ValueError(f"Invalid close: {code} {day} {close}")
        key = (day, code)
        if key in seen and seen[key] != close:
            raise ValueError(f"Conflicting duplicate: {code} {day}")
        seen[key] = close
    errors = []
    for code in names:
        present = [day for day in days if (day, code) in seen]
        if not present:
            errors.append(f"{code}: no data")
            continue
        if present[-1] != AS_OF:
            errors.append(f"{code}: ends at {present[-1]}, expected {AS_OF}")
        interior = [day for day in days if present[0] <= day <= present[-1] and (day, code) not in seen]
        if interior:
            errors.append(f"{code}: {len(interior)} missing trading days, first {interior[:4]}")
    if errors:
        raise ValueError("Incomplete daily history:\n" + "\n".join(errors))
    return [{"date": day, "code": code, "name": names[code], "close": f"{seen[(day, code)]:.6f}"}
            for day in days for code in names if (day, code) in seen]


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fetch", action="store_true", help="Get complete history from the production Eastmoney API")
    source.add_argument("--import-dir", type=Path, help="Import exported Eastmoney CSV files")
    args = parser.parse_args()
    pairs = themes()
    names = dict(pairs)
    days = calendar()
    rows = []
    if args.fetch:
        for code, name in pairs:
            print(f"Fetching {name} {code}", flush=True)
            rows.extend(fetch(code))
            time.sleep(0.5)
    else:
        rows = import_csvs(args.import_dir)
    valid = validate(rows, names, days)
    DATA.mkdir(exist_ok=True)
    temp = OUT.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=("date", "code", "name", "close"))
        writer.writeheader()
        writer.writerows(valid)
    temp.replace(OUT)
    (DATA / "行情元数据.json").write_text(json.dumps({
        "source": API if args.fetch else str(args.import_dir.resolve()),
        "source_type": "Eastmoney direct daily K-line" if args.fetch else "Eastmoney exported daily CSV",
        "adjustment": "unadjusted (fqt=0)" if args.fetch else "per exported file",
        "calendar_source": str(CALENDAR_SOURCE),
        "first_reference_date": FIRST,
        "last_verified_date": AS_OF,
        "trading_days": len(days),
        "boards": len(pairs),
        "rows": len(valid),
        "captured_at": date.today().isoformat(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Verified {len(pairs)} boards, {len(days)} trading days; wrote {len(valid)} rows to {OUT}")


if __name__ == "__main__":
    main()
