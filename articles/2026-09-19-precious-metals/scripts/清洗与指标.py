# -*- coding: utf-8 -*-
"""清洗贵金属价格数据并计算统计指标。

产出：
- data/clean/*.csv        可直接用于制图的整洁数据
- 输出/统计指标.json       区间涨跌幅、金银比、品牌溢价、回撤等
- 输出/数据体检.txt        缺失、重复、异常值等质量报告
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "输出"
CLEAN.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

CST = timezone(timedelta(hours=8))
TODAY = pd.Timestamp("2026-09-19")
TEN_YEARS_AGO = TODAY - pd.DateOffset(years=10)
TWO_YEARS_AGO = TODAY - pd.DateOffset(years=2)

health: list[str] = []


def note(message: str) -> None:
    print(message, flush=True)
    health.append(message)


def load_jsonl_series(filename: str, date_key: str, value_key: str, columns: dict[str, str]) -> pd.DataFrame:
    rows = json.loads((RAW / filename).read_text(encoding="utf-8"))
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame[date_key])
    frame = frame.rename(columns=columns)
    keep = ["date"] + list(columns.values())
    keep = list(dict.fromkeys(keep))
    frame = frame[keep].sort_values("date").drop_duplicates("date")
    for column in frame.columns:
        if column != "date":
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def load_sge(filename: str, label: str) -> pd.DataFrame:
    payload = json.loads((RAW / filename).read_text(encoding="utf-8"))
    rows = payload["time"]
    frame = pd.DataFrame(rows, columns=["date", "开盘", "收盘", "最低", "最高"])
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    # 官方字段顺序为 开盘/收盘/最低/最高，校验价格关系
    bad = frame[(frame["收盘"] > frame["最高"]) | (frame["收盘"] < frame["最低"])]
    if len(bad):
        note(f"[异常] {label} 存在 {len(bad)} 行收盘价越界，已剔除")
        frame = frame.drop(bad.index)
    note(f"{label}: {len(frame)} 个交易日，{frame['date'].min():%Y-%m-%d} ~ {frame['date'].max():%Y-%m-%d}")
    return frame.reset_index(drop=True)


def load_brand_history() -> pd.DataFrame:
    payload = json.loads((RAW / "品牌金价历史_近两年.json").read_text(encoding="utf-8"))
    records: list[dict] = []
    for brand, products in payload.items():
        for product, series in products.items():
            for item in series:
                records.append({
                    "品牌": brand,
                    "品种": product,
                    "日期": datetime.fromtimestamp(item["time"] / 1000, CST).date(),
                    "价格": float(item["q1"]),
                })
    frame = pd.DataFrame(records)
    frame["日期"] = pd.to_datetime(frame["日期"])
    before = len(frame)
    frame = frame.drop_duplicates(["品牌", "品种", "日期"])
    if before != len(frame):
        note(f"[去重] 品牌金价重复记录 {before - len(frame)} 条")
    # 同一日期同一品牌同一品种可能存在多次调价，保留当日最后一次
    frame = frame.sort_values(["品牌", "品种", "日期"]).groupby(
        ["品牌", "品种", "日期"], as_index=False).last()

    # 离群值：单日跳变超过 100 元/克、且前后两天彼此接近（差值<=60）时，
    # 判定为采集错误，用前后两天均值替换（以 2026-08-07 老凤祥 1123 元/克为例）
    fixed = 0
    for (_brand, _product), group in frame.groupby(["品牌", "品种"]):
        group = group.sort_values("日期")
        values = group["价格"].to_numpy(dtype=float).copy()
        for index in range(1, len(values) - 1):
            prev_value, point, next_value = values[index - 1], values[index], values[index + 1]
            neighbour_mean = (prev_value + next_value) / 2
            if abs(point - neighbour_mean) > 100 and abs(prev_value - next_value) <= 60:
                values[index] = neighbour_mean
                fixed += 1
                note(f"[修正] {_brand}/{_product} {_group_date(group, index)} "
                     f"{point:.0f} -> {neighbour_mean:.0f} 元/克（前后均值）")
        group["价格"] = values
        frame.loc[group.index, "价格"] = values
    if not fixed:
        note("[修正] 未发现需替换的离群值")
    return frame


def _group_date(group: pd.DataFrame, index: int) -> str:
    return group["日期"].iloc[index].strftime("%Y-%m-%d")


def window_stats(series: pd.Series, high_series: pd.Series) -> dict:
    return {
        "最新": round(float(series.iloc[-1]), 2),
        "最新日期": series.index[-1].strftime("%Y-%m-%d"),
        "区间最高": round(float(high_series.max()), 2),
        "最高日期": high_series.idxmax().strftime("%Y-%m-%d"),
    }


def main() -> None:
    note("=" * 62)
    note("贵金属价格数据体检")
    note("=" * 62)

    # ---------- 1. 国际现货金银 ----------
    columns = {"open": "开盘", "high": "最高", "low": "最低", "close": "收盘"}
    xau = load_jsonl_series("国际现货黄金_XAU_日线.json", "date", "close", columns)
    xag = load_jsonl_series("国际现货白银_XAG_日线.json", "date", "close", columns)
    note(f"伦敦金现 XAU: {len(xau)} 条，{xau['date'].min():%Y-%m-%d} ~ {xau['date'].max():%Y-%m-%d}，单位 美元/盎司")
    note(f"伦敦银现 XAG: {len(xag)} 条，{xag['date'].min():%Y-%m-%d} ~ {xag['date'].max():%Y-%m-%d}，单位 美元/盎司")

    # ---------- 2. 国内期货与上金所 ----------
    inner_columns = {"o": "开盘", "h": "最高", "l": "最低", "c": "收盘"}
    au0 = load_jsonl_series("沪金主连_AU0_日线.json", "d", "c", inner_columns)
    ag0 = load_jsonl_series("沪银主连_AG0_日线.json", "d", "c", inner_columns)
    note(f"沪金主连 AU0: {len(au0)} 条，单位 元/克")
    note(f"沪银主连 AG0: {len(ag0)} 条，单位 元/千克")
    sge_au = load_sge("上金所_Au9999_日行情.json", "上金所 Au99.99")
    sge_ag = load_sge("上金所_Ag9999_日行情.json", "上金所 Ag99.99")

    # ---------- 3. 品牌金价 ----------
    brands = load_brand_history()
    note(f"品牌金价: {len(brands)} 条，品牌 {brands['品牌'].nunique()} 个，"
         f"{brands['日期'].min():%Y-%m-%d} ~ {brands['日期'].max():%Y-%m-%d}")

    # ---------- 4. 缺失与连续性检查 ----------
    for label, frame, column in (("伦敦金现", xau, "收盘"), ("上金所Au99.99", sge_au, "收盘")):
        span = frame[frame["date"] >= TEN_YEARS_AGO]
        business_days = len(pd.bdate_range(span["date"].min(), span["date"].max()))
        note(f"[完整性] {label} 近十年 {len(span)} 个交易日 / {business_days} 个工作日"
             f"（覆盖率 {len(span) / business_days:.1%}，差额为休市）")
    for brand in sorted(brands["品牌"].unique()):
        sub = brands[(brands["品牌"] == brand) & (brands["品种"] == "黄金价格")
                     & (brands["日期"] >= TWO_YEARS_AGO)]
        span_days = (sub["日期"].max() - sub["日期"].min()).days + 1
        note(f"[完整性] {brand} 近两年黄金价格 {len(sub)} 条 / {span_days} 天"
             f"（覆盖率 {len(sub) / span_days:.1%}）")

    # ---------- 5. 指标计算 ----------
    metrics: dict = {"生成时间": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"), "数据截止": "2026-09-18"}

    def period_return(frame: pd.DataFrame, start: pd.Timestamp) -> float | None:
        sub = frame[frame["date"] >= start]
        if len(sub) < 2:
            return None
        return round(float(sub["收盘"].iloc[-1] / sub["收盘"].iloc[0] - 1) * 100, 2)

    for label, frame in (("伦敦金现", xau), ("伦敦银现", xag),
                         ("上金所Au99.99", sge_au), ("沪金主连", au0)):
        metrics.setdefault("区间涨跌幅%", {})[label] = {
            "近10年": period_return(frame, TEN_YEARS_AGO),
            "近2年": period_return(frame, TWO_YEARS_AGO),
            "近1年": period_return(frame, TODAY - pd.DateOffset(years=1)),
            "今年以来": period_return(frame, pd.Timestamp("2026-01-01")),
        }
    metrics["区间涨跌幅%"]["上海银Ag99.99"] = {
        "近10年": period_return(sge_ag, TEN_YEARS_AGO),
        "近2年": period_return(sge_ag, TWO_YEARS_AGO),
        "近1年": period_return(sge_ag, TODAY - pd.DateOffset(years=1)),
        "今年以来": period_return(sge_ag, pd.Timestamp("2026-01-01")),
    }

    # 年度涨跌幅
    yearly: dict[str, dict] = {}
    for label, frame in (("伦敦金现", xau), ("伦敦银现", xag), ("上金所Au99.99", sge_au)):
        series = frame.set_index("date")["收盘"]
        rows = {}
        for year, group in series.groupby(series.index.year):
            if year < 2016 or len(group) < 5:
                continue
            rows[str(year)] = round(float(group.iloc[-1] / group.iloc[0] - 1) * 100, 2)
        yearly[label] = rows
    metrics["年度涨跌幅%"] = yearly

    # 金银比
    ratio = (xau.set_index("date")["收盘"] / xag.set_index("date")["收盘"]).dropna()
    ratio_10y = ratio[ratio.index >= TEN_YEARS_AGO]
    metrics["金银比"] = {
        "最新": round(float(ratio_10y.iloc[-1]), 2),
        "近10年最高": round(float(ratio_10y.max()), 2),
        "最高日期": ratio_10y.idxmax().strftime("%Y-%m-%d"),
        "近10年最低": round(float(ratio_10y.min()), 2),
        "最低日期": ratio_10y.idxmin().strftime("%Y-%m-%d"),
        "近10年均值": round(float(ratio_10y.mean()), 2),
        "近2年均值": round(float(ratio_10y[ratio_10y.index >= TWO_YEARS_AGO].mean()), 2),
    }

    # 2026 年内高低点与回撤
    for label, frame in (("伦敦金现", xau), ("伦敦银现", xag), ("上金所Au99.99", sge_au)):
        sub = frame[frame["date"] >= "2026-01-01"].set_index("date")
        peak, peak_date = float(sub["收盘"].max()), sub["收盘"].idxmax()
        latest = float(sub["收盘"].iloc[-1])
        row = {
            "年内最高": round(peak, 2),
            "最高日期": peak_date.strftime("%Y-%m-%d"),
            "最新": round(latest, 2),
            "较最高回撤%": round((latest / peak - 1) * 100, 2),
            "年初": round(float(sub["收盘"].iloc[0]), 2),
        }
        metrics.setdefault("2026年内", {})[label] = row

    # 品牌溢价：品牌零售价 - 上金所 Au99.99
    base = sge_au.set_index("date")["收盘"]
    premium_records = []
    brand_2y = brands[(brands["日期"] >= TWO_YEARS_AGO) & (brands["品种"] == "黄金价格")]
    for brand in sorted(brand_2y["品牌"].unique()):
        sub = brand_2y[brand_2y["品牌"] == brand].set_index("日期")["价格"].sort_index()
        aligned = pd.concat([sub.rename("品牌价"), base.rename("上金所")], axis=1).dropna()
        if aligned.empty:
            continue
        aligned["溢价"] = aligned["品牌价"] - aligned["上金所"]
        aligned["溢价率%"] = aligned["溢价"] / aligned["上金所"] * 100
        premium_records.append({
            "品牌": brand,
            "样本数": int(len(aligned)),
            "最新品牌价": round(float(aligned["品牌价"].iloc[-1]), 2),
            "最新溢价": round(float(aligned["溢价"].iloc[-1]), 2),
            "最新溢价率%": round(float(aligned["溢价率%"].iloc[-1]), 2),
            "近两年溢价均值": round(float(aligned["溢价"].mean()), 2),
            "近两年溢价率均值%": round(float(aligned["溢价率%"].mean()), 2),
            "近两年溢价最低": round(float(aligned["溢价"].min()), 2),
            "近两年溢价最高": round(float(aligned["溢价"].max()), 2),
        })
        aligned.to_csv(CLEAN / f"品牌溢价_{brand}.csv", encoding="utf-8-sig")
    metrics["品牌溢价(品牌零售价-上金所Au99.99, 元/克)"] = premium_records

    # 品牌最近两年涨幅
    brand_return = []
    for brand in sorted(brand_2y["品牌"].unique()):
        sub = brand_2y[brand_2y["品牌"] == brand].sort_values("日期")
        first, last = sub.iloc[0], sub.iloc[-1]
        brand_return.append({
            "品牌": brand,
            "起点日期": first["日期"].strftime("%Y-%m-%d"),
            "起点价": float(first["价格"]),
            "最新日期": last["日期"].strftime("%Y-%m-%d"),
            "最新价": float(last["价格"]),
            "两年涨幅%": round(float(last["价格"] / first["价格"] - 1) * 100, 2),
            "两年最高": float(sub["价格"].max()),
            "最高日期": sub.loc[sub["价格"].idxmax(), "日期"].strftime("%Y-%m-%d"),
        })
    metrics["品牌金价近两年"] = brand_return

    # 50 克三金成本对比
    if brand_return:
        row = next((r for r in brand_return if r["品牌"] == "周大福"), brand_return[0])
        metrics["50克饰品成本示例(周大福)"] = {
            "两年起点": round(row["起点价"] * 50, 0),
            "两年最高点": round(row["两年最高"] * 50, 0),
            "最新": round(row["最新价"] * 50, 0),
            "较最高点省下": round((row["两年最高"] - row["最新价"]) * 50, 0),
        }

    # ---------- 6. 导出整洁数据 ----------
    xau[xau["date"] >= TEN_YEARS_AGO].to_csv(CLEAN / "01_伦敦金现_近十年.csv",
                                             index=False, encoding="utf-8-sig")
    xag[xag["date"] >= TEN_YEARS_AGO].to_csv(CLEAN / "02_伦敦银现_近十年.csv",
                                             index=False, encoding="utf-8-sig")
    sge_au[sge_au["date"] >= TEN_YEARS_AGO].to_csv(CLEAN / "03_上金所Au9999_近十年.csv",
                                                   index=False, encoding="utf-8-sig")
    sge_ag[sge_ag["date"] >= TEN_YEARS_AGO].to_csv(CLEAN / "04_上金所Ag9999_近十年.csv",
                                                   index=False, encoding="utf-8-sig")
    au0[au0["date"] >= TEN_YEARS_AGO].to_csv(CLEAN / "05_沪金主连_近十年.csv",
                                             index=False, encoding="utf-8-sig")
    brand_2y.to_csv(CLEAN / "06_品牌金价_近两年.csv", index=False, encoding="utf-8-sig")
    ratio_frame = ratio_10y.rename("金银比").reset_index()
    ratio_frame.columns = ["date", "金银比"]
    ratio_frame.to_csv(CLEAN / "07_金银比_近十年.csv", index=False, encoding="utf-8-sig")

    (OUT / "统计指标.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    (OUT / "数据体检.txt").write_text("\n".join(health), encoding="utf-8")
    note("整洁数据与指标已输出")


if __name__ == "__main__":
    main()
