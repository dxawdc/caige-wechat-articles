# -*- coding: utf-8 -*-
"""公众号排版脚本：把 文章.md 转成符合交付规范的微信正文 HTML。

规范要点（公众号交付规范 v1.5.0）：
- 正文 15px / 行高 1.85；小标题 17px 加粗；表格 12px；行内代码 12px；
- 代码块 11px 逐行、语法高亮、保留缩进、内部横滑；
- 图片与图注同 section，图注 12px #78858F 居中、与图片实际间距 6px；
- 正文顶部直接进入首段；不重复文章大标题。
"""
from __future__ import annotations

import html
import importlib.util
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location(
    "wxcode",
    r"C:\Users\10210\.workbuddy\skills\caige-wechat-writing\scripts\公众号代码块_v1.0.0.py",
)
wxcode = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wxcode)

# ---- 样式常量（紧凑） ------------------------------------------------------
WRAP = ("font-family:-apple-system,BlinkMacSystemFont,'Microsoft YaHei',Arial,sans-serif;"
        "font-size:15px;line-height:1.85;color:#263B49;overflow-wrap:anywhere;")
P = "margin:16px 0;"
BULLET = "margin:8px 0;padding-left:16px;text-indent:-16px;"
BULLET_L2 = "margin:8px 0;padding-left:32px;text-indent:-16px;"
NUMBERED = "margin:8px 0;padding-left:16px;text-indent:-16px;"
H2 = ("font-size:17px;font-weight:700;color:#177F82;border-bottom:1px solid #d7e4e3;"
      "padding:0 0 9px;margin:30px 0 16px;")
H3 = "font-size:17px;font-weight:700;color:#263B49;margin:24px 0 12px;"
CODE_INLINE = "font-size:12px;color:#177F82;background:#f2f6f5;padding:1px 4px;"
TABLE = "width:100%;border-collapse:collapse;margin:18px 0;font-size:12px;word-break:break-word;"
TD = "padding:6px 5px;border-bottom:1px solid #e3e8e8;"
TH = TD + "background:#edf5f4;font-weight:700;"
IMG_SEC = "margin:18px 0 22px;font-size:12px;color:#78858F;text-align:center;"
IMG = "display:block;width:100%;"
CAP = "margin:6px 0 0;"

BULLET_RE = re.compile(r"^(\s*)[-*]\s+(.*)$")
NUMBERED_RE = re.compile(r"^\d+\.\s+")

CODE_FONT = "font-size:11px!important;line-height:18px;"
PRE = ("display:block!important;margin:0;padding:12px;overflow-x:auto!important;"
       "font-family:Menlo,Consolas,monospace;background:#152C3D;color:#E6EDF3;"
       "border-radius:6px;" + CODE_FONT +
       "white-space:pre;-webkit-text-size-adjust:none;text-size-adjust:none;")
LINE = "display:block;" + CODE_FONT


def escape_with_code(text: str) -> str:
    out = []
    for part in re.split(r"(`[^`]+`)", text):
        if part.startswith("`") and part.endswith("`") and len(part) > 2:
            out.append(f'<code style="{CODE_INLINE}">{html.escape(part[1:-1])}</code>')
        else:
            out.append(html.escape(part))
    return "".join(out)


def inline(md: str) -> str:
    """加粗与行内代码一次扫描，允许加粗包住行内代码。"""
    out: list[str] = []
    pos = 0
    for m in re.finditer(r"`([^`]+)`|\*\*(.+?)\*\*", md):
        out.append(escape_with_code(md[pos:m.start()]))
        if m.group(1) is not None:
            out.append(f'<code style="{CODE_INLINE}">{html.escape(m.group(1))}</code>')
        else:
            out.append(f"<strong>{escape_with_code(m.group(2))}</strong>")
        pos = m.end()
    out.append(escape_with_code(md[pos:]))
    return "".join(out)


def render_table(rows: list[list[str]]) -> str:
    head, body = rows[0], rows[2:] if len(rows) > 2 and set(rows[1][0]) <= set("-: ") else rows[1:]
    buf = [f'<table style="{TABLE}"><thead><tr>']
    for c in head:
        buf.append(f'<th style="{TH}">{inline(c)}</th>')
    buf.append("</tr></thead><tbody>")
    for r in body:
        buf.append("<tr>" + "".join(f'<td style="{TD}">{inline(c)}</td>' for c in r) + "</tr>")
    buf.append("</tbody></table>")
    return "".join(buf)


def render_image(alt: str, src: str) -> str:
    cap = html.escape(alt)
    return (f'<section data-image-caption="true" style="{IMG_SEC}">'
            f'<img src="{html.escape(src)}" style="{IMG}">'
            f'<p style="{CAP}">{cap}</p></section>')


def render_code(source: str, language: str) -> str:
    """紧凑代码块：逐行块级 span，行内 token 带显式字号与高亮颜色。"""
    src = source.replace("\r\n", "\n").replace("\r", "\n")
    language = (language or "text").lower().strip()
    language = {"py": "python", "sh": "bash", "shell": "bash", "txt": "text",
                "plaintext": "text", "ps1": "powershell", "js": "javascript",
                "ts": "typescript"}.get(language, language)
    lexer = wxcode.get_lexer_by_name(language, stripnl=False, ensurenl=False, tabsize=0)
    rows: list[list[tuple[str, str]]] = [[]]
    for _, kind, value in lexer.get_tokens_unprocessed(src):
        for i, part in enumerate(value.split("\n")):
            if i:
                rows.append([])
            if part:
                name = wxcode.category(kind)
                if rows[-1] and rows[-1][-1][0] == name:
                    rows[-1][-1] = (name, rows[-1][-1][1] + part)
                else:
                    rows[-1].append((name, part))
    while rows and not rows[-1]:
        rows.pop()
    buf = ['<section class="code-snippet__fix" style="margin:18px 0;padding:0;overflow:hidden;">',
           f'<pre class="code-snippet__js code-snippet_nowrap" data-lang="{language}" style="{PRE}">']
    for row in rows:
        buf.append(f'<span style="{LINE}">')
        if not row:
            buf.append('\xa0')
        for name, value in row:
            style = f"font-size:11px!important;color:{wxcode.COLORS[name]};"
            cls = f' class="code-snippet__{name}"' if name != "plain" else ""
            buf.append(f'<span{cls} style="{style}">{html.escape(value).replace(" ", "\xa0")}</span>')
        buf.append("</span>")
    buf.append("</pre></section>")
    return "".join(buf)


def main() -> None:
    md = (BASE / "文章.md").read_text(encoding="utf-8")
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("## "):
            out.append(f'<h2 style="{H2}">{inline(s[3:].strip())}</h2>')
        elif s.startswith("### "):
            out.append(f'<h3 style="{H3}">{inline(s[4:].strip())}</h3>')
        elif s.startswith("|"):
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append(render_table(rows))
            continue
        elif s.startswith("```"):
            lang = s[3:].strip() or "text"
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            out.append(render_code("\n".join(code) + "\n", lang))
        elif s.startswith("!["):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", s)
            if m:
                out.append(render_image(m.group(1), m.group(2)))
        elif BULLET_RE.match(lines[i]):
            while i < len(lines):
                m = BULLET_RE.match(lines[i])
                if not m:
                    break
                style = BULLET_L2 if len(m.group(1).expandtabs(2)) >= 2 else BULLET
                out.append(f'<p style="{style}">\u2022&nbsp;&nbsp;{inline(m.group(2).strip())}</p>')
                i += 1
            continue
        elif NUMBERED_RE.match(s):
            out.append(f'<p style="{NUMBERED}">{inline(s)}</p>')
        else:
            out.append(f'<p style="{P}">{inline(s)}</p>')
        i += 1

    body = f'<section style="{WRAP}">' + "".join(out) + "</section>"
    (BASE / "公众号正文_v1.0.0.html").write_text(body, encoding="utf8")

    page = ("<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\">"
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>黄金白银这10年｜阅读版</title><style>"
            "*{box-sizing:border-box}body{max-width:720px;margin:auto;padding:16px;"
            "background:#fff}</style><body>" + body + "</body></html>")
    (BASE / "文章阅读版_v1.0.0.html").write_text(page, encoding="utf8")
    print(f"元素 {len(out)} 个；正文 HTML 字符数 {len(body)}（draft/add 上限 20000）")


if __name__ == "__main__":
    main()
