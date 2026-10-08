# 《高性价比人生指南》数据与可视化

配套文章：《高性价比人生指南》火了：它到底教人怎么过日子？

提供34节、672条建议的数据表、8张内容图表、封面与可编辑SVG，以及解析和绘图脚本。

## 数据来源

原项目：https://github.com/eternity4719/HowToLiveBetter

2026-10-08正文快照，提交a18ee40；原作者eternity4719，指南正文采用CC BY 4.0许可。条目分档沿用原作者标签与检索规则，解读时结合完整原文中的适用条件。数据表保留来源统计与可追溯条目编号。

## 使用

```bash
git clone https://github.com/eternity4719/HowToLiveBetter.git hltb
git -C hltb checkout a18ee40
pip install pandas numpy matplotlib pillow
python 分析数据.py hltb
python 生成图表.py
python 生成封面.py
```

图表脚本使用Windows的微软雅黑、Noto Sans SC字体；封面模板使用本机Chrome渲染，其他环境可调整脚本中的字体与浏览器路径。

## 物料

- 数据：条目、章节统计、来源域名、来源分类及统计JSON。
- 配图：18条精选、总览、条目结构、资源华夫图、成本漏斗、章节证据、证据与争议、来源构成；附首尾品牌动图。
- 封面：横版、方版AI插画，SVG几何模板及PNG，最终提示词。
- 源码：解析数据、生成图表、生成封面三个脚本。
- 下载包：本目录最新物料的ZIP，文件清单列于物料清单.json。
