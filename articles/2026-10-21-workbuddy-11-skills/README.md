# WorkBuddy 好用的 11 个技能

WorkBuddy 官方文档「零成本 Skill 精选」中的 9 个免费技能，加上 GitHub 上 2 个去 AI 味的写作技能。按“先装 3 个管家、再串成一条内容流水线”的顺序整理。

## 提供的物料

配套资料文件夹里是技能清单：

- WorkBuddy好用技能11个.xlsx：编号、技能、安装名、分组、流水线步骤、来源、用途、可复制的说法、注意事项和地址。
- WorkBuddy好用技能11个.md：同样内容的 Markdown 版，每条说法放在独立代码块里，便于复制。

其他文件：

- 技能清单.json：11 个技能的数据源，以上两种格式都由它生成。
- 3 张示意图（技能总览、安装顺序、内容流水线）与横版、方版封面：PNG 阅读版和可编辑 SVG。
- 生成配套资料.py、生成配图.py：重新生成清单与配图的源码。

## 怎么用

先装 find-skills、skill-scanner、self-improvement 三个技能；之后安装其他技能前，先用 skill-scanner 检查。把技能名称或 GitHub 地址发给 WorkBuddy，让它帮你安装，装好后做一件小事试试。

## 重新生成

使用 Python 3，依赖 openpyxl 和 Pillow。修改 技能清单.json 后运行：

```shell
python -m pip install -r requirements.txt
python 生成配套资料.py
python 生成配图.py --font "C:/Windows/Fonts/msyh.ttc"
```

## 来源

前 9 个技能的说明来自 WorkBuddy 官方文档：https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/Find-Skills ；Humanizer-zh 来自 https://github.com/op7418/Humanizer-zh ，写作蒸馏器来自 https://github.com/larashero3-dotcom/writing-dna-skill 。界面名称和版本以你使用的为准。

更新日期：2026-10-21。版本：1.0.0。
