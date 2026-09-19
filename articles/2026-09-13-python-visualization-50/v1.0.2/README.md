# Python数据可视化指南：50例配套资料

版本：v1.0.2｜更新时间：2026-09-13｜状态：可运行的原创示例物料｜作者：才哥AGI

50份独立Python脚本，模拟数据、PNG/SVG与指标记录。7个Plotly案例另含交互HTML。图形任务参考蓝星宇《数据可视化设计指南：从数据到新知》。

## 运行

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements_v1.0.0.txt
.venv\Scripts\python run_all_v1_0_2.py
```

macOS/Linux请替换为.venv/bin/python。只运行03与45：python run_all_v1_0_2.py 3 45。单例也可直接python cases/case_03_v1_0_2.py。公共模块在cases/common_v1_0_2.py。

需要中文系统字体（Microsoft YaHei、Noto Sans CJK SC、SimHei或PingFang SC）。不分发商业字体。Kaleido静态导出需要Chrome，可用BROWSER_PATH指定可执行文件；Windows默认检查标准Chrome路径，其他系统由Kaleido查找。

## 查看结果

打开图表索引_v1.0.2.html，可搜索图形与工具并查看50张图、源码及CSV。Plotly交互文件与outputs/plotly.min.js须保留在同一目录，可以离线查看；请遵循该第三方文件自身许可证。CSV为UTF-8 BOM，方便Excel读取。SVG中文字转为路径的图可在缺少中文字体的阅读端正常显示。

每个案例使用独立种子或明确数表。改变运行顺序不改变数据。PNG/SVG可能因系统字体、浏览器版本产生微小排版差异，数值应保持一致。

## 数据说明

全部数据为模拟，案例结论只说明模拟结构。代码不连接外部业务API，只读取本目录内的模拟数据。薪酬、收入、用户、价格、情绪等不代表现实机构或个人；本例没有真实情绪模型、真实市场价格和真实地理观测。

运行脚本包含关键数值断言；validate_v1_0_2.py独立核对全部产物、数据分母与字段约束。完整清单及SHA256见manifest_v1.0.2.json。

下载地址：https://github.com/dxawdc/caige-wechat-articles/raw/refs/heads/main/downloads/python-visualization-50_v1.0.2.zip

## 版本说明

v1.0.2：图内标识统一为“可以叫我才哥”；文章正文/代码/标题设为15/11/17px，精简参考说明并去除顶部空白。数据与计算逻辑不变。

来源页码和图号见[案例来源映射](案例来源映射_v1.0.0.md)，与当前50例对应。

[返回资料库](https://github.com/dxawdc/caige-wechat-articles) · [维护与更新规则](https://github.com/dxawdc/caige-wechat-articles/blob/main/CONTRIBUTING.md)
