<!-- v1.0.0 | 2026-09-14 | 可复现实验资料 -->
# 从预测到分群：Python数据分析与挖掘五类模型

公众号：可以叫我才哥。文章作者：才哥AGI。

全部数据由固定随机种子生成，结果只用于教学，不代表真实用户或经营表现。这里提供源代码、四份模拟数据、预测明细、验证结果以及九张图的PNG/SVG；不包含未发布文章全文。

## 运行

在当前目录打开终端，建议使用Python 3.14独立环境（实际验证版本见outputs/environment_v1.0.0.json）。

```bash
python -m venv .venv
# Windows
.venv\Scripts\python -m pip install -r requirements_v1.0.0.txt
.venv\Scripts\python run_all_v1_0_0.py
.venv\Scripts\python validate_v1_0_0.py
# macOS/Linux使用 .venv/bin/python 替换以上Python路径
```

中文图需要系统安装Microsoft YaHei、Noto Sans CJK SC或SimHei等字体。环境没有中文字体时，请安装字体后重新绘制。

`run_all`会覆盖本资料目录下对应版本的模拟数据与运行输出，不应把真实数据放入这些演示文件。单独运行case脚本会读取已有data，不会重新生成输入。

## 文件与方法

| 文件 | 分析内容 |
| --- | --- |
| make_data_v1_0_0.py | 一次生成四份互相独立的模拟数据；流失数据有意供两种分类器共用 |
| case01_regression_v1_0_0.py | 多元线性回归与训练均值基线，750/250用户划分 |
| case02_logistic_v1_0_0.py | 1800/600/600用户划分，Pipeline标准化，验证集选错误成本阈值 |
| case03_tree_v1_0_0.py | 2400人开发集内部5折选深度，与逻辑回归共享600人测试集 |
| case04_kmeans_v1_0_0.py | RFM的log1p、标准化、K=2—6轮廓系数比较与原始单位画像 |
| case05_association_v1_0_0.py | 1680笔发现规则、720笔留出复核，Apriori仅挖掘至二项集 |
| common_v1_0_0.py | 中文绘图、输出路径和品牌标记 |
| validate_v1_0_0.py | 根据输出明细独立重算指标、核验交易分母与ID |

文章代码摘自 `ARTICLE_START/ARTICLE_END` 标记区间，是对应脚本main函数的核心步骤，需结合文件头导入与辅助函数。运行完整脚本即可复现图表，无需从文章拼接代码。

分类中churn_next14d=1表示未来14天没有访问；输入全部来自观察截止时刻及以前。单个用户一行，因此模拟实验使用随机划分。真实按时间重复采样的数据应使用时间/用户分组划分，不能直接照搬随机切分。

阈值的FP+4FN仅是假设的错误成本，不是挽留活动利润。聚类是当前用户快照的探索，不报告预测准确率；四种模拟人群本身就比较分离。关联规则的支持度分母包含全部交易；全0行表示仅购买范围外商品的订单。多件同款在篮子中仍只记True一次。

## 参考

[scikit-learn文档](https://scikit-learn.org/stable/)、[mlxtend Apriori](https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/apriori/)、[关联规则](https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/association_rules/)。依赖记录为本次实际运行版本；版本更新可能带来数值细微差异。
