# Python爬虫与游戏玩家评价文本分析

版本：v1.0.0。日期：2026-09-14。状态：完成代码运行与分析自检。

本资料由公众号「可以叫我才哥」制作，面向《王者万象棋》的TapTap公开评价。包含真实采集代码、星级与玩家状态分析、主题词典、TF-IDF/NMF主题探索和Matplotlib图表。不是上一期模拟数据模型包。

## 本次数据范围

北京时间2026-09-14 21:54—22:00，沿公开默认列表最新排序读取215页至next_page为空，返回2,144条记录，按评价ID去重后2,142条。记录最早版本时间2022-11-12，最新2026-09-14 21:50。

此范围不是平台全量评价：初探页面计数约3,673，默认接口total约2,144，且存在另外的折叠列表。动态排序可能遗漏或重复。本次不访问登录资料、不处理验证码、不绕过访问验证。

状态为“玩过”1,172条、“期待”959条、未展示11条。只有244条有评价时游玩时长；TapTap账号等级不可用。徽章level不是账号等级，“期待”和缺少时长也不能等同于真实未玩过。

本包仅分享汇总数据；原始正文、用户标识和完整网页保留在采集者本地。你自行采集的数据也请保存在private目录，不提交公共仓库。

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

重新采集会产生新快照，结果未必与本包相同。新一轮请新建版本目录，保留旧输出；脚本不会替你重写已发表文章。示例固定分析首发前7天至采集时刻；如果以后延长观察，应同步修改period分段及图表标题，不能继续把很久后的数据标成“第5天未完整”。

## 采集策略

从公开HTML的Nuxt数据中提取网页实际请求，单线程每页最多10条，至少间隔1.2秒，跟随next_page，页级缓存、检查点及响应哈希。仅重试部分5xx及网络超时，401/403/429、JSON失败或验证页面停止。X-UA来自公开页面客户端参数，不是复制用户登录凭据。接口不是长期稳定的开放API，结构变化须重新检查。

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

版本说明：首次交付2142条公开默认列表评价的采集与分析案例；不含折叠列表、原始评论全文、账号等级或历史编辑版本。
