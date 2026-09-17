# A 股实时热力树图：公众号配套资料

对应公众号文章《把5000+只A股塞进一张图：这个实时热力树图是怎样做出来的》。

## 项目地址

<https://github.com/dxawdc/stock-heatmap>

本文核对的源码版本：`main` 分支提交 `26a37775e60f5e3eebe1eccde1a57659db332563`（2026-06-22）。

## 文件清单

| 路径 | 说明 |
| --- | --- |
| `代码片段.json` | 文中使用的 JavaScript、Python 与启动命令节选；每段保留实际语言标记 |
| `images/plotly.png` | Plotly 渲染器导出图（2026-09-17 22:02 闭市，全部 5553 只，按申万一级行业分组，总市值） |
| `images/echarts.png` | ECharts 渲染器导出图（2026-09-17 22:02 闭市，全部 5553 只，按申万一级行业分组，总市值） |

截图由项目在 2026-09-17 22:02 闭市后导出，用于说明界面功能；历史行情不保证后续仍然有效。项目基于公开行情数据源，供学习和研究使用，不构成投资建议。

## 使用方式

项目的运行与安装步骤请以原项目 README 为准：

```bash
git clone https://github.com/dxawdc/stock-heatmap.git
cd stock-heatmap/web
pip install -r requirements.txt
python app.py
```

浏览器插件版则在 Chrome 或 Edge 的扩展管理页开启开发者模式，加载原项目中的 `extension/` 目录。
