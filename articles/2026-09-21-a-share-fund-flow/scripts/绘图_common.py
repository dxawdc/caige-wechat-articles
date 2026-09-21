# -*- coding: utf-8 -*-
"""v1.0.0 | 2026-09-21 | 绘图脚本公共配置。

解决的问题：原先各绘图脚本把交易日（"2026-09-18"）和一堆统计数字硬编码在标题里，
换一天数据就必须手改多处、极易漏改。这里统一：
- TRADE_DATE：从 `数据采集/资金流向_全市场.json` 的 meta.fetched_at 自动识别，
  也可被环境变量 TRADE_DATE 覆盖；
- 绝对路径：脚本从任意 CWD 运行都能找到数据与输出目录；
- 通用工具：yi() 元转亿、load_market()/load_ext() 清洗加载。

各绘图脚本 `import _common as C` 后使用 C.DATE / C.yi / C.load_market()。
"""
from __future__ import annotations
import json
import os
import re

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)                    # .../A股资金流向_公众号图文
DATA_DIR = os.path.join(ROOT, "数据采集")
OUT_DIR = _HERE


def _detect_date() -> str:
    env = os.environ.get("TRADE_DATE", "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", env):
        return env
    p = os.path.join(DATA_DIR, "资金流向_全市场.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                meta = json.load(f).get("meta", {})
            # 优先用采集时写入的交易日；付稿时点（fetched_at）只作兜底
            for key in ("trade_date", "fetched_at"):
                m = re.match(r"(\d{4}-\d{2}-\d{2})", str(meta.get(key, "")))
                if m:
                    return m.group(1)
        except Exception:  # noqa: BLE001
            pass
    return ""


DATE = _detect_date()
MARKET_CSV = os.path.join(DATA_DIR, "资金流向_全市场.csv")
EXT_CSV = os.path.join(DATA_DIR, "资金流向_全市场_扩展.csv")
INDUSTRY_CSV = os.path.join(DATA_DIR, "资金流向_行业_全量.csv")
INTRADAY_JSON = os.path.join(DATA_DIR, "分时资金流_候选股.json")

# 配色：方向用 A 股习惯（红涨绿跌）
RED, GREEN = "#D93025", "#0E8F63"
INK, MUTED = "#2B2B2B", "#8A8A8A"

NUM_COLS = ["price", "pct", "main_net", "main_pct", "xl_net", "l_net", "m_net", "s_net"]


def yi(v) -> float:
    """元 -> 亿元。"""
    return float(v) / 1e8


def add_fonts(matplotlib):
    """注册中文字体，避免每脚本重复样板。"""
    from matplotlib import font_manager
    for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc",
               "C:/Windows/Fonts/consola.ttf"]:
        try:
            font_manager.fontManager.addfont(fp)
        except Exception:  # noqa: BLE001
            pass
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
    matplotlib.rcParams["axes.unicode_minus"] = False


def load_market(path: str | None = None) -> pd.DataFrame:
    """加载全市场资金流，剔除停牌/退市（净额为 '-'）的样本。"""
    df = pd.read_csv(path or MARKET_CSV, dtype=str)
    for c in NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].replace("-", None), errors="coerce")
    df = df.dropna(subset=["main_net"]).copy()
    df["name"] = df["name"].astype(str).str.replace(" ", "", regex=False)
    for c in ["xl_net", "l_net", "m_net", "s_net"]:
        df[c] = df[c].fillna(0.0)
    return df


def load_ext(path: str | None = None) -> pd.DataFrame:
    """加载扩展字段（含总市值/成交额/换手率）。"""
    df = pd.read_csv(path or EXT_CSV, dtype=str)
    for c in ["pct", "main_net", "xl_net", "s_net", "amount", "turnover",
              "mktcap", "float_cap"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].replace("-", None), errors="coerce")
    return df.dropna(subset=["main_net", "mktcap"]).copy()


def load_intraday(path: str | None = None) -> dict:
    with open(path or INTRADAY_JSON, encoding="utf-8") as f:
        return json.load(f)
