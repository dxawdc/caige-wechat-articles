"""v1.0.0 | 2026-09-15 | 可复用：代码JSON生成微信内联HTML；不访问网络、不更新草稿。"""
from pathlib import Path
import argparse
import json
import warnings
from lxml import etree
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.token import Token
from pygments.util import ClassNotFound

VERSION = 'v1.0.0'
FONT = 'Menlo,Consolas,monospace'
COLORS = {'plain': '#E6EDF3', 'comment': '#9BADBE', 'keyword': '#D8A5F5',
          'string': '#A4DBA1', 'number': '#F2B880', 'built_in': '#8CCBFF',
          'function': '#8CCBFF', 'operator': '#80DAD3'}
TYPE = f'font-family:{FONT};font-size:11px!important;line-height:18px!important;'
ADJUST = '-webkit-text-size-adjust:none!important;text-size-adjust:none!important;'
SPACE = 'white-space:pre!important;word-break:normal!important;word-wrap:normal!important;overflow-wrap:normal!important;'


def category(kind):
    for family, name in [(Token.Comment, 'comment'), (Token.Keyword, 'keyword'),
                         (Token.Literal.String, 'string'), (Token.Literal.Number, 'number'),
                         (Token.Name.Function, 'function'), (Token.Name.Builtin, 'built_in'),
                         (Token.Name.Class, 'function'), (Token.Operator, 'operator')]:
        if kind in family:
            return name
    return 'plain'


def render_block(source, language):
    """返回section元素；保留源码（换行统一LF），语言必须由调用者明确提供。

    显示空格转NBSP；调用者始终另存原始源码，不从显示HTML生成可运行文件。
    未知语言降级纯文本并发出告警，不猜测语言。
    """
    if not isinstance(source, str) or not isinstance(language, str):
        raise TypeError('source和language必须为字符串')
    source = source.replace('\r\n', '\n').replace('\r', '\n')
    language = language.lower().strip()
    aliases = {'py': 'python', 'sh': 'bash', 'shell': 'bash', 'ps1': 'powershell',
               'js': 'javascript', 'ts': 'typescript', 'txt': 'text', 'plaintext': 'text'}
    language = aliases.get(language, language or 'text')
    try:
        lexer = get_lexer_by_name(language, stripnl=False, ensurenl=False, tabsize=0)
    except ClassNotFound:
        warnings.warn(f'未知语言 {language!r}，按纯文本显示', stacklevel=2)
        language = 'text'
        lexer = TextLexer(stripnl=False, ensurenl=False, tabsize=0)
    rows = [[]]
    for _, kind, value in lexer.get_tokens_unprocessed(source):
        for i, part in enumerate(value.split('\n')):
            if i:
                rows.append([])
            if part:
                name = category(kind)
                if rows[-1] and rows[-1][-1][0] == name:
                    rows[-1][-1] = (name, rows[-1][-1][1] + part)
                else:
                    rows[-1].append((name, part))
    if '\n'.join(''.join(v for _, v in row) for row in rows) != source:
        raise ValueError('分词器改变了源码，停止生成')
    outer = etree.Element('section', {'class': 'code-snippet__fix'})
    outer.set('style', 'display:block;width:100%;max-width:100%;min-width:0;margin:20px 0;'
              'padding:0;overflow:hidden;box-sizing:border-box;' + TYPE + ADJUST)
    pre = etree.SubElement(outer, 'pre', {'class': 'code-snippet__js code-snippet_nowrap', 'data-lang': language})
    pre.set('style', 'display:block!important;width:100%!important;max-width:100%!important;min-width:0;'
            'box-sizing:border-box;float:none;overflow-x:auto!important;overflow-y:hidden;'
            '-webkit-overflow-scrolling:touch;tab-size:4;margin:0;padding:12px;'
            f'background:#152C3D;color:{COLORS["plain"]};border-radius:6px;' + TYPE + SPACE + ADJUST)
    for row in rows:
        line = etree.SubElement(pre, 'code')
        line.set('style', 'display:block!important;min-height:18px;width:max-content!important;'
                 'min-width:100%;max-width:none!important;' + TYPE + SPACE + ADJUST)
        leaf = etree.SubElement(line, 'span', {'leaf': ''})
        leaf.set('style', TYPE + ADJUST)
        # 每行必须有整行leaf字号层；高亮片段在其中。空行保留占位。
        for name, value in row or [('plain', '\xa0')]:
            token = etree.SubElement(leaf, 'span')
            token.set('style', TYPE + SPACE + ADJUST + f'color:{COLORS[name]}!important;')
            if name != 'plain':
                token.set('class', 'code-snippet__' + name)
            token.text = value.replace(' ', '\xa0')
    return outer


def render_html(blocks):
    """输入[{language,source},...]，返回只含代码区的HTML。"""
    return '\n'.join(etree.tostring(render_block(b['source'], b['language']),
                                   encoding='unicode', method='html') for b in blocks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='JSON数组，每项明确language和source')
    parser.add_argument('--output', required=True, type=Path, help='输出目录，文件含版本号')
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding='utf-8-sig'))
    if not isinstance(source, list):
        raise TypeError('JSON必须为代码块数组')
    body = render_html(source)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f'代码片段_{VERSION}.html').write_text(body, encoding='utf8')
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    page += '<title>公众号代码块示例</title><style>*{box-sizing:border-box}body{max-width:720px;margin:auto;padding:16px}</style><body>'
    (args.output / f'代码阅读版_{VERSION}.html').write_text(page + body + '</body></html>', encoding='utf8')
    (args.output / f'原始代码_{VERSION}.json').write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding='utf8')
    print(f'生成{len(source)}个代码块；未调用微信接口。')


if __name__ == '__main__':
    main()
