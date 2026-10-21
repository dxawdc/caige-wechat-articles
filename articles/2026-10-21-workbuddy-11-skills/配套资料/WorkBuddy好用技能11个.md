# WorkBuddy 好用的 11 个技能

版本 1.0.0 · 更新 2026-10-21

前 9 个来自 WorkBuddy 官方文档「零成本 Skill 精选」（来源 SkillHub），后 2 个是 GitHub 上公开的社区技能；说明按官方文档和仓库 SKILL.md 整理，非逐个实测。

## 01｜Find Skills（find-skills）

分组：管家 · 来源：SkillHub

说出想做的事，它从技能里找出候选，并比较区别。

怎么说：

```text
我想把网页里的表格抓下来存成 Excel。帮我找 2 到 3 个合适的技能，比较各自的用途、来源和需要的权限，先别安装。
```

注意：推荐结果可能是还没装的技能，装之前先过一遍 Skill Scanner。

https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/Find-Skills

## 02｜Skill Scanner（skill-scanner）

分组：管家 · 来源：SkillHub

安装第三方技能前做安全检查，看依赖、脚本和硬编码配置有没有可疑之处。

怎么说：

```text
安装前先用 skill-scanner 检查这个技能：【技能链接】。列出它会读写哪些目录、会不会联网、依赖了什么，有风险的地方标出来，等我确认再装。
```

注意：它能降低风险，不能保证零风险；来源不明的技能，检查结果再好也要谨慎。

https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/Skill-Scanner

## 03｜self-improvement（self-improvement）

分组：管家 · 来源：SkillHub

记下你纠正过的偏好、任务失败的原因，下次同类任务少犯同样的错。

怎么说：

```text
记一下：以后整理表格时，金额保留两位小数，日期统一写成 YYYY-MM-DD，不要合并单元格。
```

注意：官方说法是“可能”沿用，不是每次都一定生效；纠正时说得越明确越好。

https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/self-improvement

## 04｜tl_video_downloader（tl_video_downloader）

分组：流水线 · 流水线：拿素材 · 来源：SkillHub

下载视频、音频或字幕，交给后面的步骤整理。

怎么说：

```text
帮我下载这个视频的字幕和音频：【视频链接】，存到当前工作空间的「素材」文件夹，先不用下载视频本身。
```

注意：遵守平台规则和版权，只用于个人学习和研究。

https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/tl_video_downloader

## 05｜Local Whisper（local-whisper）

分组：流水线 · 流水线：转文字 · 来源：SkillHub

在本地把录音转成文字，模型下载好以后可以离线用。

怎么说：

```text
用 local-whisper 把「素材」里的音频转成文字，按时间分段，保存成 txt。听不清的地方标「？」，不要自己猜。
```

注意：第一次要先下载模型；录音越清楚，转出来越准。

https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/Local-Whisper

## 06｜Web Search（web-search）

分组：流水线 · 流水线：补资料 · 来源：SkillHub

先联网搜索再回答，问“最近、最新”的事不容易用到过时信息。

怎么说：

```text
课里提到的【工具或概念】，帮我搜一下最近 3 个月有没有新版本或变化，列出要点并附上来源链接和日期。
```

注意：提问时带上时间范围，并要求附来源，方便核对。

https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/Web-Search

## 07｜Agent Browser（agent-browser）

分组：流水线 · 流水线：看网页 · 来源：SkillHub

打开网页做滚动、点击、展开和截图，适合要点开才看得到内容的页面。

怎么说：

```text
打开【官方文档链接】，把需要展开和滚动才能看到的内容读完，整理成摘要，关键页面截图存到「素材」文件夹。
```

注意：遇到登录、验证码或付款页面就停下来交给自己处理。

https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/Agent-Browser

## 08｜Obsidian（obsidian）

分组：流水线 · 流水线：存笔记 · 来源：SkillHub

直接读写、搜索本地的 Obsidian 笔记库。

怎么说：

```text
把上面的转写稿、补充资料和截图整理成一篇 Obsidian 笔记，放进「课程笔记」目录：知识框架、重点概念、可以马上用的做法、原始链接。
```

注意：先在笔记库里规划好目录，比如日报、项目、课程笔记。

https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/Obsidian

## 09｜写作蒸馏器（writing-dna-skill）

分组：流水线 · 流水线：定文风 · 来源：GitHub

读你过去写的文章，整理出一份写作风格规则（Writing-DNA.md），以后写作时照着用。

怎么说：

```text
用 writing-dna-skill 分析「我的文章」文件夹里的 20 篇文章，生成我的 Writing-DNA.md。只分析我自己写的文章。
```

注意：至少要 20 篇完整文章；只用于分析自己或已获授权的文章，不要拿来冒充别人。

https://github.com/larashero3-dotcom/writing-dna-skill

## 10｜Humanizer-zh（humanizer-zh）

分组：流水线 · 流水线：去 AI 味 · 来源：GitHub

按 31 类常见问题修改空话、重复和模板化表达，保留事实和作者语气。

怎么说：

```text
用 humanizer-zh 润色这篇初稿，只改表达，不增加数据和经历，代码、链接和标题保持原样。改完列出主要改了哪几类问题。
```

注意：它只改表达，不核对事实，也不保证通过 AI 检测；先把内容写对，再谈像不像人写的。

https://github.com/op7418/Humanizer-zh

## 11｜Frontend Design（frontend-design）

分组：流水线 · 流水线：做成页面 · 来源：SkillHub

做网页时兼顾视觉设计和风格统一，不只是能打开。

怎么说：

```text
把这篇笔记做成一个可以直接打开的单页 HTML：顶部一句话总结，中间按章节展开，配色简洁，手机上也好读。
```

注意：说清页面用途（展示、报名还是汇报）和风格关键词，效果更稳定。

https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/WorkBuddy-Zero-Cost-Skill-Top-10/Frontend-Design
