# -*- coding: utf-8 -*-
"""本地验收：模拟微信编辑器改写后的正文里，代码块是否折行、是否内部横滑、字号是否 11px。

微信编辑器保存草稿时会把代码区的 white-space 改成 pre-wrap，并给正文套上
`.rich_media_content * { word-wrap: break-word !important; overflow-wrap: break-word !important }`。
本脚本按同样条件渲染，逐行量高度：一行应等于行高 18px，出现 30px+ 即为折行。

场景 A（编辑器只改 white-space）：white-space:pre → pre-wrap，我们加的三件套保留；
场景 B（更严苛）：再把 word-break / word-wrap / overflow-wrap 声明一并抽掉。
不连接微信、不修改草稿。
"""
from __future__ import annotations

import glob
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
BODY = ROOT / "公众号正文_v1.0.0.html"
OUT = ROOT / "输出"
RESULT = OUT / "代码块不折行验收.json"

WECHAT_CSS = ("*{box-sizing:border-box}"
              ".rich_media_content *{max-width:100%!important;box-sizing:border-box!important;"
              "word-wrap:break-word!important;overflow-wrap:break-word!important}"
              "body{margin:0;background:#fff}")


def find_chromium() -> str | None:
    for pattern in (r"C:\Users\10210\AppData\Local\ms-playwright\chromium-*\chrome-win64\chrome.exe",
                    r"C:\Users\10210\AppData\Local\ms-playwright\chromium-*\chrome-win\chrome.exe",
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    return None


def scenario_a(text: str) -> str:
    """编辑器把代码区 white-space 改成 pre-wrap，其余保留。"""
    return text.replace("white-space:pre!important", "white-space:pre-wrap!important")


def scenario_b(text: str) -> str:
    """更严苛：white-space 被改写，三件套声明也被抽掉。"""
    out = scenario_a(text)
    for prop in ("word-break", "word-wrap", "overflow-wrap"):
        out = re.sub(rf"{prop}:[^;]*;", "", out)
    return out


def measure(page, width: int, body: str) -> dict:
    page.set_viewport_size({"width": width, "height": 900})
    page.set_content(
        f'<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<style>{WECHAT_CSS}</style>"
        f'<body><div class="rich_media_content" style="padding:0 16px">{body}</div></body></html>',
        wait_until="load",
    )
    return page.evaluate("""() => {
      const out = {blocks: [], pageOverflow: 0, fonts: [], colors: []};
      for (const pre of document.querySelectorAll('pre')) {
        // 行元素：新版是 pre > code；被微信改写过的旧版是 pre > span[display:block]
        const lines = [...pre.children].filter(el =>
          el.tagName === 'CODE' || getComputedStyle(el).display === 'block');
        const probe = lines[0] || pre;
        const lineHeight = parseFloat(getComputedStyle(probe).lineHeight) || 18;
        const heights = lines.map(c => Math.round(c.getBoundingClientRect().height));
        out.blocks.push({
          lines: lines.length,
          lineHeight,
          heights,
          wrapped: heights.filter(h => h > lineHeight * 1.6).length,
          scrollWidth: Math.round(pre.scrollWidth),
          clientWidth: Math.round(pre.clientWidth),
          scrollable: pre.scrollWidth > pre.clientWidth + 1,
          whiteSpace: getComputedStyle(probe).whiteSpace,
        });
        for (const node of pre.querySelectorAll('span, code')) {
          if (node.textContent.trim() && !node.querySelector('span, code')) {
            const style = getComputedStyle(node);
            out.fonts.push(style.fontSize);
            out.colors.push(style.color);
          }
        }
      }
      out.pageOverflow = document.documentElement.scrollWidth - window.innerWidth;
      out.fonts = [...new Set(out.fonts)];
      out.colors = [...new Set(out.colors)];
      return out;
    }""")


def main() -> None:
    raw = BODY.read_text(encoding="utf-8")
    bodies = {"A_编辑器只改white-space": scenario_a(raw), "B_三件套也被抽掉": scenario_b(raw)}
    previous = OUT / "草稿正文_修复前对照.html"
    if previous.is_file():
        bodies["C_修复前的草稿（微信已改写）"] = previous.read_text(encoding="utf-8")
    results: dict = {}
    executable = find_chromium()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True)
        page = browser.new_page()
        for name, body in bodies.items():
            results[name] = {str(w): measure(page, w, body) for w in (1280, 390, 360)}
        page.set_viewport_size({"width": 390, "height": 1200})
        page.set_content(
            f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>{WECHAT_CSS}</style>'
            f'<body><div class="rich_media_content" style="padding:0 16px">{bodies["A_编辑器只改white-space"]}</div></body></html>')
        first = page.query_selector("pre")
        if first:
            first.screenshot(path=str(OUT / "代码块首块_390px模拟微信.png"))
        browser.close()

    summary = {}
    for name, widths in results.items():
        summary[name] = {
            "折行行数": {w: sum(b["wrapped"] for b in d["blocks"]) for w, d in widths.items()},
            "可内部横滑": {w: [b["scrollable"] for b in d["blocks"]] for w, d in widths.items()},
            "页面横向溢出": {w: d["pageOverflow"] for w, d in widths.items()},
            "字号": sorted({f for d in widths.values() for f in d["fonts"]}),
            "颜色数": len({c for d in widths.values() for c in d["colors"]}),
        }
    results["结论"] = summary
    RESULT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
