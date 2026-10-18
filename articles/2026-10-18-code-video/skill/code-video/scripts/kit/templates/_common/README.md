# {{TITLE}}

1920×1080 / 30fps / H.264 + AAC 立体声。画面由 Canvas 2D 代码绘制，配乐和音效由代码合成。

| 文件 | 作用 |
|---|---|
| `STORYBOARD.md` | 分镜表 |
| `src/timeline.js` | 共享时间表：时长、字幕、音效事件 |
| `src/scene.js` | 画面，`drawFrame(ctx, t)` |
| `audio.js` | 配乐与音效 → `out/soundtrack.wav` |
| `index.html` | 浏览器预览（带声音、可拖动，空格键播放） |

共享工具在 `kit/`（相对路径 `{{KIT_NODE}}`）。在 `D:\AI\视频制作` 下运行：

```bash
node kit/bin/film.js all <本项目目录>
```

分步：`node audio.js` → `film.js stills <项目> auto:12` 检查 → `film.js video <项目>` → `film.js share <mp4>` → `film.js verify <mp4>`。
