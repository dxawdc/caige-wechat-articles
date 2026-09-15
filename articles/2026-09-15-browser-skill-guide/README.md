# BrowserSkill 安装与实操配套资料

版本：v1.0.0
更新时间：2026-09-15
状态：可公开分享；演示站、快照导出、截图已核对。

公众号：可以叫我才哥。本文资料由才哥AGI整理。

这里提供本篇自行制作的演示源码与素材，不包含未发表文章全文、私人浏览器资料、Cookie、Token 或草稿标识。BrowserSkill 是独立的第三方开源项目：[Tencent/BrowserSkill](https://github.com/Tencent/BrowserSkill)，官方许可证为 MIT；本目录没有打包其程序或官方文档副本。

## 1. 浏览器环境

测试环境为 Windows x64、Chrome、bsk CLI 0.2.1、扩展0.2.1。此次为已有环境升级使用；macOS/Linux安装方式仅依官方说明整理。

按[官方安装指南](https://github.com/Tencent/BrowserSkill/blob/cli-v0.2.1/README.md)安装 CLI、浏览器扩展和 Skill，再新开 Agent 对话。扩展需要用户手动安装。`bsk --version`、`bsk status`、`bsk doctor` 用于核对环境。

## 2. 启动本地演示

在本目录执行（Python 3.10+；服务器及导出器只用标准库）：

```bash
python -m http.server 8769 --bind 127.0.0.1 --directory 演示站_v1.0.0
```

打开 `http://127.0.0.1:8769/`。资料页12条、Python类别4条，全部为虚构数据。表单 `/#form` 只在页面显示结果，不发送网络请求；移动布局 `/#mobile` 用于宽窄屏检查。终端按 Ctrl+C 关闭服务。

本次数据以2026年9月的演示日期固定生成，不反映真实文章、用户或业务。

## 3. 复现导出结果

已有快照可直接复现，不必再次连接浏览器：

```bash
python 导出可见资料_v1.0.0.py 筛选快照_v1.0.0.txt --output 复现资料.csv
```

预期4行（不含表头），阅读时长36分钟，与 `演示资料_v1.0.0.csv` 一致。解析器只适配此演示表的四列，不能泛化到任意网站。

实时操作时，让 Agent 先建立会话、导航、观察页面，填写 Python 并选择 Python 类别。快照中的 `@eN` 引用和四字母会话ID每次需要重新获取。Windows PowerShell保存快照建议使用 `Out-File -Encoding utf8`；不要将默认UTF-16文本直接交给UTF-8解析器。

本机原生点击返回成功但列表未变化，最终仅在自建资料页使用 `document.querySelector("#filter").click()` 兼容处理后核对结果。它通过 `bsk evaluate ... --json` 执行，必须检查返回值 `.ok`。页面脚本属于常规交互不足时的后备方案，不能视作普通点击通过。

## 4. 实测边界

| 项目 | 结果 |
| --- | --- |
| 搜索框填写、类别选择 | 通过 |
| 普通点击筛选 | 本机未生效 |
| 自建资料页兼容触发 | 4条，36分钟 |
| CSV导出 | 已复核 |
| 表单姓名、邮箱、主题 | 已填写 |
| 表单提交 | 未验证，不以勾选状态证明自动化完成 |
| 手机布局 | 390×844 CSS px，scrollWidth=390 |
| 设备模拟 | 不等同于真机；卡片按钮交互未纳入通过项 |
| 私人后台、文件上传下载、record | 介绍用法，未做业务实测 |

浏览器实拍使用网页截图，不包含工具栏和书签。`00`、`01`、`02`为明确标注的原创示意图/输出摘要，不是软件截图。控制台曾出现扩展资源错误，没有声称零错误。

## 5. 配图与排版源码

`生成讲解配图_v1.0.0.py` 生成封面和3张讲解图，默认使用Windows微软雅黑；其他系统需替换脚本内字体路径。不会修改真实软件截图。

```bash
python -m pip install -r requirements_v1.0.0.txt
python 生成讲解配图_v1.0.0.py
```

`微信排版_v1.0.0.py` 支持 Markdown 转内联HTML、Pygments分词高亮、11px逐行代码与6px图注间距。使用者需要提供自己的Markdown原稿；本目录不提供未发表文章全文。

```bash
python 微信排版_v1.0.0.py --input 自己的文章.md --output 阅读输出
```

单独图片段落的 alt 会作为图下注释，图片路径应位于Markdown所在目录之内。复用前修改脚本中的 TITLE、URL 和 VERSION。手机尺寸浏览器验收不代表真实微信客户端验收。

## 6. 版本与入口

本篇固定参考 [cli-v0.2.1](https://github.com/Tencent/BrowserSkill/releases/tag/cli-v0.2.1) 与对应 [Skill](https://github.com/Tencent/BrowserSkill/blob/cli-v0.2.1/skill/SKILL.md)。具体参数以安装版本的 `bsk <command> --help` 为准。该版本截图帮助未提供 `--full-page`，命令清单没有 `bsk replay`。

v1.0.0：首次整理，7张正文配图、1张封面、13个文章代码块对应的使用说明、演示站与CSV导出器。
