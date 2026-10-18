# code-video 技能介绍：九种技术栈样例工程与演示动图

本目录是公众号文章《视频不是拍出来的，是算出来的：我做了一个 9 种画风的代码做视频技能》的配套资料。文章介绍开源技能 code-video（用代码生成视频的工作流 + film 命令行），本目录提供九种技术栈各自的 8 秒演示工程源码、正文演示动图和 GIF 生成脚本。

## 目录结构

| 路径 | 内容 |
| --- | --- |
| `scenes/<栈名>/` | 九种技术栈各一个 8 秒演示工程：画面源码、时间表 `src/timeline.js`、配乐 `audio.js`、项目配置 `film.json` |
| `images/` | 正文九张演示 GIF、九栈画面总览图、文章封面 |
| `scripts/生成演示GIF.py` | 从渲染成片生成演示 GIF 的 ffmpeg 封装脚本（两段式调色板，`--small` 压缩模式） |
| `物料清单_v1.0.0.json` | 本包物料清单 |

九种技术栈与演示主题：canvas《代码做视频的8种方式》、shader《着色器》（GLSL 极光）、three《三维晶体》（粒子环）、p5brush《手绘小镇》（水彩逐格生长）、dom《网页动效》（HTML 图表）、hyperframes《超帧》（标题动画）、remotion《数据周报》（React 柱状图）、manim《正弦与变形》（数学动画）、blender《程序化三维》（EEVEE 渲染）。

## 怎么跑

前提：已安装 code-video 技能（Node.js 18+、ffmpeg、Chrome/Edge；manim 栈需 Python 3 + manim，blender 栈需 Blender 4.2+）。安装方式见技能仓库的一键安装脚本。

```bash
# 把某个样例工程复制为工作目录后：
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

## 数据与素材来源

- 演示工程由 `film new --type <栈>` 生成的模板改造，九条样片均实际渲染（1080p30、8 秒）并抽帧检查；
- 演示 GIF 从对应成片截取 4 秒生成，参数见脚本说明；
- code-video 技能本体与文档见作者的开源发布渠道，样例工程中的画面代码可自由修改复用。
