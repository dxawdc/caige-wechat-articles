# 桑基图 弦图与流转可视化 配套资料

版本：v1.0.0；更新：2026-10-04；微信公众号：可以叫我才哥。

提供四张教学图的 PNG 和 SVG、四份模拟 CSV、绘图脚本、数据验收摘要，以及可离线打开的交互桑基图。

## 数据与口径

- 桑基图：1000 位访客，600 位注册，180 位付费，420 位注册未付费，400 位未注册。固定 7 日观察窗，每人一个归属渠道和最终结果。
- 弦图与关系矩阵：四部门、六对无向协作关系。每对协作计一次，关系总量 470，部门端点合计 940。
- 冲积图：500 位用户、六条完整路径。第 1 月轻度 300、重度 200；第 2 月轻度 180、重度 200、流失 120。
- 数据均为脚本中显式构造的教学示例。CSV 是这些常量的导出；替换为业务数据时，需要同时修改脚本对应函数中的输入与口径。

## 运行

使用 Python 3.10 或更高版本，安装中文字体，例如 Microsoft YaHei 或 Noto Sans CJK SC。

```bash
python -m pip install -r requirements.txt
python 绘制图表.py
```

脚本会生成配图、CSV、交互 HTML 和数据验收 JSON。交互 HTML 已内嵌 Plotly，可以下载后直接用浏览器打开。

静态流带由 Matplotlib 路径手工布局；弦图为对称无向矩阵，流带两端按同一数值分配弧长；冲积图逐条完整路径绘制。

## 官方参考

- [D3 Sankey](https://github.com/d3/d3-sankey)：标准布局适用范围和节点、连接结构。
- [D3 Chord](https://d3js.org/d3-chord/chord)：普通和有向弦图布局。
- [D3 Ribbons](https://d3js.org/d3-chord/ribbon)：普通与箭头流带。
- [Plotly Sankey](https://plotly.com/python/sankey-diagram/)：Python 接口示例。
- [RAWGraphs Alluvial](https://rawgraphs.github.io/learning/old-how-to-make-an-alluvial-diagram/)：同一组对象的分类组合解释。

## 物料

- `绘制图表.py`：复现入口。
- `requirements.txt`：依赖范围。
- `数据/`：边表、协作矩阵和完整路径表。
- `配图/`：四张 PNG 与四张 SVG。
- `交互桑基图.html`：可离线浏览的交互示例。
- `数据验收.json`：数据总量与比例核验结果。
- `物料清单.json`：文件字节数与 SHA-256 校验值。

查看完整来源后，可依据自己的单位、时间窗口和去重规则替换模拟输入，再生成图表。
