# 数据分析与可视化 Skill 实测：公众号配套资料

对应公众号文章《我做了一个数据分析与可视化 Skill：从数据体检到出图洞察的完整流程》。

本目录是该 skill 的完整规则、脚本与七套模拟数据的实测物料。skill 整合了两部分来源：《数据可视化设计指南：从数据到新知》（蓝星宇）中的可视化设计原则，以及游戏数据分析方法体系（指标口径、恒等式拆解、决策报告结构）。

## 文件清单

| 路径 | 说明 |
| --- | --- |
| `skill/SKILL.md` | Skill 入口：七步工作流（接收对齐 → 体检清洗 → 统计特征 → 关键指标 → 图表匹配 → 可视化设计 → 洞察交付） |
| `skill/references/` | 六份方法参考 + 一份来源合成说明（清洗阶梯、统计特征、指标四层、图表匹配、设计四维原则、洞察摘要模板） |
| `skill/scripts/profile_data.py` | 数据体检脚本：规模/类型/缺失/重复/异常/粒度，输出 JSON + Markdown 报告 |
| `skill/scripts/suggest_chart.py` | 选图建议脚本：按分析意图 + 字段类型 + 数据规模推荐图型 |
| `skill/scripts/viz_style.py` | matplotlib 统一样式（中文字体、配色、图注、导出） |
| `demo/数据模拟.py` | 生成七套模拟数据（固定随机种子 20260919，可复现） |
| `demo/数据分析.py` | 完整实测脚本：清洗 → 统计特征 → 生成文中 8 张图 |
| `demo/洞察摘要.md` | 按 skill 交付模板产出的数据洞察摘要 |
| `demo/reports/` | 七套数据的体检报告与统计特征汇总 |
| `data/` | 演示数据（CSV，模拟生成，无业务含义） |
| `images/` | 文中图 1—图 8（PNG，可直接预览） |

## 数据说明

- 全部数据为程序模拟，随机种子固定为 `20260919`，运行 `demo/数据模拟.py` 可完整复现；
- `data/raw/` 未包含 `05_订单流水.csv`（约 13 MB），同样由 `demo/数据模拟.py` 一键生成；
- 目录结构即 `demo/数据分析.py` 期望的布局（`skill/`、`demo/`、`data/raw/` 平级），clone 后无需改路径即可复现：先跑 `数据模拟.py` 补齐缺失数据与 `data/raw/`，再跑 `数据分析.py`；
- 模拟数据中故意埋入了常见质量问题用于演示：重复行、渠道名同义异写、收入单位混用、缺失值、毫秒误记为秒——可对照体检报告观察 skill 的识别与处理方式。

## 运行环境与使用

- Python 3.10+，依赖：`pandas`、`numpy`、`matplotlib`（`pip install pandas numpy matplotlib`）。
- 复现实测：

```bash
python demo/数据模拟.py     # 生成七套模拟数据到 data/raw/
python demo/数据分析.py     # 清洗 + 统计 + 生成 8 张图（输出到 配图/ 与 输出/）
python skill/scripts/profile_data.py 你的数据.csv --out 体检报告
python skill/scripts/suggest_chart.py --intent compare --dim-unique 31 --label-len long
```

- 在 WorkBuddy 中安装：将 `skill/` 目录复制到 `~/.workbuddy/skills/data-analysis-viz/`，之后在对话里直接给出数据文件并提出分析需求即可触发。

## 局限

- 所有数值均为模拟生成，不构成任何行业结论；
- skill 覆盖静态图表，交互式可视化与实时看板不在范围内；
- 设计原则部分整理自 2023 年出版的《数据可视化设计指南：从数据到新知》，具体工具行为以官方文档为准。

仅供学习交流。
