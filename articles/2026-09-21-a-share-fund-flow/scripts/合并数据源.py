# -*- coding: utf-8 -*-
"""v1.0.0 | 2026-09-21 | 合并多数据源，生成全市场标准表（供绘图脚本直接使用）。

背景：2026-09-21 东方财富 clist 接口遭 IP 级限流，全市场数据改用两个宽容数据源拼装：
  1. datacenter-web 的 RPT_DMSK_TS_STOCKNEW：超大单/大单流入流出、主力净额、涨跌幅、换手率
  2. 腾讯行情 qt.gtimg.cn：成交额、总市值、流通市值
两者均可用且互为独立风控，覆盖面一致（5198 只）。

口径说明（重要）：
  - 主力净额 = 超大单净额 + 大单净额（与东财 PRIME_INFLOW 完全一致，已验证）
  - 四档净额恒有 超大 + 大 + 中 + 小 = 0，因此「中单+小单」= -主力净额，
    这是**精确推导值而非近似**。本案以 m_net 列承载「中小单合计」，
    s_net 留空——旧表把中单、小单分成两列，本次受数据源限制合并为一档。

输出：资金流向_全市场.csv / 资金流向_全市场_扩展.csv / 资金流向_全市场.json
"""
from __future__ import annotations
import csv, json
from datetime import datetime

import pandas as pd

DC_CSV = "数据中心_当日个股.csv"
TX_CSV = "市值成交额_腾讯.csv"
OUT_CSV = "资金流向_全市场.csv"
OUT_EXT = "资金流向_全市场_扩展.csv"
OUT_JSON = "资金流向_全市场.json"
YI = 1e8


def _num(s):
    return pd.to_numeric(s, errors="coerce")


def main():
    dc = pd.read_csv(DC_CSV, dtype=str)
    tx = pd.read_csv(TX_CSV, dtype=str)
    dc["code"] = dc["SECURITY_CODE"].str.zfill(6)
    tx["code"] = tx["code"].str.zfill(6)

    m = dc.merge(tx[["code", "amount", "turnover", "float_cap", "mktcap"]],
                 on="code", how="left")

    m["name"] = m["SECURITY_NAME_ABBR"].astype(str).str.replace(" ", "", regex=False)
    m["price"] = _num(m["CLOSE_PRICE"])
    m["pct"] = _num(m["CHANGE_RATE"])
    m["xl_net"] = _num(m["SUPERDEAL_INFLOW"]) - _num(m["SUPERDEAL_OUTFLOW"])
    m["l_net"] = _num(m["BIGDEAL_INFLOW"]) - _num(m["BIGDEAL_OUTFLOW"])
    m["main_net"] = m["xl_net"] + m["l_net"]
    m["amount"] = _num(m["amount"])                      # 元
    m["turnover"] = _num(m["turnover"])                  # %
    m["float_cap"] = _num(m["float_cap"]) * YI           # 亿元 → 元
    m["mktcap"] = _num(m["mktcap"]) * YI                 # 亿元 → 元
    m["main_pct"] = m["main_net"] / m["amount"] * 100    # 主力净额占成交额%
    m["m_net"] = -m["main_net"]                          # 中小单合计（精确：四档净额和为 0）
    m["s_net"] = ""

    m = m.dropna(subset=["main_net", "price"]).copy()
    m = m.sort_values("main_net", ascending=False)

    # 交易日
    td = str(dc["TRADE_DATE"].iloc[0])[:10]

    # ---- 主表：与旧格式同构（列名/顺序保持一致，绘图脚本无需改动） ----
    cols = ["code", "name", "price", "pct", "main_net", "main_pct",
            "xl_net", "l_net", "m_net", "s_net"]
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for _, r in m.iterrows():
            w.writerow([r["code"], r["name"], r["price"], r["pct"],
                        round(r["main_net"], 0), round(r["main_pct"], 4),
                        round(r["xl_net"], 0), round(r["l_net"], 0),
                        round(r["m_net"], 0), ""])

    # ---- 扩展表：补市值/成交额/换手率 ----
    ecols = ["code", "name", "price", "pct", "amount", "turnover",
             "mktcap", "float_cap", "main_net", "main_pct",
             "xl_net", "l_net", "m_net", "s_net"]
    with open(OUT_EXT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(ecols)
        for _, r in m.iterrows():
            w.writerow([r["code"], r["name"], r["price"], r["pct"],
                        round(r["amount"], 0), round(r["turnover"], 4),
                        round(r["mktcap"], 0), round(r["float_cap"], 0),
                        round(r["main_net"], 0), round(r["main_pct"], 4),
                        round(r["xl_net"], 0), round(r["l_net"], 0),
                        round(r["m_net"], 0), ""])

    # ---- JSON 元数据 ----
    rows = [{"code": r["code"], "name": r["name"], "price": r["price"],
             "pct": r["pct"], "main_net": r["main_net"], "main_pct": r["main_pct"],
             "xl_net": r["xl_net"], "l_net": r["l_net"],
             "m_net": r["m_net"], "s_net": None} for _, r in m.iterrows()]
    meta = {
        "source": "东方财富 datacenter RPT_DMSK_TS_STOCKNEW + 腾讯行情 qt.gtimg.cn",
        "trade_date": td,
        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(rows),
        "note": ("东方财富 clist 接口当日被 IP 级限流，改用数据中心报表与腾讯行情拼装。"
                 "m_net 列为「中单+小单」合计（= -main_net，精确推导）；s_net 留空。"),
        "fields": {
            "main_net": "主力净流入额(元) = 超大单+大单",
            "main_pct": "主力净流入占成交额%",
            "xl_net": "超大单净额", "l_net": "大单净额",
            "m_net": "中小单合计净额", "s_net": "本次无（合并入 m_net）",
        },
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "rows": rows}, f, ensure_ascii=False, indent=1)

    # ---- 打印关键校验 ----
    print(f"[merge] 交易日 {td}；样本 {len(m)} 只")
    print(f"[merge] 主力净额合计 {m['main_net'].sum()/YI:+.1f} 亿")
    print(f"[merge] 超大单合计 {m['xl_net'].sum()/YI:+.1f} 亿  大单合计 {m['l_net'].sum()/YI:+.1f} 亿")
    print(f"[merge] 中小单合计 {m['m_net'].sum()/YI:+.1f} 亿（四档和应为 0）")
    print(f"[merge] 上涨 {(m['pct']>0).sum()} / 下跌 {(m['pct']<0).sum()} / 平 {(m['pct']==0).sum()}")
    print(f"[merge] 涨停 {(m['pct']>=9.8).sum()} 只   跌停 {(m['pct']<=-9.8).sum()} 只")
    print(f"[merge] 写入 {OUT_CSV} / {OUT_EXT} / {OUT_JSON}")


if __name__ == "__main__":
    main()
