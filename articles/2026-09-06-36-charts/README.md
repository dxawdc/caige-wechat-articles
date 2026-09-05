# 36 种数据分析图表：Plotly 与 Matplotlib 对照

<!-- 版本：v1.1.0 | 更新时间：2026-09-06 | 状态：已完成本地语义和图片验收 -->

微信公众号「可以叫我才哥」同题文章的配套资料。所有数据均为固定种子 `20260906` 生成的教学模拟数据，不代表真实业务或投资表现。

- `代码/`：36 个独立绘图脚本，另附共用数据、样式和批量运行入口。
- `数据/`：7 份教学 CSV。
- `图表/`：72 张原始 PNG、36 个 Plotly HTML、36 份图形 JSON，以及离线所需的 `plotly.min.js`。
- `对照图/`：36 张组合图，每张上半部分是 Matplotlib，下半部分是 Plotly。
- `图表目录与口径_v1.0.0.json`：图表对应的问题、统计口径及两套实现。
- `验收/图表语义验收_v1.1.0.json`：198 项图形语义和本地组合图检查结果。

## 下载

[下载整库 ZIP](https://github.com/dxawdc/caige-wechat-articles/archive/refs/heads/main.zip)，解压后进入 `articles/2026-09-06-36-charts/`。

想看交互图，双击本目录内 `交互图目录_v1.1.0.html`。请保留 `图表/plotly.min.js`；GitHub 文件页面不直接执行 HTML，需要下载到本地打开。

## 运行

验证环境：Python 3.12.14。完整依赖固定在 `requirements_v1.0.0.txt`，安装前建议使用独立环境。

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements_v1.0.0.txt
.venv\Scripts\python "代码/运行全部图表_v1.0.0.py"
```

只画一种图：

```powershell
.venv\Scripts\python "代码/09_堆叠柱状图_v1.0.0.py"
```

macOS/Linux 将解释器路径改成 `.venv/bin/python`。中文字体需在本机安装微软雅黑或 Noto Sans CJK SC；其他字体可调整共用样式中的字体列表。

Plotly 静态图片通过 Kaleido 导出，需要 Chrome/Chromium。[官方静态导出说明](https://plotly.com/python/static-image-export/)。Windows 示例会自动尝试标准 Chrome 安装位置；其他环境按官方说明配置。

文章里的短代码省略了重复导入和造数，直接运行独立 `.py` 文件即可。代码、数据和绘图资产沿用原 v1.0.0 文件名，v1.1.0 增加图文核对和公开资料入口。
