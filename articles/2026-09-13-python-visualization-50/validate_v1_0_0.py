"""v1.0.0 | 独立检查保存后的数据与文件，不重用绘图中的断言结果。"""

from pathlib import Path
import json, hashlib, ast
import numpy as np
import pandas as pd
from PIL import Image
from scipy.stats import t

ROOT = Path(__file__).parent
OUT = ROOT / "outputs"
checks = []


def check(name, condition):
    checks.append({"name": name, "pass": bool(condition)})
    if not condition:
        raise AssertionError(name)


def df(n, suffix="data"):
    return pd.read_csv(OUT / f"{n:02d}_v1.0.0_{suffix}.csv")


mapping = json.loads(
    (ROOT / "案例来源映射_v1.0.0.json").read_text(
        encoding="utf-8"
    )
)
check(
    "50个编号连续且唯一",
    [e["id"] for e in mapping] == list(range(1, 51)),
)
hashes = []
for e in mapping:
    n = e["id"]
    code = ROOT / "cases" / f"case_{n:02d}_v1_0_0.py"
    ast.parse(code.read_text(encoding="utf-8"))
    png = OUT / f"{n:02d}_v1.0.0.png"
    with Image.open(png) as im:
        check(
            f"{n:02d}图片非空且可读取",
            im.width >= 1000
            and np.asarray(im.convert("RGB")).std() > 10,
        )
    check(
        f"{n:02d}有SVG",
        (OUT / f"{n:02d}_v1.0.0.svg").stat().st_size > 1000,
    )
    record = json.loads(
        (OUT / f"{n:02d}_v1.0.0_metrics.json").read_text(
            encoding="utf-8"
        )
    )
    check(
        f"{n:02d}记录标题与案例对应",
        record["title"] == e["title"] and record["case"] == n,
    )
    for name in e["tables"]:
        check(
            f"{n:02d}数据{name}非空",
            len(pd.read_csv(OUT / name)) > 0,
        )
    hashes.append(hashlib.sha256(png.read_bytes()).hexdigest())
check("50张图字节各不相同", len(set(hashes)) == 50)
check(
    "交互文件数为7", len(list(OUT.glob("*_v1.0.0.html"))) == 7
)
check(
    "堆叠收入四个合计",
    df(3).iloc[:, 1:].sum(axis=1).tolist()
    == [110, 124, 143, 171],
)
check(
    "分组与堆叠不是同一数据",
    set(df(2).columns) != set(df(3).columns),
)
check(
    "圆面积正比于调用量",
    np.allclose(df(8).半径 ** 2 / df(8).调用量, 0.85**2 / 800),
)
check("日历连续31天且唯一", df(9).日期.nunique() == 31)
check("单位点阵合计94", df(10).交付量.sum() == 94)
check(
    "移动平均前6日缺失而后续完整",
    df(11)["7日均值"].iloc[:6].isna().all()
    and df(11)["7日均值"].iloc[6:].notna().all(),
)
check(
    "百分比图分母600/800/1200",
    df(22)[["新客", "老客"]].sum(axis=1).tolist()
    == [600, 800, 1200],
)
check(
    "华夫图合计100且非负",
    df(24).百分比.sum() == 100 and (df(24).百分比 >= 0).all(),
)
ohlc = df(20)
check(
    "OHLC高低关系",
    (
        (ohlc.最高 >= ohlc[["开盘", "收盘"]].max(axis=1))
        & (ohlc.最低 <= ohlc[["开盘", "收盘"]].min(axis=1))
    ).all(),
)
check(
    "漏斗非递增且最终7.8%",
    (df(25).人数.diff().dropna() <= 0).all()
    and np.isclose(
        df(25).人数.iloc[-1] / df(25).人数.iloc[0], 0.078
    ),
)
check("会话时长全部正值", (df(26).时长 > 0).all())
check("箱线图保留303行", len(df(28)) == 303)
check(
    "蜂群每组35人", (df(30).groupby("组别").size() == 35).all()
)
check(
    "7000条请求的耗时全部正值",
    len(df(32)) == 7000 and (df(32).耗时 > 0).all(),
)
corr = df(38, "correlation").iloc[:, 1:].to_numpy()
check(
    "相关矩阵对称且范围正确",
    np.allclose(corr, corr.T)
    and np.allclose(np.diag(corr), 1)
    and (abs(corr) <= 1).all(),
)
sim = df(39)
check(
    "辛普森反转实际成立",
    sim.投入.corr(sim.得分) < 0
    and all(
        g.投入.corr(g.得分) > 0 for _, g in sim.groupby("任务")
    ),
)
check("旭日叶子合计200", df(40).收入.sum() == 200)
check("目录容量合计1100", df(41).容量.sum() == 1100)
import networkx as nx

G = nx.from_pandas_edgelist(
    df(42), "上级", "下级", create_using=nx.DiGraph
)
check(
    "组织树10点9边",
    nx.is_arborescence(G)
    and len(G) == 10
    and G.number_of_edges() == 9,
)
flows = df(45, "edges")
check(
    "桑基注册流入流出守恒",
    flows.loc[flows.target == 2, "value"].sum()
    == flows.loc[flows.source == 2, "value"].sum()
    == 640,
)
freq = df(46, "frequency")
tokens = df(46, "tokens")
check(
    "词频与700个词元逐项相等",
    freq.set_index("词").频次.to_dict()
    == tokens.分词结果.value_counts().to_dict()
    and len(tokens) == 700,
)
raw = df(47, "counts")
normalized = df(47, "per_1000")
check(
    "词频使用全部词数分母",
    np.allclose(
        normalized[["代码", "原理", "步骤", "报错"]],
        raw[["代码", "原理", "步骤", "报错"]].div(
            raw.总词数, axis=0
        )
        * 1000,
    ),
)
raw48 = df(48)
check(
    "四象限标记可重算",
    ((raw48.字数 >= 200) & (raw48.情绪指数 < 0)).tolist()
    == raw48.优先复核.tolist(),
)
month = df(49, "monthly")
check(
    "低覆盖月份留空",
    month.loc[month.coverage < 0.8, "shown"].isna().all()
    and month.shown.isna().sum() == 2,
)
summary = df(50, "summary")
raw50 = df(50, "raw")
for _, r in summary.iterrows():
    samples = raw50.loc[raw50.组别 == r.组别, "耗时"]
    half = (
        t.ppf(0.975, len(samples) - 1)
        * samples.std(ddof=1)
        / np.sqrt(len(samples))
    )
    check(
        f"95%t区间重算-{r.组别}", np.isclose(half, r.halfwidth)
    )
check(
    "无重复数据表集合",
    len({tuple(e["tables"]) for e in mapping}) == 50,
)
report = {
    "version": "1.0.0",
    "date": "2026-09-13",
    "passed": True,
    "count": len(checks),
    "checks": checks,
}
(ROOT / "验收报告_v1.0.0.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(
    f"PASS {len(checks)} checks; 50 cases; 50 PNG + 50 SVG + 7 interactive HTML"
)
