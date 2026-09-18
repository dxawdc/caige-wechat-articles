# A 股热力树图 WorkBuddy Skill 版：公众号配套资料

对应公众号文章《在 WorkBuddy 里说一句话，生成 5000+ 只A股的热力树图》。

## 项目地址

<https://github.com/dxawdc/stock-heatmap>

本文核对的源码版本：`main` 分支提交 `70bcfed9c4b8b6c8d25534de1e94ceb2759329f8`（2026-09-18），Skill 位于仓库 `skill/` 目录。

## 文件清单

| 路径 | 说明 |
| --- | --- |
| `skill/SKILL.md` | Skill 说明文件（触发词 + 工作流），安装时以它为入口 |
| `skill/generate_heatmap.py` | 核心脚本：拉取行情 → 申万分组 → 生成树图数据 / 交互式 HTML |
| `skill/template.html` | 自包含 Plotly 前端模板（筛选器内嵌，实时切换） |
| `skill/implementation.md` | 实现知识沉淀（数据源、字段解析、分组逻辑、缓存策略） |
| `images/skill.jpg` | 文中图 1：Skill 版生成页面全貌（2026-09-18 23:20 闭市，5551 只，申万分组，总市值） |
| `demo/heatmap.html` | 演示文件：脚本 `--html` 模式的真实输出，下载后可直接用浏览器打开 |

演示 `demo/heatmap.html` 是 2026-09-18 闭市数据的真实导出，历史行情不保证后续仍然有效。项目基于公开行情数据源，供学习和研究使用，不构成投资建议。

## 安装 Skill（三种方式任选）

**方式一：WorkBuddy 对话发送仓库链接（推荐）**

> 帮我安装这个 skill：https://github.com/dxawdc/stock-heatmap

**方式二：技能管理从 Git 仓库导入**，选定仓库中的 `skill/` 目录。

**方式三：手动复制**

```bash
git clone --depth 1 https://github.com/dxawdc/stock-heatmap.git /tmp/sh
cp -r /tmp/sh/skill ~/.workbuddy/skills/a-share-heatmap
```

Windows 手动安装示例：

```powershell
git clone --depth 1 https://github.com/dxawdc/stock-heatmap.git "$env:TEMP\sh"
Copy-Item -Recurse "$env:TEMP\sh\skill" "$env:USERPROFILE\.workbuddy\skills\a-share-heatmap"
```

## 运行环境与使用

- Python 3.8+，依赖仅标准库加 `requests`（`pip install requests`）；不依赖 akshare / plotly / pandas，渲染由页面内 Plotly CDN 完成。
- 装好后，在 WorkBuddy 对话里说「生成A股热力图」即可触发；命令行直接运行：

```bash
# 交互式 HTML（筛选器内嵌页面，实时切换）
python generate_heatmap.py --html --out heatmap.html

# 传统 JSON 模式
python generate_heatmap.py --top-n 0 --group-by sw --size-by vol --out heatmap.json
```

- 筛选维度：`ST`（ST/*ST 股）、`KCB`（科创板）、`CYB`（创业板）、`BSE`（北交所）、`SH`（沪主板）、`SZ`（深主板）；`--include` 为并集、`--exclude` 为排除，可组合。
- 脚本运行时会在同级目录生成 `sector_map.json`（申万映射，24h 缓存）与 `trade_calendar.json`（交易日历，24h 缓存），均为自动生成，无需手工维护。

更多参数与实现细节见 `skill/SKILL.md` 与 `skill/implementation.md`。
