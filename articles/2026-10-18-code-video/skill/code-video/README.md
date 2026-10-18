# code-video：让 AI 用代码做视频

一个可移植的 AI 技能包 + `film` 命令行。装好后，在 Claude Code、Codex、WorkBuddy 等 AI 工具里说一句“用 code-video 做一个关于 X 的视频”，AI 就会按完整流程出片：选技术栈 → 分镜 → 时间表 → 画面代码 → 配乐/旁白/字幕 → 逐帧审片 → 渲染 → 校验 → 交付分享版和封面。

画面、配乐、音效全部由代码生成，不依赖素材库，也不依赖视频生成模型。

## 一键安装

**Windows**：双击 `一键安装.cmd`。需要 Manim（数学动画）和 Blender（真实感 3D）就双击 `一键安装（完整版，含Manim和Blender）.cmd`。

**macOS / Linux**：
```bash
bash install.sh            # 标准
bash install.sh --full     # 含 Manim + Blender
```

安装器会：
1. 检查 Node.js 18+、ffmpeg（缺了用 winget / brew / apt 自动装）和 Chrome/Edge；
2. 把运行时装到 `~/.code-video/`，安装 JS 依赖（Three.js、p5.brush、GSAP、Lottie、Remotion、HyperFrames…），npm 慢会自动换国内镜像；
3. 把 `film` 加入 PATH；
4. 把技能复制到本机已有的 AI 工具：`~/.claude/skills`、`~/.codex/skills`、`~/.workbuddy/skills`（以及 `%APPDATA%\WorkBuddy\skills`、`~/.agents/skills`）；
5. 运行 `film doctor` 报告哪些技术栈可用。

装完**重启 AI 工具**。想先看效果：新开终端运行 `film demo`（约 5~10 分钟，生成一条各技术栈样片合集）。

只给某些工具装，或装到自定义目录：
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -Targets claude,codex
powershell -ExecutionPolicy Bypass -File install.ps1 -Targets "D:\某工具\skills"
```

WorkBuddy 也可以在界面里上传 zip（Skills → 添加 → 上传），但仍需运行一次安装器装好 film 运行时。

## 怎么用

对 AI 说：

> 用 code-video 技能，做一个 60 秒的横屏科普短片，主题是“为什么天空是蓝色的”，要有旁白和字幕。

> 用 code-video 的 three 技术栈做一个 15 秒的竖屏产品展示，结尾出现品牌名“ARC”。

> 用 code-video 把这份 CSV 做成 45 秒的数据故事视频。

> 用 code-video 的 manim 讲清楚冒泡排序，40 秒，男声旁白。

也可以自己用命令行：
```bash
film new 我的片 --type canvas --title "我的片"     # 新建（可加 --size 9:16）
film preview 我的片                               # 浏览器实时预览
film tts 我的片                                   # 合成旁白（先在 src/timeline.js 写 TL.VO）
film lint 我的片                                  # 检查时间表
film stills 我的片 auto:12                         # 抽帧检查
film all 我的片                                   # 配乐 → 母版 → 分享版 → 校验 → 封面
```

## 九种技术栈

| 类型 | 适合 |
|---|---|
| canvas | 科普讲解、示意图、排版、粒子光效（默认） |
| shader | 极光、墨流、液态金属等 GLSL 质感背景和转场 |
| three | 3D 物体、粒子群、辉光、运镜 |
| p5brush | 手绘水彩/铅笔、绘本风、歌词 MV |
| dom | HTML/CSS/SVG + GSAP + Lottie：动态排版、图表、UI 动效 |
| hyperframes | HeyGen HyperFrames 格式 |
| remotion | React 组件化、批量/数据驱动出片 |
| manim | 数学/算法讲解（3Blue1Brown 风格） |
| blender | 真实感材质灯光、景深 |

## 包内文件

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 给 AI 的主说明（工作流 + 规则） |
| `references/` | 详细文档：workflow、cli、story、design、audio、qa、stacks/*、troubleshooting、platforms |
| `scripts/kit/` | film 运行时源码：命令行、动画库、着色器库、音频合成库、九种模板、Python 工具 |
| `install.ps1` / `install.sh` / `一键安装*.cmd` | 安装器 |
| `uninstall.ps1` | 卸载 |
| `AGENTS.md` | 给不支持技能的工具用的精简版说明 |

## 系统要求

Windows 10/11、macOS 或 Linux；Node.js 18+（HyperFrames 需 22+）；ffmpeg；Chrome / Edge / Chromium。可选：Python 3（Manim、edge-tts 旁白）、Blender 4.2+。旁白默认用 edge-tts（需联网），离线时退回系统语音。

## 卸载

Windows：`powershell -ExecutionPolicy Bypass -File uninstall.ps1`；macOS/Linux：见安装结束时的提示。
