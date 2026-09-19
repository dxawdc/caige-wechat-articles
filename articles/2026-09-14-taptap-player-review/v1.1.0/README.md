# Python爬虫与游戏玩家评价文本分析

版本：v1.1.0｜资料整理：2026-09-15｜状态：采集、基础分析与语境标注的完整使用说明。

本资料由公众号「可以叫我才哥」制作，面向《王者万象棋》的TapTap公开评价。包含真实采集代码、星级与玩家状态分析、主题词典、TF-IDF/NMF主题探索和Matplotlib图表。全部12张分析图可从公开汇总资料重绘。

## 本次数据范围

北京时间2026-09-14 21:54—22:00，沿公开默认列表最新排序读取215页至next_page为空，返回2,144条记录，按评价ID去重后2,142条。记录最早版本时间2022-11-12，最新2026-09-14 21:50。

此范围不是平台全量评价：初探页面计数约3,673，默认接口total约2,144，且存在另外的折叠列表。动态排序可能遗漏或重复。本次不访问登录资料、不处理验证码、不绕过访问验证。

状态为“玩过”1,172条、“期待”959条、未展示11条。只有244条有评价时游玩时长；TapTap账号等级不可用。徽章level不是账号等级，“期待”和缺少时长也不能等同于真实未玩过。

采集到的原始页面、正文与用户标识请放在 `private/` 目录（已在 `.gitignore` 中），与汇总结果分开管理。

## 安装与直接复现图表

实际环境：Windows，Python3.14，详见requirements和environment文件。Python其他版本未在本次验证；部分固定依赖版本可能要求较新Python。

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements_v1.0.0.txt
.venv\Scripts\python plot_v1_0_0.py
.venv\Scripts\python validate_v1_0_0.py
```

作图仅使用outputs内的汇总JSON，不需要原始评价，可以复现本次图表数值。图表默认微软雅黑；其他系统请安装中文字体并在plot脚本中替换font.sans-serif。PNG/SVG已经随包提供。

## 重新采集与分析

在资料目录运行以下命令。默认python指向你安装好依赖的虚拟环境。

```bash
python crawl_v1_0_0.py --output private/raw_v1.0.0
python prepare_v1_0_0.py --raw private/raw_v1.0.0 --output private/clean_v1.0.0
python analyze_v1_0_0.py --input private/clean_v1.0.0/reviews_private_v1.0.0.csv --output outputs --private-output private/analysis_v1.0.0
```

分析脚本会将同一轮清洗生成的collection_summary_v1.0.0.json复制到outputs，确保图表与汇总计数来自同一个快照。然后作图和复核：

```bash
python plot_v1_0_0.py
python validate_v1_0_0.py --private-csv private/clean_v1.0.0/reviews_private_v1.0.0.csv
python article_walkthrough_v1_0_0.py private/clean_v1.0.0/reviews_private_v1.0.0.csv
```

重新采集会产生新快照，结果未必与本包相同。新一轮先在临时目录完成采集与核验，再更新当前物料；原始快照按研究需要另行管理，不在文章目录堆叠整包版本。脚本不会替你重写已发表文章。示例固定分析首发前7天至采集时刻；如果以后延长观察，应同步修改period分段及图表标题，不能继续把很久后的数据标成“第5天未完整”。

## 采集策略

从公开HTML的Nuxt数据中提取网页实际请求，单线程每页最多10条，至少间隔1.2秒，跟随next_page，页级缓存、检查点及响应哈希。仅重试部分5xx及网络超时，401/403/429、JSON失败或验证页面停止。X-UA来自公开页面客户端参数。接口不是长期稳定的开放API，结构变化须重新检查。

## 分析口径

- 4—5星为本文高星，3星为中星，1—2星为低星；不是平台官方评分或情绪概率。
- 版本时间为max(created_time,edited_time)，时区Asia/Shanghai。主分析是当前幸存可见版本，不能重建历史全貌。
- 开服点为2026-09-10 07:00，依据官方公告。96小时前后窗口均左闭右开。
- 全样本星级与词典统计保留不同账号完全同文评价，另做同文去重敏感性分析；TF-IDF/NMF对同文去重。
- 主题词典多标签，一条评价对同主题计一次。没有命中不代表中性；命中也不是投诉或方面负面。
- TF-IDF/NMF仅使用开服前7天到快照的近首发文本。共同词表，min_df=5，max_df=.8，最多4000特征，sublinear_tf及默认L2归一化；零向量不参与主题归组。
- NMF探索6主题，nndsvda，random_state42，最大800轮。数量是最大权重归组，不是玩家群体或概率。
- Wilson区间仅表达二项模型下的计数不确定性，不能修正公开评论的选择偏差。

## 自检与限制

validation文件记录计数、分母、主题歧义回归案例，以及本地原始清洗表复算结果。文章代码已实际运行；所有图表进行了视觉检查。此前按每主题5条的50个命中项做开发性试读，修正“英雄联动”“平衡优化”“站位优化”等歧义，不把该试读当独立准确率测试。

本例没有训练并验证游戏方面情感分类器，不提供文本分类准确率，也不识别评价真假。某些主题中的竞品比较和语境歧义仍需人工回读。分析结论不能自动推出产品机制事实或因果效果。

## 官方与项目来源

- 评价页：https://www.taptap.cn/app/243110/review
- 官方开服公告：https://www.taptap.cn/moment/846472707175353375
- jieba：https://github.com/fxsjy/jieba
- 文本特征：https://scikit-learn.org/stable/modules/feature_extraction.html
- NMF：https://scikit-learn.org/stable/modules/decomposition.html

## 语境标注与高低星主题分析

安装原有requirements_v1.0.0.txt后，在本目录运行：

```bash
python aspect_analysis_v1_1_0.py
python plot_aspects_v1_1_0.py
```

若手上有对应时段的评价快照 CSV，可以加 `--private-csv PATH` 核对全量提及计数。新抓取数据随时间变化，不能期待得到同样数字。

## 两个层次不能混用

全量主题提及：高星1107条、低星776条，十类词典，分母分别取各组评价数。它不表示方面的正负态度。

语境样本：原快照全时段，高低星各随机40条，pandas原始行序、sample(n=40, random_state=20260914)。由Codex完整语境阅读，标出praise与criticism，允许混合态度，泛泛评价/预约提问不赋具体方面。只表达未来期待、不指向本产品的评价不计为当前产品明确方面态度。没有独立人工复核，不是分类器准确率测试，不将样本占比外推给平台全体玩家。

界面功能、IP定位、运营响应为语境新增分类；商业化观感含主观商业动机，不与词典商业化付费等同。解锁造成入门障碍计入新手引导，奖励领取与账号绑定计入福利任务，教程长计入新手而非强行推断单局长。仅看演示的音画评价不被视为玩过。玩家关于抄袭、控胜率等指控仅作为观点，未被验证为事实。

## 语境分析物料

`outputs/aspect_annotations_v1.1.0.json`：80条匿名编号、评分、双向方面标签与简短转述。代码只统计已有标签，不自动分类新文本。

`outputs/aspect_summary_v1.1.0.json`：分组汇总与标注边界。

`outputs/rating_theme_mentions_v1.1.0.json`：全量高低星各自的主题计数与分母。

`aspect_analysis_v1_1_0.py`：计数与一致性校验；`plot_aspects_v1_1_0.py`：3张新图的PNG与SVG生成。

标签到结果的过程可在本包内复算；语义判断本身的准确性无法只凭本包独立复核。

当前目录只保留最新完整一套。

## 独立资料包

[仅下载本篇 ZIP](https://raw.githubusercontent.com/dxawdc/caige-wechat-articles/main/downloads/taptap-player-review_v1.1.0.zip)。解压后进入 `taptap-player-review_v1.1.0/`，按本页运行步骤使用。

[返回资料库](https://github.com/dxawdc/caige-wechat-articles) · [维护与更新规则](https://github.com/dxawdc/caige-wechat-articles/blob/main/CONTRIBUTING.md)
