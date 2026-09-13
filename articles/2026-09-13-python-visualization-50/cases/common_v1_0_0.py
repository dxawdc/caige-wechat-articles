"""v1.0.0 | 才哥AGI | 2026-09-13 | 统一导出与中文字体。"""

from pathlib import Path
import os, json
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
FONT = None
for name in [
    "Microsoft YaHei",
    "Noto Sans CJK SC",
    "SimHei",
    "PingFang SC",
]:
    try:
        FONT = font_manager.findfont(
            name, fallback_to_default=False
        )
        break
    except ValueError:
        pass
if FONT is None:
    raise RuntimeError(
        "请安装 Noto Sans CJK SC 中文字体后重新运行。"
    )
FONT_NAME = font_manager.FontProperties(fname=FONT).get_name()
COLORS = [
    "#188568",
    "#4878B7",
    "#E59B42",
    "#9566AA",
    "#CB6677",
    "#5D9FAD",
]
sns.set_theme(style="whitegrid", font=FONT_NAME, palette=COLORS)
plt.rcParams.update(
    {
        "axes.unicode_minus": False,
        "font.size": 12,
        "axes.titlesize": 16,
        "axes.labelsize": 12,
        "figure.dpi": 150,
        "savefig.dpi": 170,
        "svg.fonttype": "path",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)
(
    os.environ.setdefault(
        "BROWSER_PATH",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )
    if os.name == "nt"
    else None
)


def start(n, title, size=(8, 5), **kwargs):
    rng = np.random.default_rng(20260913 + n)
    fig, ax = plt.subplots(figsize=size, **kwargs)
    return rng, fig, ax


def finish(n, title, fig, df, metrics=None):
    stem = f"{n:02d}_v1.0.0"
    if not isinstance(df, dict):
        df = {"data": df}
    tables = []
    for key, table in df.items():
        filename = f"{stem}_{key}.csv"
        table.to_csv(
            OUT / filename,
            index=False,
            encoding="utf-8-sig",
            float_format="%.9g",
        )
        tables.append(filename)
    if hasattr(fig, "write_image"):
        fig.update_layout(
            template="plotly_white",
            width=1000,
            height=650,
            title=dict(text=f"{n:02d} · {title}", x=0.04),
            font=dict(family=FONT_NAME, size=18),
            colorway=COLORS,
            margin=dict(t=110, b=90, l=75, r=65),
        )
        fig.add_annotation(
            text="模拟数据 · 才哥AGI · v1.0.0",
            x=0,
            y=-0.13,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color="#64746C"),
        )
        fig.write_html(
            OUT / f"{stem}.html",
            include_plotlyjs="directory",
            auto_open=False,
        )
        fig.write_image(OUT / f"{stem}.png", scale=1.6)
        fig.write_image(OUT / f"{stem}.svg")
    else:
        fig.suptitle(
            f"{n:02d} · {title}",
            x=0.08,
            ha="left",
            fontweight="bold",
            color="#1C493A",
        )
        fig.text(
            0.08,
            0.012,
            "模拟数据 · 才哥AGI · v1.0.0",
            fontsize=9,
            color="#64746C",
        )
        fig.tight_layout(rect=(0, 0.04, 1, 0.94))
        fig.savefig(OUT / f"{stem}.png")
        fig.savefig(OUT / f"{stem}.svg")
        plt.close(fig)
    record = dict(
        case=n,
        title=title,
        seed=20260913 + n,
        synthetic=True,
        tables=tables,
        metrics=metrics or {},
    )
    (OUT / f"{stem}_metrics.json").write_text(
        json.dumps(
            record,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
            default=lambda v: v.item(),
        ),
        encoding="utf-8",
    )
    print(f"PASS {n:02d} {title}", flush=True)
