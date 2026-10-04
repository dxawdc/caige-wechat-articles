# 桑基图 弦图 冲积图 制图教程配套资料

版本：v1.1.0；更新：2026-10-04；微信公众号：可以叫我才哥。

提供四份独立制图源码、共用样式和统一运行入口，配有四份模拟CSV、五张PNG与SVG、两个可离线打开的交互HTML。

## 运行

使用Python 3.10及以上版本，先安装Microsoft YaHei或Noto Sans CJK SC中文字体。

```bash
python -m pip install -r requirements.txt
python 绘制图表.py
```

入口会依次执行四份示例，并生成四种图的效果总览。单独制图时，运行对应文件：

```bash
python 01_桑基图.py
python 02_弦图.py
python 03_冲积图.py
python 04_关系矩阵.py
```

Plotly使用Kaleido导出PNG、SVG；Kaleido 1.x需要可用的Chrome。已有Chrome时直接运行；需要安装导出用Chrome时，可执行 `plotly_get_chrome`。交互HTML已经内嵌Plotly，下载后可离线打开。

## 四份示例怎样实现

| 源码 | 输入 | 核心接口 |
| --- | --- | --- |
| 01_桑基图.py | 起点、终点、数量的边表 | Plotly go.Sankey |
| 02_弦图.py | 部门协作的对称矩阵 | pyCirclize Circos.chord_diagram |
| 03_冲积图.py | 六条完整路径及各路径人数 | Plotly go.Parcats，按观察时间排列分类列 |
| 04_关系矩阵.py | 同一份部门协作矩阵 | Matplotlib imshow和text |

`图表工具.py`负责共用字体、配色、标题、品牌和导出；`绘制图表.py`负责批量执行、总览图和数据一致性检查。示例实际读取CSV，替换数据后可重新生成。

## 模拟数据与口径

- 桑基图：1000位访客，600位注册，180位付费，420位注册未付费，400位未注册。固定7日观察窗，每人一个归属渠道和最终结果。
- 弦图：四部门、六对无向协作关系。关系总量470，端点合计940。代码取矩阵上三角，避免把同一无向关系重复绘制。
- 冲积图：500位用户、六条完整路径。第1月轻度300、重度200；第2月轻度180、重度200、流失120。counts是路径人数，颜色固定按进入批次编码。
- 矩阵图：保留完整对称矩阵显示，数值范围固定为0至120。

CSV由教学场景显式构造，均为模拟数据。部门协作边表额外提供了相同关系的起终点表示，便于转换为其他网络布局。

## 官方参考

- [Plotly Sankey](https://plotly.com/python/sankey-diagram/)
- [pyCirclize Chord Diagram](https://moshi4.github.io/pyCirclize/chord_diagram/)
- [Plotly Parcats](https://plotly.com/python/reference/parcats/)
- [Matplotlib Heatmap](https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html)
- [Plotly静态导出](https://plotly.com/python/static-image-export/)

## 版本与文件

v1.1.0增加四份独立源码与共用样式，改用原生绘图库接口生成对应图，增加开头效果总览与冲积图交互HTML。

`配图/`提供PNG和SVG，`数据/`提供CSV，`数据验收.json`记录教学数据核验，`物料清单.json`列出文件字节数与SHA-256。
