# -*- coding: utf-8 -*-
"""v1.0.0 | 2026-09-21 | 从分时缓存提取上证指数，生成"全市场分时"节奏图输入。

背景：东财没有"全市场 5195 只直接聚合"的分钟级资金流接口，唯一分钟级四档
接口 fflow/kline 只对单只/单指数返回。用户决定先"只看上证指数试试"——
用上证指数(1.000001, 沪市)这一条完整全天分时，作为章节二"钱是什么时候
进来的"的口径。

上证指数分时已在 `分时缓存_慢速.json` 里采到（240 条，全天主力 +30.6 亿），
本脚本把它转成 `分时资金流_全市场.json`（含 times + main/small/mid/large/super），
供 `绘图_资金结构图.py` 的 rhythm() 直接读取，无需再发起任何网络请求。

口径说明（重要）：上证指数只覆盖沪市（约全市场一半市值），不是全市场；
末条主力约 +30.6 亿，对应全市场 +108.5 亿。文件名沿用"全市场"仅为复用绘图
脚本的读取路径，真实口径以 meta.note 为准。
"""
from __future__ import annotations
import json
import os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "分时缓存_慢速.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "分时资金流_全市场.json")
INDEX_SH = "1.000001"


def main():
    with open(SRC, encoding="utf-8") as f:
        cache = json.load(f)

    if INDEX_SH not in cache:
        raise SystemExit(f"[err] {SRC} 中找不到上证指数 {INDEX_SH}")

    sh = cache[INDEX_SH]["series"]
    # fflow/kline 字段顺序：[时间,主力,小单,中单,大单,超大单]
    times = [r[0] for r in sh]
    out = {
        "meta": {
            "source": "东财 fflow/kline 单指数",
            "index": INDEX_SH,
            "name": cache[INDEX_SH].get("name", "上证指数"),
            "note": "口径 = 上证指数(沪市) 分时资金流，非全市场；"
                    "上证指数仅覆盖沪市（约全市场一半市值），末条主力约 +30.6 亿，"
                    "对应全市场 +108.5 亿。",
        },
        "times": times,
        "main": [float(r[1]) for r in sh],
        "small": [float(r[2]) for r in sh],
        "mid": [float(r[3]) for r in sh],
        "large": [float(r[4]) for r in sh],
        "super": [float(r[5]) for r in sh],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    n = len(times)
    main_last = out["main"][-1] / 1e8
    print(f"[done] 已从 {os.path.basename(SRC)} 提取上证指数 {n} 条 → "
          f"{os.path.basename(OUT)}，全天主力 {main_last:+.1f} 亿")


if __name__ == "__main__":
    main()
