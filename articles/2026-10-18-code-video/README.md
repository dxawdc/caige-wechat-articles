# code-video 技能：在 WorkBuddy 里用一句话做出代码视频

本目录是公众号文章《网上很火的 Opus 5.5 代码视频，我在 WorkBuddy 里做出了同款：9种画风，附技能》的配套资料。提供 code-video 技能本体（含 `film` 命令行运行时、九种技术栈文档和一键安装脚本）、九种技术栈各自的 8 秒演示工程、正文演示动图和 GIF 生成脚本。

## 目录结构

| 路径 | 内容 |
| --- | --- |
| `skill/code-video/` | 技能本体：`SKILL.md`（AI 读取的工作流）、`references/`（九种技术栈与设计、声音、审片说明）、`scripts/kit/`（`film` 运行时与模板）、一键安装与卸载脚本 |
| `scenes/<栈名>/` | 九种技术栈各一个 8 秒演示工程：画面源码、时间表 `src/timeline.js`、配乐 `audio.js`、项目配置 `film.json` |
| `images/` | 正文九张演示 GIF、九栈画面总览图、文章封面 |
| `scripts/生成演示GIF.py` | 从渲染成片生成演示 GIF 的 ffmpeg 封装脚本（两段式调色板，`--small` 压缩模式） |
| `物料清单_v1.1.0.json` | 本包物料清单 |

九种技术栈与演示主题：canvas（发光粒子聚成标题）、shader（墨流与液态金属）、three（三维粒子晶体）、p5brush（水彩小镇逐格生长）、dom（网页图表与数字动效）、hyperframes（标题入场动画）、remotion（数据柱状图）、manim（正弦曲线与图形变换）、blender（EEVEE 渲染的 3D 场景）。

## 安装技能

**Windows**：进入 `skill/code-video/`，双击 `一键安装.cmd`；需要数学动画和真实感 3D 时，双击 `一键安装（完整版，含Manim和Blender）.cmd`。

**macOS / Linux**：

```bash
cd skill/code-video
bash install.sh            # 标准
bash install.sh --full     # 含 Manim + Blender
```

安装器会检查并补齐 Node.js 18+ 和 ffmpeg，把 `film` 运行时装到 `~/.code-video`，并把技能复制到本机已有的 WorkBuddy、Claude Code、Codex 技能目录。装完重启 AI 工具即可。

## 在 WorkBuddy 里使用

重启 WorkBuddy 后，直接用中文描述需求：

> 检查一下 code-video 技能，现在能用哪些画风？

> 用 code-video 技能跑一下演示，9 种画风各出一条样片，再拼成一条合集。

> 用 code-video 做一条 30 秒的竖屏短视频，主题是"一杯咖啡从种子到杯子"，手绘水彩风，要旁白和字幕。

技能会让 AI 按"分镜 → 时间表 → 画面代码 → 配乐/旁白/字幕 → 抽帧审片 → 渲染 → 校验 → 交付"的流程出片，交付 MP4、封面、GIF 和字幕文件。

## 运行样例工程

样例工程可以直接交给 WorkBuddy："用 code-video 打开 scenes/canvas 这个工程，把标题改成我的频道名再出片"。也可以在命令行运行：

```bash
film preview scenes/canvas            # 浏览器实时预览（浏览器类栈）
film all scenes/canvas                # 出片：渲染 + 配乐 + 校验 + 封面
film video scenes/manim               # manim / blender 等外部渲染器栈用 video 出片
```

时间表（时长、字幕、音效时刻）集中在每个工程的 `src/timeline.js`，改完同步 `film.json` 的 `duration` 即可重新出片。

生成演示 GIF：

```bash
python scripts/生成演示GIF.py <成片.mp4> out.gif            # 480px / 15fps / 4 秒
python scripts/生成演示GIF.py <成片.mp4> out.gif --small    # 360px / 12fps 压缩模式
```

## 环境要求

Windows 10/11、macOS 或 Linux；Node.js 18+、ffmpeg、Chrome 或 Edge。可选：Python 3（manim 数学动画与 edge-tts 旁白）、Blender 4.2+（真实感 3D）。旁白合成需要联网。

## 素材来源

- 演示工程由 `film new --type <栈>` 生成的模板改造，九条样片均实际渲染（1080p30、8 秒）并抽帧检查；
- 演示 GIF 从对应成片截取 4 秒生成，参数见脚本说明；
- 文章封面背景由 AI 生成，文字为后期排版；
- 技能与样例工程中的代码可自由修改复用。
