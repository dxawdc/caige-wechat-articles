# -*- coding: utf-8 -*-
"""把 分时缓存_慢速.json（key 带市场前缀，含上证指数）转成绘图脚本认识的标准格式。

标准格式（与旧 分时资金流_候选股.json 一致）：
  key = 6 位纯代码（如 "300476"）
  value = {"name": str, "main_net_final": float(元), "series": [[时间,主力,小单,中单,大单,超大单], ...]}
其中 series 里 主力 是"超大单+大单"的当日累计净额（元），即绘图用的主序列。
去掉上证指数（它不属于候选池，会让"候选池累计"口径错乱）。
"""
import csv
import json

CACHE = "分时缓存_慢速.json"
OUT = "分时资金流_候选股.json"


def main():
    with open(CACHE, encoding="utf-8") as f:
        raw = json.load(f)

    # 读全市场表，取每只的收盘主力净额（元），用于补 main_net_final
    final = {}
    with open("资金流向_全市场.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["main_net"] not in ("-", ""):
                final[r["code"]] = float(r["main_net"])

    out = {}
    skipped = []
    for key, v in raw.items():
        if not v.get("series"):
            skipped.append((key, "无 series"))
            continue
        # key 形如 "0.300476" / "1.600664"；去掉市场前缀得到 6 位代码
        code = key.split(".")[-1]
        if code == "000001" and v.get("name") == "上证指数":
            skipped.append((key, "上证指数（剔除）"))
            continue
        out[code] = {
            "name": v["name"].replace(" ", ""),
            "main_net_final": final.get(code, 0.0),
            "series": v["series"],
        }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"[done] 写入 {OUT}：{len(out)} 只候选股")
    if skipped:
        print("[skip]", ", ".join(f"{k}({r})" for k, r in skipped))
    # 核对榜首
    top_in = max(out.items(), key=lambda kv: kv[1]["main_net_final"])
    top_out = min(out.items(), key=lambda kv: kv[1]["main_net_final"])
    print(f"[核对] 流入榜首 {top_in[0]} {top_in[1]['name']} "
          f"{top_in[1]['main_net_final']/1e8:+.2f}亿")
    print(f"[核对] 流出榜首 {top_out[0]} {top_out[1]['name']} "
          f"{top_out[1]['main_net_final']/1e8:+.2f}亿")


if __name__ == "__main__":
    main()
