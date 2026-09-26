# “9·24”之后，谁跑在前面？30个A股主题板块赛马图

公众号文章配套资料，版本 v1.0.0，数据截至 **2026年9月24日收盘**。从东方财富30个主题板块指数的日收盘点位出发，生成“9·24”以来、2026年初以来和滚动20个交易日三种视角的赛马图。

## 目录

| 路径 | 内容 |
| --- | --- |
| [data/板块清单.csv](data/板块清单.csv) | 小程序所用的30个东方财富主题板块及代码 |
| [data/原始日线](data/原始日线) | 逐板块保存的30份日线CSV |
| [data/交易日历.csv](data/交易日历.csv)、[data/行情.csv](data/行情.csv) | 交易日期参考表与校验后主表 |
| [prepare_data.py](prepare_data.py)、[phone_collect.py](phone_collect.py) | 网页行情采集、导入、检查和合并脚本 |
| [render_videos.py](render_videos.py)、[palette.py](palette.py) | 六段赛马视频的制作逻辑与配色 |
| [export_html.py](export_html.py)、[html_src](html_src) | 两份单文件交互网页的生成逻辑 |
| [A股板块轮动赛马图.html](A股板块轮动赛马图.html)、[动态坐标轴版](A股板块轮动赛马图_动态坐标轴.html) | 可下载后直接打开的交互成品 |
| [配图](配图)、[videos](videos) | 文章配图、视频预览图 |
| [validate_outputs.py](validate_outputs.py) | 视频和交互网页验收脚本 |

资料可从[独立ZIP](../../downloads/a-share-sector-race_v1.0.0.zip)一次下载。GitHub文件预览页不运行交互网页，下载HTML到本地后可直接打开。

## 数据与计算口径

- 板块日线来自[东方财富板块行情](https://quote.eastmoney.com/bk/90.BK1134.html)网页使用的历史K线接口，板块代码形如 `90.BK1134`，日K参数为 `klt=101`，不复权参数为 `fqt=0`。网页接口可能调整域名、字段和访问策略，重采时请核对响应。
- `data/行情.csv` 保存 `date,code,name,close` 四列，共30个板块、13,932条记录；参考交易日为488个。交易日列表从申万A指（801003）的日期列提取，仅用于连续性核验。
- “9·24”视角以2024年9月23日收盘为基准，包含9月24日当天涨跌；2026年初视角以2025年最后一个交易日收盘为基准。滚动20日视角每个交易日重新计算，以该窗口首日前一个交易日收盘为基准。
- 两个较晚收录的板块从2026年3月16日起有本次可用日线；早期排名依当时有值的板块计算。图中为板块指数涨跌幅，不代表板块内个股的平均收益。

## 运行

准备 Python 3.10+、NumPy、Matplotlib，以及命令行可用的 FFmpeg。本次成品在 Python 3.14.3、NumPy 2.5.3、Matplotlib 3.11.2、FFmpeg 9.0 环境制作。进入解压后的资料目录，依次运行：

```powershell
python -m pip install numpy matplotlib
python .\prepare_data.py --import-dir .\data\原始日线
python .\render_videos.py
python .\render_videos.py --axis-follow
python .\export_html.py
python .\export_html.py --axis-follow
python .\validate_outputs.py
```

视频为三种视角乘两种坐标轴的六段 1440×1300 MP4；两份HTML都可切换三种视角、暂停、调速和拖动日期。先查看短窗口效果可运行 `python .\render_videos.py --window 20d`。重新请求网页接口可运行 `python .\prepare_data.py --fetch`。更新数据截点时，同步调整 `prepare_data.py` 的 `AS_OF` 和交易日列表，再重新采集与验收。

2024年9月24日作为市场节点的背景，可参阅[国新办发布会记录](https://www.csrc.gov.cn/csrc/c106311/c7508374/content.shtml)与[新华社当周行情回顾](https://www.news.cn/20240927/c2676c277f2943a4a8d3e3c4965c36f4/c.html)。本资料用于复盘和可视化练习，历史排名不构成未来收益预测。
