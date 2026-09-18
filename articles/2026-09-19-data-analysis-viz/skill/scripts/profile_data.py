# -*- coding: utf-8 -*-
"""profile_data —— 数据概览与清洗体检。

输入任意表格（CSV / Excel / Parquet），输出：
  - 结构体检：规模、字段类型推断、粒度与唯一键候选
  - 质量体检：缺失、重复、异常、常量列、高基数
  - 字段角色：维度 / 顺序 / 时间 / 度量 / 标识 / 文本
  - 分布特征：偏度、分位数、集中度，并给出图表建议
  - Markdown 报告 + JSON 结果

用法：
    python profile_data.py data.csv
    python profile_data.py data.xlsx --sheet Sheet1 --out profile
    python profile_data.py data.csv --target revenue --group region,channel
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ------------------------------------------------------------- 读取

def load_table(path: Path, sheet: str | int | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls", ".xlsm"}:
        return pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix in {".tsv", ".txt"}:
        return pd.read_csv(path, sep="\t")
    # 自动嗅探分隔符与编码
    for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, sep=None, engine="python")
        except Exception:  # noqa: BLE001
            continue
    return pd.read_csv(path)


# ------------------------------------------------------------- 类型推断

_ID_HINTS = ("id", "编号", "编码", "代码", "code", "uuid", "key", "单号", "订单号")
_FLAG_HINTS = ("是否", "有没有", "flag", "is_", "has_")

#: 形如 2026-09 / 2026/09 / 2026-09-19 / 2026年9月 的字符串按时间处理
_DATE_PATTERN = re.compile(
    r"^\s*\d{4}\s*[-/.年]\s*\d{1,2}\s*([-/.月]\s*\d{1,2}\s*日?)?\s*$"
)


def looks_like_period(vals) -> bool:
    """判断一批字符串是否形如年月 / 年月日。"""
    sample = [str(v) for v in list(vals)[:50]]
    if not sample:
        return False
    hit = sum(1 for v in sample if _DATE_PATTERN.match(v))
    return hit / len(sample) > 0.8


def infer_role(series: pd.Series, name: str, n_rows: int) -> str:
    """推断字段角色：measure / category / ordinal / time / identifier / text。"""
    s = series.dropna()
    if s.empty:
        return "empty"

    nunique = s.nunique()
    lower = str(name).lower()

    if pd.api.types.is_datetime64_any_dtype(series):
        return "time"

    # 非数值、非布尔的列，先试时间解析（pandas 3.x 的 str dtype 也要覆盖）
    is_text_like = not (
        pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series)
    )
    if is_text_like and nunique > 1:
        sample = s.head(200)
        try:
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            parsed_ratio = float(parsed.notna().mean())
        except Exception:  # noqa: BLE001
            parsed_ratio = 0.0
        if parsed_ratio > 0.8 or looks_like_period(sample):
            return "time"

    if pd.api.types.is_bool_dtype(series):
        return "category"

    if pd.api.types.is_numeric_dtype(series):
        is_int = pd.api.types.is_integer_dtype(series)
        ratio = nunique / max(len(s), 1)
        looks_id = any(h in lower for h in _ID_HINTS)
        # 0/1 或 是否类命名 → 当作分类标志，而不是顺序维度
        if (nunique <= 2 and is_int) or any(h in lower for h in _FLAG_HINTS):
            return "category"
        if looks_id and ratio > 0.8:
            return "identifier"
        # 连续整数且取值范围有限 → 顺序维度（如小时 0-23、月份 1-12、评分 1-5）
        if is_int and nunique <= 60 and float(s.max()) - float(s.min()) + 1 == nunique:
            return "ordinal"
        if is_int and nunique <= 12 and ratio < 0.02 and "年" not in str(name):
            return "ordinal"
        return "measure"

    # 字符串 / 高基数文本
    ratio = nunique / max(len(s), 1)
    avg_len = float(s.astype(str).str.len().mean())
    if any(h in lower for h in _ID_HINTS) and nunique > 50:
        return "identifier"
    if ratio > 0.9 and nunique > 50:
        return "text" if avg_len > 18 else "identifier"
    if nunique <= 50:
        return "category"
    return "text"


def numeric_summary(s: pd.Series) -> dict:
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return {}
    q = s.quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    mean, std = float(s.mean()), float(s.std(ddof=1)) if len(s) > 1 else 0.0
    return {
        "count": int(len(s)),
        "min": float(s.min()),
        "q25": float(q.loc[0.25]),
        "median": float(q.loc[0.5]),
        "q75": float(q.loc[0.75]),
        "p90": float(q.loc[0.9]),
        "p95": float(q.loc[0.95]),
        "p99": float(q.loc[0.99]),
        "max": float(s.max()),
        "mean": mean,
        "std": std,
        "cv": float(std / mean) if mean else None,
        "skew": float(s.skew()) if len(s) > 2 else None,
        "kurtosis": float(s.kurtosis()) if len(s) > 3 else None,
        "zeros": int((s == 0).sum()),
    }


def topn_share(s: pd.Series, n: int = 10) -> dict:
    v = pd.to_numeric(s, errors="coerce").dropna()
    v = v[v > 0]
    if len(v) < 5 or v.sum() <= 0:
        return {}
    top = v.sort_values(ascending=False)
    k = max(1, int(round(len(top) * 0.1)))
    return {
        "positive_count": int(len(v)),
        "top10pct_share": float(top.head(k).sum() / v.sum()),
        "top1_share": float(top.iloc[0] / v.sum()),
    }


# ------------------------------------------------------------- 体检

def find_near_duplicate_labels(s: pd.Series) -> list[tuple[str, str]]:
    """找出疑似同义异写的类别标签，如 `信息流` 与 `信息流广告`。"""
    vals = [str(v) for v in s.dropna().unique()]
    out = []
    for i, a in enumerate(vals):
        for b in vals[i + 1:]:
            if a == b:
                continue
            shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
            if len(shorter) >= 2 and shorter in longer:
                out.append((shorter, longer))
    return out


def detect_unit_mixing(s: pd.Series) -> float | None:
    """检测极端极值：最大值 / 中位数 悬殊时提示核对（单位混用或真实长尾）。"""
    v = pd.to_numeric(s, errors="coerce").dropna()
    v = v[v > 0]
    if len(v) < 20:
        return None
    med = float(v.median())
    if med <= 0:
        return None
    ratio = float(v.max()) / med
    return ratio if ratio > 1000 else None


def profile(df: pd.DataFrame, target: str | None, groups: list[str]) -> dict:
    n_rows, n_cols = df.shape
    report: dict = {
        "shape": {"rows": n_rows, "columns": n_cols},
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": [],
        "quality_issues": [],
        "chart_hints": [],
    }

    for col in df.columns:
        s = df[col]
        role = infer_role(s, col, n_rows)
        missing = int(s.isna().sum())
        entry = {
            "name": str(col),
            "dtype": str(s.dtype),
            "role": role,
            "unique": int(s.nunique(dropna=True)),
            "missing": missing,
            "missing_rate": round(missing / n_rows, 4) if n_rows else None,
        }
        if role == "measure":
            entry["numeric"] = numeric_summary(s)
            entry["concentration"] = topn_share(s)
        elif role in {"category", "ordinal"}:
            vc = s.value_counts(dropna=True)
            entry["top_values"] = {
                str(k): int(v) for k, v in vc.head(8).items()
            }
            entry["imbalance"] = (
                round(float(vc.iloc[0] / vc.sum()), 4) if len(vc) else None
            )
        elif role == "time":
            parsed = pd.to_datetime(s, errors="coerce", format="mixed")
            if parsed.notna().any():
                valid = parsed.dropna().sort_values()
                entry["time_range"] = [valid.iloc[0].isoformat(), valid.iloc[-1].isoformat()]
                gaps = valid.diff().dropna()
                if len(gaps):
                    entry["median_interval_seconds"] = float(gaps.dt.total_seconds().median())
        report["columns"].append(entry)

        # ------- 质量问题
        if entry["missing_rate"] and entry["missing_rate"] > 0.3:
            report["quality_issues"].append(
                f"字段 `{col}` 缺失率 {entry['missing_rate']:.1%}，需确认缺失类型（随机/结构性）后再决定插补或剔除"
            )
        if role == "measure" and entry.get("numeric", {}).get("skew") is not None:
            sk = abs(entry["numeric"]["skew"])
            if sk >= 1:
                report["quality_issues"].append(
                    f"字段 `{col}` 偏度 {entry['numeric']['skew']:.2f}（高度偏态），汇报时用中位数与分位数，不要只用均值"
                )
        if role == "measure":
            ratio = detect_unit_mixing(s)
            if ratio:
                report["quality_issues"].append(
                    f"字段 `{col}` 最大值是中位数的 {ratio:.0f} 倍，属于极端极值：先核对是不是**单位混用或输入错误**"
                    f"（如一部分行用元、一部分用万元，或毫秒写成秒），确认无误后再按真实长尾处理"
                )
        if role in {"category", "ordinal"}:
            dup_labels = find_near_duplicate_labels(s)
            for shorter, longer in dup_labels[:3]:
                report["quality_issues"].append(
                    f"字段 `{col}` 疑似同义异写：`{shorter}` 与 `{longer}`，需统一为标准写法后再分组"
                )
        if role == "category" and entry.get("imbalance", 0) and entry["imbalance"] > 0.9:
            report["quality_issues"].append(
                f"字段 `{col}` 高度不平衡（最大类占比 {entry['imbalance']:.1%}），分组分析时注意小类样本量"
            )
        if role == "identifier" and entry["unique"] == n_rows:
            report["quality_issues"].append(
                f"字段 `{col}` 取值唯一，是标识符，不参与统计与图表维度"
            )
        if role == "text" and entry["unique"] > n_rows * 0.5:
            report["quality_issues"].append(
                f"字段 `{col}` 为自由文本且高基数，需先做主题/情感编码再用于可视化"
            )
        if entry["unique"] <= 1 and n_rows > 1:
            report["quality_issues"].append(f"字段 `{col}` 为常量列，可删除")

    # 唯一键候选：单字段标识符，或若干维度字段的组合
    key_candidates = [
        c["name"]
        for c in report["columns"]
        if c["role"] == "identifier" and c["unique"] == n_rows
    ]
    dim_cols = [
        c["name"] for c in report["columns"] if c["role"] in {"category", "ordinal", "time"}
    ]
    composite_keys: list[str] = []
    if not key_candidates and dim_cols and n_rows:
        from itertools import combinations

        for size in (2, 3):
            for combo in combinations(dim_cols, size):
                if df[list(combo)].drop_duplicates().shape[0] == n_rows:
                    composite_keys.append(" + ".join(combo))
            if composite_keys:
                break
    report["unique_key_candidates"] = key_candidates
    report["composite_key_candidates"] = composite_keys[:5]
    if report["duplicate_rows"]:
        report["quality_issues"].insert(
            0,
            f"存在 {report['duplicate_rows']} 行完全重复（占 {report['duplicate_rows']/max(n_rows,1):.2%}），"
            "需先判断是脏数据还是真实重复事件，再决定去重",
        )
    if n_rows and not key_candidates and not composite_keys:
        report["quality_issues"].insert(
            0,
            "未找到唯一键（含字段组合）：可能粒度不纯（同一行代表多种对象），或本来就允许多行代表同一实体",
        )

    # ------- 图表建议
    measures = [c for c in report["columns"] if c["role"] == "measure"]
    categories = [c for c in report["columns"] if c["role"] in {"category", "ordinal"}]
    times = [c for c in report["columns"] if c["role"] == "time"]

    if times and measures:
        t = times[0]
        report["chart_hints"].append(
            f"`{t['name']}` × `{measures[0]['name']}` → 折线图（单系列）或多系列折线（分组）"
        )
    if categories and measures:
        c0, m0 = categories[0]["name"], measures[0]["name"]
        two_dims = len(categories) >= 2
        if not two_dims:
            if categories[0]["unique"] <= 12:
                report["chart_hints"].append(f"`{c0}` × `{m0}` → 柱状图（类别 ≤ 12，标签短）")
            else:
                report["chart_hints"].append(
                    f"`{c0}` 有 {categories[0]['unique']} 个类别 → 排序条形图取 Top-N，或改用热力图"
                )
    if len(measures) >= 2:
        report["chart_hints"].append(
            f"`{measures[0]['name']}` 与 `{measures[1]['name']}` → 散点图 + 回归线（两个连续数值变量）"
        )
    if len(measures) >= 3 and categories:
        report["chart_hints"].append(
            "多维场景 → 气泡图（第三个度量映射到面积，分类映射到颜色），变量不超过 4 个"
        )
    if len(measures) >= 4:
        report["chart_hints"].append("度量 ≥ 4 → 先算相关性热力矩阵，再选代表变量深入")
    if len(categories) >= 2 and measures and not times:
        a, b = categories[0], categories[1]
        if 2 <= a["unique"] <= 40 and 2 <= b["unique"] <= 40:
            report["chart_hints"].append(
                f"`{a['name']}` × `{b['name']}` × `{measures[0]['name']}` → **热力矩阵**"
                "（分类×分类，用颜色深浅表示数值，比分组柱状图更省空间）"
            )
    # 时间 × 分类 × 度量 → 复合目的（趋势 + 构成）
    if times and categories and 2 <= categories[0]["unique"] <= 8 and measures:
        report["chart_hints"].append(
            f"`{times[0]['name']}` × `{categories[0]['name']}` × `{measures[0]['name']}` → "
            "**堆叠面积图 / 100% 堆叠面积图**（同时看总量与构成随时间变化；"
            "若要比较中间层大小，改用多条折线或小倍数分面）"
        )
    if not times and not categories:
        report["chart_hints"].append("只有数值字段 → 直方图 / 箱线图看分布")
    for c in measures:
        n = c.get("numeric", {}).get("skew")
        if n is not None and abs(n) >= 1:
            report["chart_hints"].append(
                f"`{c['name']}` 右偏长尾（偏度 {n:.2f}）→ 箱线图 + 对数轴，或分位数柱状图"
            )
        conc = c.get("concentration") or {}
        if conc.get("top10pct_share", 0) > 0.6:
            report["chart_hints"].append(
                f"`{c['name']}` 前 10% 贡献 {conc['top10pct_share']:.1%} → 排序条形图 + 累计曲线（帕累托图）"
            )

    report["target"] = target
    report["groups"] = groups
    return report


# ------------------------------------------------------------- 输出

def to_markdown(rep: dict) -> str:
    shape = rep["shape"]
    single = rep["unique_key_candidates"]
    combo = rep.get("composite_key_candidates") or []
    key_text = ", ".join(single) or ("；".join(combo) if combo else "未找到")
    lines = [
        "# 数据体检报告",
        "",
        "## 一、基本信息",
        f"- 规模：{shape['rows']} 行 × {shape['columns']} 列",
        f"- 完全重复行：{rep['duplicate_rows']}",
        f"- 唯一键候选：{key_text}",
    ]
    for c in rep["columns"]:
        if c["role"] == "time" and c.get("time_range"):
            lines.append(f"- 时间字段 `{c['name']}`：{c['time_range'][0]} → {c['time_range'][1]}")
    lines += ["", "## 二、字段清单", "",
              "| 字段 | 类型 | 角色 | 唯一值 | 缺失率 | 备注 |",
              "| --- | --- | --- | --- | --- | --- |"]
    role_cn = {
        "measure": "度量", "category": "分类维度", "ordinal": "顺序维度",
        "time": "时间", "identifier": "标识符", "text": "文本", "empty": "空列",
    }
    for c in rep["columns"]:
        note = ""
        if c["role"] == "measure" and c.get("numeric"):
            n = c["numeric"]
            note = (
                f"中位数 {n['median']:.4g}，P95 {n['p95']:.4g}"
                + (f"，偏度 {n['skew']:.2f}" if n.get("skew") is not None else "")
            )
        elif c["role"] in {"category", "ordinal"} and c.get("top_values"):
            top = list(c["top_values"].items())[:3]
            note = "、".join(f"{k}({v})" for k, v in top)
        lines.append(
            f"| `{c['name']}` | {c['dtype']} | {role_cn.get(c['role'], c['role'])} | "
            f"{c['unique']} | {c['missing_rate']:.1%} | {note} |"
        )

    lines += ["", "## 三、质量问题"]
    lines += [f"- {q}" for q in rep["quality_issues"]] or ["- 未发现明显问题"]

    lines += ["", "## 四、图表建议"]
    lines += [f"- {h}" for h in rep["chart_hints"]] or ["- 需补充分析意图后再定图型"]

    lines += [
        "", "## 五、下一步", "",
        "1. 确认口径：每个关键字段写出自包含定义（分子、分母、人群、时间窗、实体、排除项）。",
        "2. 处理异常值：区分输入错误与真实长尾，记录处置规则与影响行数。",
        "3. 提取统计特征：偏态字段用中位数与分位数，分组后重算关键统计量。",
        "4. 选图：按 `references/04-图表匹配.md` 从分析意图推导图型。",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="数据概览与清洗体检")
    ap.add_argument("input", help="CSV / Excel / Parquet 路径")
    ap.add_argument("--sheet", default=None, help="Excel 工作表名或索引")
    ap.add_argument("--out", default="profile", help="输出文件主干名")
    ap.add_argument("--target", default=None, help="主要关注的度量字段")
    ap.add_argument("--group", default="", help="分组维度，逗号分隔")
    args = ap.parse_args(argv)

    path = Path(args.input)
    if not path.exists():
        print(f"[ERROR] 文件不存在：{path}", file=sys.stderr)
        return 2

    df = load_table(path, args.sheet)
    groups = [g for g in args.group.split(",") if g]
    rep = profile(df, args.target, groups)

    md_path = Path(f"{args.out}.md")
    js_path = Path(f"{args.out}.json")
    md_path.write_text(to_markdown(rep), encoding="utf-8")
    js_path.write_text(
        json.dumps(rep, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    print(f"rows={rep['shape']['rows']} cols={rep['shape']['columns']} "
          f"dup={rep['duplicate_rows']} issues={len(rep['quality_issues'])}")
    print(f"wrote {md_path} / {js_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
