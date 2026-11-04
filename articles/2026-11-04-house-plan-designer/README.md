# 户型图 → 装修设计器：识图实测与对账数据

配套文章《1.7 秒量完 19 面墙，但它只读懂了半个户型图》。

这里放的是这次实测的原始数据和脚本：开源项目 [house-plan-designer](https://github.com/ZWD11/house-plan-designer)（MIT）自带一张酷家乐户型图和一份人工校对的户型描述，本文用这两样东西对识图结果做了逐墙对账。

## 提供什么

| 目录 / 文件 | 内容 |
| --- | --- |
| `数据/example-spec.json` | 作者给的户型描述（HouseSpec），21 面墙、8 个房间、37 件家具，作为对账的标准答案 |
| `数据/draft.json` | `analyze.py` 对示例户型图自动识别出的草稿：19 面墙，无房间、无门窗 |
| `数据/analysis.json` | 识图过程数据（比例、尺寸线刻度、外轮廓） |
| `对比墙体偏差.py` | 把草稿墙体逐点对到标准答案，输出中位/P90/P99/超差比例 |
| `图/` | 识图标号图、草稿生成结果、完整成品 2D 与 3D、叠图对账、水电点位图 |
| `配图/` | 文章封面的横版（1800×766）与方版（1200×1200），含可编辑 SVG |

## 怎么跑

先按 upstream 仓库说明装好技能本体（Python 依赖与 `scripts/` 下的 npm 依赖），再执行：

```bash
# 1. 识图，得到草稿（draft 目录内会生成 draft.json 与 analysis.png）
python <skill>/scripts/analyze.py 示例户型图.jpg \
  --total-width 12340 --total-height 11940 --out 数据/识图

# 2. 把草稿与标准答案逐墙对账
python 对比墙体偏差.py 数据/draft.json 数据/example-spec.json

# 3. 用标准答案生成设计器页面，跑自查
python <skill>/scripts/build.py 数据/example-spec.json -o 设计器.html
node <skill>/scripts/check.mjs 设计器.html check
```

第 2 步的期望输出：

```json
{"samples": 399, "median_mm": 5.0, "p90_mm": 10.0,
 "share_within_10mm": 93.5, "max_mm": 712.3}
```

## 数据从哪来

户型图、`example-spec.json`、识图脚本与验收脚本都来自 upstream 仓库 `ZWD11/house-plan-designer`，示例户型为 108.25 平方米三室两卫，图面标注总宽 12340、总深 11940 毫米。

对账口径：沿草稿每面墙等距取 21 个点，逐点计算到最近一条标准墙中线的距离，共 399 个采样点。门窗洞会让墙断开，所以只比距离，不比墙数。

## 依赖

```
numpy
pillow
opencv-python
pymupdf
ezdxf
pypdf
```

Node 侧只需 `puppeteer-core`（在技能的 `scripts/` 目录下 `npm install`），浏览器使用本机 Chrome / Edge。
