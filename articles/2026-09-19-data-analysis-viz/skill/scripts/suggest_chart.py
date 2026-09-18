# -*- coding: utf-8 -*-
"""suggest_chart —— 按分析意图与字段结构推荐图表。

设计原则见 references/04-图表匹配.md。这个脚本把"三步定图型"规则化，
但它只是辅助：最终决策仍由分析逻辑决定，不要因为脚本推荐就放弃专业判断。

用法一（结构化 spec）：
    python suggest_chart.py --spec chart_spec.json

用法二（命令行速查）：
    python suggest_chart.py --intent compare --dim-unique 31 --label-len long --rows 12000
    python suggest_chart.py --intent trend --series 8 --time-points 240
    python suggest_chart.py --intent correlation --rows 200000 --measures 2

spec 字段说明：
{
  "intent": "compare|trend|proportion|distribution|correlation|hierarchy|
             relation|logic|geo|composite",
  "dimension": {"name": "地区", "type": "category", "unique": 31, "label_len": "long"},
  "time": {"name": "月份", "points": 12, "continuous": true},
  "measures": [{"name": "销售额", "skew": 2.4, "has_negative": false}],
  "series": 3,
  "rows": 12000,
  "constituents_sum_100": true,   # 仅 proportion 需要
  "audience": "business|public|academic|design",
  "media": "mobile|screen|print|slide",
  "audience_literacy": "low|medium|high"
}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ------------------------------------------------------------ 规则库

def _ranked(*pairs):
    """pairs: (名称, 理由)；靠前的优先级高。"""
    return [{"chart": n, "why": w} for n, w in pairs]


def recommend(spec: dict) -> dict:
    intent = spec.get("intent", "compare")
    rows = int(spec.get("rows") or 0)
    dim = spec.get("dimension") or {}
    unique = int(dim.get("unique") or 0)
    label_len = dim.get("label_len", "short")
    time = spec.get("time") or {}
    points = int(time.get("points") or 0)
    series = int(spec.get("series") or 1)
    measures = spec.get("measures") or []
    n_measures = len(measures)
    sum100 = bool(spec.get("constituents_sum_100"))
    literacy = spec.get("audience_literacy", "medium")
    media = spec.get("media", "screen")

    out: dict = {"intent": intent, "recommended": [], "avoid": [], "checklist": []}

    if intent == "compare":
        if unique and unique > 12:
            out["recommended"] = _ranked(
                ("排序条形图", f"类别 {unique} 个偏多，水平条形图 + 排序后最易读"),
                ("点图/棒棒糖图", "类别多时视觉更轻盈"),
                ("分组柱状图", "如果有 2–4 个子系列，可分组对比"),
            )
            out["avoid"] = [
                ("饼图", f"类别 {unique} 个远超 5 个，扇形无法区分"),
                ("垂直柱状图", "标签长且类别多时会被挤压"),
            ]
        elif label_len == "long":
            out["recommended"] = _ranked(
                ("条形图（水平）", "分类标签较长，水平布局不用旋转标签"),
                ("棒棒糖图", "类别不多但要减轻视觉重量"),
            )
        else:
            out["recommended"] = _ranked(
                ("柱状图", "类别少、标签短，位置/长度通道精度最高"),
                ("分组柱状图" if series > 1 else "棒棒糖图",
                 f"{series} 个子系列，分组柱状图可同时比较" if series > 1 else "类别较多时的轻盈替代"),
            )
        if series >= 5:
            out["avoid"].append(("分组柱状图", f"{series} 个子系列会让每根柱子过窄，改用小倍数分面"))
        out["checklist"].append("柱状图/面积图的纵轴基线必须为 0，否则比例失真")

    elif intent == "trend":
        if not points:
            out["recommended"] = _ranked(("（缺少时间字段）", "趋势图必须有一个有序时间变量，请补充"))
        elif series <= 1:
            out["recommended"] = _ranked(
                ("折线图", "单系列看趋势与拐点，位置通道精度最高"),
                ("面积图", "若重点是累计总量而非单点读数"),
            )
        elif series <= 5:
            out["recommended"] = _ranked(
                ("多系列折线图", f"{series} 条线，建议高亮 1 条、其余转灰"),
                ("小倍数分面", "各系列量级差异大时，分面比叠加更清晰"),
            )
        else:
            out["recommended"] = _ranked(
                ("小倍数分面", f"{series} 个系列，叠加会缠绕"),
                ("热力图（时间 × 系列）", "系列很多时用颜色表示数值密度"),
            )
            out["avoid"] = [("多系列折线图", f"{series} 条线重叠严重，无法分辨")]
        if points > 50:
            out["avoid"].append(("柱状图", f"时间点 {points} 个过多，改用折线"))
        if points > 300:
            out["checklist"].append(f"时间点 {points} 个，建议改热力图或加移动平均线")
        out["checklist"].append("时间轴必须从左到右；缺失周期显式留空，不要让折线跨过缺口")

    elif intent == "proportion":
        if not sum100:
            out["recommended"] = _ranked(
                ("（不适用占比图）→ 柱状图", "各部分不构成 100% 整体，占比图前提不成立"),
            )
            out["avoid"] = [("饼图", "数据不构成整体，饼图无意义"),
                            ("百分比堆叠条形图", "同上")]
        elif unique and unique <= 5:
            out["recommended"] = _ranked(
                ("饼图 / 环形图", f"{unique} 个类别，符合 ≤5 的上限"),
                ("华夫饼图", "面向大众时更直观"),
            )
        elif unique and unique <= 12:
            out["recommended"] = _ranked(
                ("百分比堆叠条形图", f"{unique} 个类别，横向排列容纳更多"),
                ("华夫饼图", "类别中等时的直观替代"),
                ("饼图 + 合并'其他'", "把长尾合并为一项后再用饼图"),
            )
            out["avoid"] = [("饼图（不合并）", f"{unique} 个扇形过多，小扇形不可读")]
        else:
            out["recommended"] = _ranked(
                ("排序条形图 + 累计曲线", "帕累托图同时看排名与累计贡献"),
                ("树图 Treemap", "类别很多时的空间填充方案"),
            )
            out["avoid"] = [("饼图", f"{unique} 个类别完全不可读")]
        out["checklist"].append("确认各类别合计为 100%；用面积类图表时把数据映射到面积而不是半径")

    elif intent == "distribution":
        if rows and rows < 100:
            out["recommended"] = _ranked(
                ("散点图 / 蜂群图", f"样本量 {rows}，可以逐个点展示"),
                ("箱线图", "分组比较分布的中位数与四分位"),
            )
        elif rows and rows > 10000:
            out["recommended"] = _ranked(
                ("密度图 KDE", f"样本量 {rows}，平滑后看整体形状"),
                ("分箱热力图", "多维分布时用颜色表示密度"),
                ("箱线图（分组）", "同时比较多组时仍是首选"),
            )
        else:
            out["recommended"] = _ranked(
                ("直方图", "单变量分布的首选，柱子紧贴表示区间"),
                ("箱线图", "分组比较中位数与离散程度"),
                ("密度图", "想平滑看形状时"),
            )
        for m in measures:
            if m.get("skew") is not None and abs(m["skew"]) >= 1:
                out["checklist"].append(
                    f"字段 `{m.get('name')}` 偏度 {m['skew']:.2f}，建议对数轴或分位数表达，避免长尾压扁主体"
                )
        out["avoid"] = [("饼图", "分布不是占比，不能用饼图"),
                        ("只报均值", "均值会掩盖长尾、多峰和极端值")]
        out["checklist"].append("发现多峰时先按可能的隐藏分层变量分组重画")

    elif intent == "correlation":
        if n_measures >= 2 and n_measures <= 2:
            if rows and rows >= 5000:
                out["recommended"] = _ranked(
                    ("六边形分箱图 / 二维密度图", f"{rows} 个点，直接画散点会完全重叠"),
                    ("抽样散点图", "随机抽样后仍用散点，保留点的可解释性"),
                    ("半透明散点 + 回归线", "透明度可缓解重叠"),
                )
            else:
                out["recommended"] = _ranked(
                    ("散点图 + 回归线 + 置信带", "两个连续数值变量的相关性首选，双位置通道最准"),
                    ("气泡图", "有第三个数值变量时映射到面积"),
                )
        elif n_measures >= 3:
            if n_measures <= 4:
                out["recommended"] = _ranked(
                    ("气泡图", "三个数值变量（x、y、面积）+ 分类映射到颜色，上限 4 个变量"),
                    ("散点图矩阵", "想两两对比时"),
                )
            else:
                out["recommended"] = _ranked(
                    ("相关性热力矩阵", f"{n_measures} 个变量，先看总览再深入"),
                    ("散点图矩阵", f"{n_measures} 个变量在 6 个以内时可用"),
                    ("平行坐标图", "想看多维模式分层"),
                )
        out["avoid"] = [
            ("双折线图代替散点图", "折线暗示了顺序关系，两个数值变量之间并不存在这种顺序"),
            ("把分类变量放到散点轴", "分类变量不该映射到连续通道，应改为颜色或分面"),
            ("3D 散点图", "透视会扭曲距离感知，且难以精确读数"),
        ]
        out["checklist"].append("相关系数必须同时给出样本量与置信区间；去掉极端值后重算一遍")
        out["checklist"].append("存在明显分层变量时必须分组重算，防止辛普森悖论")

    elif intent == "hierarchy":
        depth = int(spec.get("depth") or 2)
        if depth <= 3:
            out["recommended"] = _ranked(
                ("树图 Treemap", "层级 + 占比，空间利用率最高，适合发现大块"),
                ("旭日图", "径向展开，层级 ≤ 3 层时可读"),
                ("打包圆形图", "形状圆润，但空间利用率低于树图"),
            )
        else:
            out["recommended"] = _ranked(
                ("拆分多张图", f"层级深度 {depth} 层过深，建议按层拆图"),
                ("可交互树图", "用交互展开代替一次画全"),
            )
            out["avoid"] = [("旭日图", f"{depth} 层会让最外层细环不可读")]
        out["checklist"].append("父节点面积必须等于子节点面积之和，否则比例不可信")

    elif intent == "relation":
        nodes = int(spec.get("nodes") or 0)
        if nodes and nodes > 200:
            out["recommended"] = _ranked(
                ("邻接矩阵热力图", f"{nodes} 个节点，网络图会变成一团毛线"),
                ("筛选度阈值后的网络图", "只保留连接数高的节点"),
            )
            out["avoid"] = [("力导向网络图", f"{nodes} 个节点会严重重叠")]
        else:
            out["recommended"] = _ranked(
                ("桑基图", "多级流向 + 量级，需保证每个节点流入 = 流出"),
                ("力导向网络图", "看社群结构与关键节点"),
                ("弧长连接图", "节点少、流向清晰时视觉效果好"),
            )
        out["checklist"].append("桑基图每个节点的流入总量必须等于流出总量")

    elif intent == "logic":
        out["recommended"] = _ranked(
            ("流程图", "步骤顺序"),
            ("鱼骨图", "归因分析"),
            ("甘特图", "任务时间跨度与并行关系"),
            ("韦恩图", "集合包含与交叠"),
        )
        out["checklist"].append("逻辑示意图不承载数值精度，涉及数值的部分另用统计图表")

    elif intent == "geo":
        out["recommended"] = _ranked(
            ("分级填色地图", "数值在区域间的分布，最通用"),
            ("变形地图 Cartogram", "想让面积代表数值而非地理面积"),
            ("点密度地图", "事件的绝对分布（注意隐私）"),
            ("地图 + 内嵌图表", "地图上叠加饼图/柱状图，需控制内嵌数量"),
        )
        out["checklist"].append("地图面积大的地区视觉权重会被高估，比较人均/密度时改用变形地图或分级")
        out["checklist"].append("涉及中国地图必须使用符合国家标准的正确地图数据")

    elif intent == "composite":
        combo = spec.get("combo")
        table = {
            "trend+composition": ("堆叠面积图", "同时看总量与构成随时间变化；不适合比较中间层大小"),
            "trend+rank": ("排序折线图 / 动态追逐柱状图", "关注排名变化而非绝对取值"),
            "trend+decomposition": ("瀑布图 / 柱线组合图", "瀑布图看增量如何累积；柱线组合图柱=量、线=率"),
            "dist+correlation": ("气泡图 / 二维密度图", "变量不超过 4 个"),
            "hierarchy+share": ("多层树图 / 旭日图", "层级不超过 3 层"),
            "relation+time": ("动态网络图", "静态交付时信息会丢失，需保留关键帧"),
        }
        if combo in table:
            chart, why = table[combo]
            out["recommended"] = _ranked((chart, why))
        else:
            out["recommended"] = _ranked(
                ("上下对齐的双子图（共享横轴）", "复合目的最稳妥的方案，避免双轴误导"),
                ("气泡图", "两个数值 + 尺寸 + 颜色"),
            )
        out["avoid"] = [("双轴图随意缩放", "会人为制造或抹平两个系列的同步感，除非有明确理由并标注轴范围")]
    else:
        out["recommended"] = _ranked(
            ("请先明确分析意图", "一句话只允许一个意图；出现两个就画两张图")
        )

    # ---- 通用适配
    if media == "mobile":
        out["checklist"].append("手机端：类别数再减一半、字号加大、必要时拆成多张图")
    if media == "print":
        out["checklist"].append("印刷：确认灰度打印后仍可区分，避免仅靠色相区分类别")
    if literacy == "low":
        out["checklist"].append("受众视觉素养较低：优先用地图、柱状图、折线图、饼图这类常见图表，并且减少编码层数")
    if rows and rows > 1_000_000:
        out["checklist"].append(f"数据量 {rows} 行，先在数据仓库侧聚合到图表能承载的粒度")

    out["checklist"].append("反向自检：3 秒内能读出结论吗？坐标轴有误导性截断吗？图例离数据近吗？")
    return out


# ------------------------------------------------------------ 输出

def render(result: dict) -> str:
    lines = [f"## 分析意图：{result['intent']}", "", "### 推荐（按优先级）", ""]
    for i, r in enumerate(result["recommended"], 1):
        lines.append(f"{i}. **{r['chart']}** —— {r['why']}")
    if result["avoid"]:
        lines += ["", "### 慎用/禁用", ""]
        for name, why in result["avoid"]:
            lines.append(f"- **{name}**：{why}")
    if result["checklist"]:
        lines += ["", "### 落地检查", ""]
        lines += [f"- {c}" for c in result["checklist"]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="按分析意图推荐图表类型")
    ap.add_argument("--spec", help="JSON 规格文件路径")
    ap.add_argument("--intent", help="compare|trend|proportion|distribution|correlation|hierarchy|relation|logic|geo|composite")
    ap.add_argument("--dim-unique", type=int, default=0, help="分类维度的唯一值数量")
    ap.add_argument("--label-len", default="short", choices=["short", "long"])
    ap.add_argument("--time-points", type=int, default=0)
    ap.add_argument("--series", type=int, default=1)
    ap.add_argument("--measures", type=int, default=1, help="数值字段个数")
    ap.add_argument("--rows", type=int, default=0)
    ap.add_argument("--nodes", type=int, default=0, help="关系图的节点数")
    ap.add_argument("--depth", type=int, default=2, help="层级图的深度")
    ap.add_argument("--combo", default=None, help="复合目的，如 trend+composition")
    ap.add_argument("--sum100", action="store_true", help="占比数据是否构成 100%")
    ap.add_argument("--media", default="screen", choices=["mobile", "screen", "print", "slide"])
    ap.add_argument("--literacy", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非 Markdown")
    args = ap.parse_args(argv)

    if args.spec:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    elif args.intent:
        spec = {
            "intent": args.intent,
            "dimension": {"unique": args.dim_unique, "label_len": args.label_len},
            "time": {"points": args.time_points},
            "series": args.series,
            "measures": [{"name": f"m{i+1}"} for i in range(args.measures)],
            "rows": args.rows,
            "nodes": args.nodes,
            "depth": args.depth,
            "combo": args.combo,
            "constituents_sum_100": args.sum100,
            "media": args.media,
            "audience_literacy": args.literacy,
        }
    else:
        ap.print_help()
        return 1

    result = recommend(spec)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
