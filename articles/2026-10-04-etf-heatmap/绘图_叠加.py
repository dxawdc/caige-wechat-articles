# -*- coding: utf-8 -*-
"""同一张图展示20日涨跌与11项指标。输入原始K线，输出PNG/SVG/JSON/CSV。
运行：python 绘图_叠加.py。仅显示时舍入，所有交易日按基准日期对齐。
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm
from matplotlib.patches import Rectangle
import numpy as np

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "数据" / "etf_K线.json"
OUT = BASE / "图表"
BENCHMARK, N = "510300", 20
NAME_FIXES = {"159819": "人工智能ETF", "159516": "半导体设备ETF"}
NAME_SOURCES = {
    "159819": "https://www.efunds.com.cn/en/fund/159819.shtml",
    "159516": "https://e.gtfund.com/Etrade/Jijin/etflist",
}
plt.rcParams.update({"font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"], "axes.unicode_minus": False, "svg.fonttype": "path"})
SIGNED = LinearSegmentedColormap.from_list("a_share", ["#207657", "#fbfcfd", "#c33543"])
BLUE = LinearSegmentedColormap.from_list("strength", ["#f4f7fc", "#285d9d"])
GOLD = LinearSegmentedColormap.from_list("risk", ["#fff9ec", "#ad6a0d"])
INK, MUTED, RULE = "#18293a", "#657587", "#dae2e9"

# key, 显示名称, 单位, 色彩类别, 色标组, 完整口径
DEFINITIONS = [
    ("m5", "5日动量", "%", "signed", "momentum", "(C_t/C_(t-5)-1)×100"),
    ("m10", "10日动量", "%", "signed", "momentum", "(C_t/C_(t-10)-1)×100"),
    ("m20", "20日动量", "%", "signed", "momentum", "(C_t/C_(t-20)-1)×100；20个收益观测需要21个收盘价"),
    ("accel5", "5日加速度", "百分点", "signed", "accel5", "本5日动量−前5日动量；前5日=(C_(t-5)/C_(t-10)-1)×100"),
    ("excess20", "20日超额", "百分点", "signed", "excess20", "ETF20日动量−沪深300ETF(510300)20日动量；为收益率之差"),
    ("bias20", "MA20乖离", "%", "signed", "bias20", "(最新收盘价/最近20日收盘价均值-1)×100"),
    ("rsi14", "RSI(14)", "0–100", "strength", "hundred", "Wilder RSI：前14个价差涨/跌额均值初始化，其后(前值×13+当日值)/14；使用全部120日历史"),
    ("up20", "上涨占比", "%", "strength", "hundred", "近20日收盘价严格上涨的天数/20×100；平盘算入分母"),
    ("vol20", "年化波动", "%", "risk", "vol20", "近20日简单收益率样本标准差(ddof=1)×√252×100"),
    ("mdd20", "最大回撤", "%", "risk", "mdd20", "max(1-当日收盘价/窗口截至当日最高收盘价)×100；含前一日基准收盘价，共21个价位；显示正幅度"),
    ("volume_ratio", "5/20均量", "倍", "strength", "volume_ratio", "近5日平均成交量/近20日平均成交量；大于1表示近期均量高于20日均量"),
]
METRICS = [dict(zip(("key", "label", "unit", "kind", "scale", "formula"), x)) for x in DEFINITIONS]


def wilder_rsi(closes, period=14):
    diffs = np.diff(closes)
    if len(diffs) < period:
        raise ValueError("RSI历史不足")
    gain, loss = np.maximum(diffs, 0), np.maximum(-diffs, 0)
    ag, al = float(gain[:period].mean()), float(loss[:period].mean())
    for g, l in zip(gain[period:], loss[period:]):
        ag, al = (ag * (period - 1) + float(g)) / period, (al * (period - 1) + float(l)) / period
    if al == 0:
        return 100.0 if ag > 0 else 50.0
    return 100 - 100 / (1 + ag / al)


def calculate():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if BENCHMARK not in data:
        raise ValueError("缺少沪深300ETF基准")
    bs = sorted(data[BENCHMARK]["series"], key=lambda x: x["date"])
    if len(bs) < N + 1:
        raise ValueError("至少需要21个收盘价")
    window = [x["date"] for x in bs[-(N + 1):]]
    rows = []
    for code, fund in data.items():
        series = sorted(fund["series"], key=lambda x: x["date"])
        dates = [x["date"] for x in series]
        if len(dates) != len(set(dates)):
            raise ValueError(f"{code}交易日期重复")
        if dates[-(N + 1):] != window:
            raise ValueError(f"{code}最近21个日期与基准不同；禁止按位置拼接")
        lookup = {x["date"]: x for x in series}
        prices = np.array([x["close"] for x in series], dtype=float)
        if not np.isfinite(prices).all() or np.any(prices <= 0):
            raise ValueError(f"{code}价格无效")
        closes = np.array([lookup[d]["close"] for d in window], dtype=float)
        volumes = np.array([lookup[d]["vol"] for d in window[1:]], dtype=float)
        if not np.isfinite(volumes).all() or np.any(volumes < 0) or volumes.mean() <= 0:
            raise ValueError(f"{code}成交量无效")
        ret = closes[1:] / closes[:-1] - 1
        m5 = (closes[-1] / closes[-6] - 1) * 100
        row = {
            "code": code, "name": NAME_FIXES.get(code, fund["name"]), "source_name": fund["name"],
            "latest_date": window[-1], "close": float(closes[-1]), "daily_pct": (ret * 100).tolist(), "history_count": len(series),
            "m5": float(m5), "m10": float((closes[-1] / closes[-11] - 1) * 100), "m20": float((closes[-1] / closes[0] - 1) * 100),
            "accel5": float(m5 - (closes[-6] / closes[-11] - 1) * 100),
            "bias20": float((closes[-1] / closes[1:].mean() - 1) * 100), "rsi14": float(wilder_rsi(prices)),
            "up20": float(np.count_nonzero(ret > 0) / N * 100), "vol20": float(ret.std(ddof=1) * math.sqrt(252) * 100),
            "mdd20": float(np.max(1 - closes / np.maximum.accumulate(closes)) * 100),
            "volume_ratio": float(volumes[-5:].mean() / volumes.mean()),
        }
        if not math.isclose((np.prod(1 + ret) - 1) * 100, row["m20"], abs_tol=1e-10):
            raise ValueError(f"{code}收益复利核对失败")
        rows.append(row)
    benchmark_m20 = next(r["m20"] for r in rows if r["code"] == BENCHMARK)
    for row in rows:
        row["excess20"] = row["m20"] - benchmark_m20
    rows.sort(key=lambda r: (-r["m20"], r["code"]))
    return {
        "version": "2.0.0", "as_of": window[-1], "start_date": window[1], "baseline_date": window[0], "trading_days": N,
        "dates": window[1:], "universe": "本地数据中的16只宽基与行业ETF代表样本",
        "source": {"file": "数据/etf_K线.json", "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                   "provider": "腾讯证券行情（第三方行情）", "adjustment": "统一请求qfq，部分ETF返回day字段；计算采用接口实际返回价格",
                   "endpoint_template": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market_code},day,,,120,qfq",
                   "scope": "使用已有本地行情快照；基金名称按官方资料修正"},
        "benchmark": {"code": BENCHMARK, "name": "沪深300ETF", "m20": benchmark_m20},
        "name_corrections": [{"code": c, "original": data[c]["name"], "corrected": n, "source_url": NAME_SOURCES[c]} for c, n in NAME_FIXES.items() if c in data],
        "metrics": METRICS, "rows": rows,
    }


def ceil_scale(values, step=1.):
    return max(step, math.ceil(max(abs(float(v)) for v in values) / step) * step)


def scales_for(data):
    rows = data["rows"]
    scales = {"daily": ceil_scale([v for r in rows for v in r["daily_pct"]]),
              "momentum": ceil_scale([r[k] for r in rows for k in ("m5", "m10", "m20")]), "hundred": 100.}
    for key in ("accel5", "excess20", "bias20", "mdd20"):
        scales[key] = ceil_scale([r[key] for r in rows])
    scales["vol20"] = ceil_scale([r["vol20"] for r in rows], 5)
    scales["volume_ratio"] = ceil_scale([r["volume_ratio"] for r in rows], .5)
    return scales


def text_on(color):
    def linear(v):
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    lum = sum(w * linear(c) for w, c in zip((.2126, .7152, .0722), color[:3]))
    # 从纯黑与纯白中选对比度更高者，保证普通字号文字对比度至少4.5:1。
    return "white" if 1.05 / (lum + .05) > (lum + .05) / .05 else "black"


def fmt(value, signed=False, decimals=1):
    value = 0. if abs(value) < .5 * 10 ** (-decimals) else value
    return f"{value:+.{decimals}f}" if signed else f"{value:.{decimals}f}"


def draw(data):
    rows, dates = data["rows"], data["dates"]
    scales = scales_for(data)
    data["color_scales"] = scales
    label_w, daily_w, metric_w, gap = 4.1, .94, 1.22, .34
    daily_start = label_w
    positions, x = [], daily_start + N * daily_w + gap
    for i, metric in enumerate(METRICS):
        if i in (6, 8, 10):
            x += gap
        positions.append(x)
        x += metric_w
    total_w, nrows = x, len(rows)
    fig = plt.figure(figsize=(29.4, max(11.7, nrows * .48 + 4.0)), facecolor="white")
    ax = fig.add_axes([.025, .20, .95, .62])
    ax.set_xlim(0, total_w)
    ax.set_ylim(nrows + 3.25, -.16)
    ax.axis("off")
    fig.text(.027, .936, "ETF 近20个交易日 · 涨跌与多维指标", fontsize=27, fontweight="bold", color=INK)
    fig.text(.028, .895, f"{data['start_date']} — {data['as_of']}  |  {nrows}只ETF代表样本  |  按20日动量由高到低排列", fontsize=13, color=MUTED)
    fig.text(.975, .939, "20 + 11", fontsize=25, color="#355c78", ha="right", fontweight="bold")
    fig.text(.975, .902, "20日涨跌 + 11项指标", fontsize=12, color=MUTED, ha="right")
    ax.text(.06, .37, "ETF / 代码", fontsize=12, color=INK, fontweight="bold", va="center")
    def group(left, width, name, cue):
        ax.add_patch(Rectangle((left, .02), width, .65, facecolor="#f0f4f8", edgecolor="none"))
        ax.text(left + width / 2, .29, name, fontsize=12, fontweight="bold", color=INK, ha="center", va="center")
        ax.text(left + width / 2, .89, cue, fontsize=9.7, color=MUTED, ha="center", va="center")
    group(daily_start, N * daily_w, "逐日涨跌幅  /  %", "日期从左到右：由早到晚")
    group(positions[0], 6 * metric_w, "动量与趋势", "有符号数值；红正绿负")
    group(positions[6], 2 * metric_w, "强弱与持续性", "蓝色越深，数值越高")
    group(positions[8], 2 * metric_w, "风险", "金色越深，波动 / 回撤越大")
    group(positions[10], metric_w, "量能", ">1 放量")
    daily_norm = TwoSlopeNorm(vmin=-scales["daily"], vcenter=0, vmax=scales["daily"])
    for j, date in enumerate(dates):
        ax.text(daily_start + (j + .5) * daily_w, 1.56, date[5:], ha="center", va="center", fontsize=9.7, color=INK)
    for i, metric in enumerate(METRICS):
        xm = positions[i] + metric_w / 2
        ax.text(xm, 1.40, metric["label"], ha="center", va="center", fontsize=10., color=INK, fontweight="bold" if metric["key"] == "m20" else "normal")
        ax.text(xm, 1.90, metric["unit"], ha="center", va="center", fontsize=8.7, color=MUTED)
        maximum = scales[metric["scale"]]
        bound = f"±{maximum:g}" if metric["kind"] == "signed" else f"0–{maximum:g}"
        ax.text(xm, nrows + 2.90, bound, ha="center", va="center", fontsize=8.7, color=MUTED)
    y0 = 2.42
    for ri, row in enumerate(rows):
        yy = y0 + ri
        if ri % 2 == 0:
            ax.add_patch(Rectangle((0, yy), label_w - .07, 1, facecolor="#f8fafc", edgecolor="none"))
        ax.text(.08, yy + .5, f"{ri + 1:02}", fontsize=10.5, color=MUTED, va="center")
        ax.text(.57, yy + .5, row["name"], fontsize=12, fontweight="bold" if row["code"] == BENCHMARK else "normal", color=INK, va="center")
        ax.text(label_w - .19, yy + .51, row["code"], fontsize=9, color=MUTED, va="center", ha="right")
        for j, value in enumerate(row["daily_pct"]):
            xx, color = daily_start + j * daily_w, SIGNED(daily_norm(value))
            ax.add_patch(Rectangle((xx, yy), daily_w, 1, facecolor=color, edgecolor="white", linewidth=.8))
            ax.text(xx + daily_w / 2, yy + .5, fmt(value, True, 2), ha="center", va="center", fontsize=9.1, color=text_on(color))
        for i, metric in enumerate(METRICS):
            value, maximum = row[metric["key"]], scales[metric["scale"]]
            if metric["kind"] == "signed":
                color = SIGNED(TwoSlopeNorm(vmin=-maximum, vcenter=0, vmax=maximum)(value))
            else:
                color = (GOLD if metric["kind"] == "risk" else BLUE)(Normalize(0, maximum)(value))
            xx = positions[i]
            ax.add_patch(Rectangle((xx, yy), metric_w, 1, facecolor=color, edgecolor="white", linewidth=.8))
            displayed = fmt(value, metric["kind"] == "signed", 2 if metric["key"] == "volume_ratio" else 1)
            ax.text(xx + metric_w / 2, yy + .5, displayed, ha="center", va="center", fontsize=10.5, color=text_on(color), fontweight="bold" if metric["key"] == "m20" else "normal")
    ax.plot([0, total_w], [y0 - .1, y0 - .1], color=RULE, lw=.8)
    cax = fig.add_axes([.151, .153, .34, .018])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=daily_norm, cmap=SIGNED), cax=cax, orientation="horizontal")
    cb.set_ticks([-scales["daily"], -scales["daily"] / 2, 0, scales["daily"] / 2, scales["daily"]])
    cb.set_ticklabels([f"{v:+g}%" if v != 0 else "0" for v in cb.get_ticks()])
    cb.ax.tick_params(labelsize=10, length=0, pad=7)
    cb.outline.set_visible(False)
    fig.text(.029, .157, "每日涨跌色标", fontsize=11, color=MUTED)
    fig.text(.518, .164, "指标色标：各列独立；5 / 10 / 20日动量共用色标。不同单位、不同色标的颜色深浅不可横向比较。", fontsize=11, color=MUTED)
    fig.text(.029, .093, "动量 = 累计复利涨跌；加速度 = 本5日 − 前5日；20日超额 = 相对沪深300ETF（510300）的收益率差。", fontsize=11, color=MUTED)
    fig.text(.029, .063, "上涨占比 = 上涨天数 / 20；年化波动 = 日收益样本标准差 × √252；最大回撤显示损失幅度；5/20均量 = 5日均量 / 20日均量。", fontsize=11, color=MUTED)
    fig.text(.029, .029, "数据：腾讯证券日线（qfq请求），截至 " + data["as_of"] + " 收盘。RSI(14)采用Wilder平滑；返回字段与指标口径见配套文件。", fontsize=10.5, color=MUTED)
    fig.text(.975, .029, "可以叫我才哥", fontsize=11, color=MUTED, ha="right")
    OUT.mkdir(exist_ok=True)
    png, svg = OUT / "ETF热力图_叠加多维度.png", OUT / "ETF热力图_叠加多维度.svg"
    fig.savefig(png, dpi=180, facecolor="white")
    fig.savefig(svg, facecolor="white", metadata={"Title": "ETF近20日涨跌与11项指标", "Description": f"{data['start_date']}至{data['as_of']}，{nrows}只ETF"})
    plt.close(fig)
    return [png, svg]


def export(data):
    jp, cp = BASE / "数据" / "etf_多维指标.json", BASE / "数据" / "etf_多维指标.csv"
    jp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    headers = ["排名", "ETF", "代码", "截至日期", "最新收盘价(qfq请求)"] + data["dates"] + [f"{m['label']}({m['unit']})" for m in METRICS]
    with cp.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for i, row in enumerate(data["rows"], 1):
            writer.writerow([i, row["name"], row["code"], row["latest_date"], row["close"]] + row["daily_pct"] + [row[m["key"]] for m in METRICS])
    lines = ["# ETF 多维热力图", "", f"版本：{data['version']}；生成日期：2026-10-04；行情截至：{data['as_of']}。", "",
             f"图中展示现有数据中的{len(data['rows'])}只ETF代表样本，每行一只ETF，左侧20个交易日逐日涨跌，右侧11项指标。按20日动量由高到低排列。", "",
             f"收益窗口：{data['start_date']}至{data['as_of']}；窗口前基准收盘日：{data['baseline_date']}。", "",
             "## 使用", "", "PNG用于查看高清图片，SVG可在浏览器内放大。CSV提供完整数值，JSON提供完整精度、色标和来源。", "",
             "安装numpy与matplotlib后，在本目录运行：", "", "```powershell", "python 绘图_叠加.py", "```", "",
             "## 指标口径", "", "C为接口返回的收盘价（统一请求qfq），t为最新交易日，下标为交易日位移。每日涨跌=(当日收盘/前一交易日收盘−1)×100。", "",
             "| 指标 | 单位 | 定义 |", "| --- | --- | --- |"]
    lines.extend(f"| {m['label']} | {m['unit']} | {m['formula']} |" for m in METRICS)
    lines.extend(["", "## 颜色与解读", "", "每日涨跌与动量/趋势采用A股常用的红正绿负，数值保留正负号。每列下方标出色标范围，5/10/20日动量共用色标，其余指标独立；不同单位、不同色标之间不比较颜色深浅。", "",
                  "蓝色深浅表示数值大小，金色深浅表示历史波动/回撤幅度。上涨占比与RSI使用0–100色标，量能以1为放量/缩量分界。RSI、量能与动量描述历史观测，年化波动为252日换算。", "",
                  "最大回撤包含前一日基准收盘价，计21个价格，按正幅度展示。20日超额以沪深300ETF(510300)为比较基准，单位为百分点。价格表现按接口返回序列计算。", "",
                  "## 来源", "", "现有数据/etf_K线.json行情快照，采集接口：", "",
                  "`https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market_code},day,,,120,qfq`", "",
                  f"源文件SHA256：`{data['source']['sha256']}`。", "",
                  "腾讯证券行情为第三方来源；统一请求qfq，部分ETF实测返回day字段，采集脚本记录实际返回字段。跨分红/拆分期复用时需核对复权，价格表现不能直接视为现金分红再投资后的总回报。本次核验日期、价格与成交量完整性，全部市场价格未逐笔与交易所交叉核验。", "",
                  "名称按基金公司官方资料校正，保留代码和原始行情：", ""])
    lines.extend(f"- {x['code']}：原标签“{x['original']}”改为“{x['corrected']}”；[基金公司资料]({x['source_url']})。" for x in data["name_corrections"])
    lines.extend(["", "## 物料", "", "高清PNG、矢量SVG、绘图源码、原始K线、完整指标CSV/JSON、口径说明、验收结果，以及一份最新下载包。", ""])
    (BASE / "多维热力图说明.md").write_text("\n".join(lines), encoding="utf-8")
    return [jp, cp]


def main():
    data = calculate()
    for path in draw(data) + export(data):
        print(path.name)
    print(f"ETF={len(data['rows'])}; daily_columns=20; metrics={len(METRICS)}; as_of={data['as_of']}")


if __name__ == "__main__":
    main()
