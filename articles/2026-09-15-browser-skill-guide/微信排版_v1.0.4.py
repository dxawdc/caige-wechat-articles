"""v1.0.4 | 2026-09-15 | Markdown转微信内联HTML：语法高亮、微信pre标记与强制横滑、紧邻图注。
用法：python 微信排版_v1.0.4.py --input 文章.md --output 输出目录
不调用网络；图片路径按Markdown所在目录解析，输出目录不同时复制相对路径图片。
"""
from pathlib import Path
import argparse,hashlib,json,shutil,re
import markdown
from lxml import html,etree
from pygments.lexers import PythonLexer,BashLexer,PowerShellLexer,TextLexer
from pygments.token import Token

VERSION='v1.0.4'
TITLE='让AI用上我的浏览器：BrowserSkill安装与实操'
URL='https://github.com/dxawdc/caige-wechat-articles/tree/main/articles/2026-09-15-browser-skill-guide'
FONT='Menlo,Consolas,monospace'
COLORS={'plain':'#E6EDF3','comment':'#9BADBE','keyword':'#D8A5F5','string':'#A4DBA1',
    'number':'#F2B880','function':'#8CCBFF','operator':'#80DAD3'}

def token_color(kind):
    if kind in Token.Comment:return COLORS['comment']
    if kind in Token.Keyword:return COLORS['keyword']
    if kind in Token.Literal.String:return COLORS['string']
    if kind in Token.Literal.Number:return COLORS['number']
    if kind in Token.Name.Function or kind in Token.Name.Builtin or kind in Token.Name.Class:return COLORS['function']
    if kind in Token.Operator:return COLORS['operator']
    return COLORS['plain']

def highlighted_lines(source,language):
    cls=PythonLexer if language in ('python','py') else BashLexer if language in ('bash','sh','shell') else PowerShellLexer if language in ('powershell','ps1') else TextLexer
    lexer=cls(stripnl=False,ensurenl=False,tabsize=0)
    rows=[[]]
    for _,kind,value in lexer.get_tokens_unprocessed(source):
        for i,part in enumerate(value.split('\n')):
            if i:rows.append([])
            if not part:continue
            fragments=[(token_color(kind),part)]
            # Bash将外部命令和参数多记为Text；为本文Python命令及选项补充显示颜色。
            if cls is BashLexer and kind in Token.Text:
                pieces=re.split(r'(\bpython\b|(?<!\S)--?[\w-]+)',part)
                fragments=[(COLORS['function'] if piece=='python' else COLORS['keyword'] if index%2 else token_color(kind),piece)
                    for index,piece in enumerate(pieces) if piece]
            for color,fragment in fragments:
                if rows[-1] and rows[-1][-1][0]==color:rows[-1][-1]=(color,rows[-1][-1][1]+fragment)
                else:rows[-1].append((color,fragment))
    assert '\n'.join(''.join(v for _,v in row) for row in rows)==source
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=Path(__file__).parent/(TITLE+'_'+VERSION+'.md'))
    ap.add_argument('--output',type=Path);args=ap.parse_args()
    base=args.input.resolve().parent;out=(args.output or base).resolve();out.mkdir(parents=True,exist_ok=True)
    body=markdown.markdown(args.input.read_text(encoding='utf8'),extensions=['fenced_code','tables'],output_format='html')
    doc=html.fragment_fromstring(body,create_parent='section')
    for comment in doc.xpath('//comment()'):comment.getparent().remove(comment)
    doc.set('style','font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei",Arial,sans-serif;font-size:15px;line-height:1.85;color:#263B49;overflow-wrap:break-word;')
    for p in doc.xpath('.//p'):p.set('style','font-size:15px;line-height:1.85;margin:18px 0;')
    doc.xpath('.//p')[0].set('style','font-size:15px;line-height:1.85;margin:0 0 18px;')
    for h in doc.xpath('.//h1|.//h2|.//h3'):h.set('style','font-size:17px;font-weight:700;color:#177F82;border-bottom:1px solid #d7e4e3;padding:0 0 10px;margin:36px 0 18px;line-height:1.6;')
    for a in doc.xpath('.//a'):a.set('style','font-size:12px;color:#177F82;word-break:break-all;')
    for a in doc.xpath('.//a'):
        wrap=etree.Element('span');wrap.set('style','font-size:12px;word-break:break-all;');a.addprevious(wrap);wrap.append(a)
    for p in doc.xpath('.//p'):
        if p.text_content().startswith('可复制地址：'):p.set('style','font-size:12px;word-break:break-all;margin:18px 0;')
    for quote in doc.xpath('.//blockquote'):quote.set('style','border-left:3px solid #147D82;margin:18px 0;padding:2px 14px;background:#F2F7F6;')
    for table in doc.xpath('.//table'):table.set('style','width:100%;border-collapse:collapse;margin:20px 0;font-size:12px;table-layout:auto;')
    for cell in doc.xpath('.//th|.//td'):cell.set('style','font-size:12px;padding:8px 5px;border-bottom:1px solid #e3e8e8;text-align:left;word-break:break-word;'+('background:#edf5f4;font-weight:700;' if cell.tag=='th' else ''))
    for code in doc.xpath('.//code[not(parent::pre)]'):code.set('style','font-size:12px;white-space:normal;overflow-wrap:anywhere;color:#177F82;background:#f2f6f5;')
    image_map=[]
    for i,im in enumerate(doc.xpath('.//img'),1):
        src=im.get('src');path=(base/src).resolve();assert path.is_file(),src
        assert path.is_relative_to(base),'图片须在文章目录内'
        if out!=base:
            destination=out/src;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination)
        im.set('style','display:block;width:100%;max-width:100%;height:auto;margin:0;padding:0;vertical-align:top;')
        im.set('loading','eager');parent=im.getparent()
        assert parent.tag=='p' and len(parent)==1 and not (parent.text or '').strip(),'独立图片段落才可转换图注组'
        group=etree.Element('section');group.set('data-image-caption','true')
        group.set('style','display:block;margin:22px 0 24px;padding:0;font-size:0;line-height:0;')
        parent.getparent().replace(parent,group);group.append(im)
        cap=etree.SubElement(group,'p');cap.set('style','display:block;font-size:12px;color:#78858F;text-align:center;margin:6px 0 0;padding:0;line-height:18px;')
        cap.text=im.get('alt','')
        image_map.append({'order':i,'alt':im.get('alt'),'file':src,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    native_classes={'#9BADBE':'code-snippet__comment','#D8A5F5':'code-snippet__keyword','#A4DBA1':'code-snippet__string','#F2B880':'code-snippet__number','#8CCBFF':'code-snippet__built_in','#80DAD3':'code-snippet__operator'}
    blocks=[]
    for pre in doc.xpath('.//pre'):
        source=pre.text_content().rstrip('\n');blocks.append(source)
        code=pre.find('code');language=(code.get('class','') if code is not None else '').removeprefix('language-')
        pre.clear();pre.set('class','code-snippet__js code-snippet_nowrap');pre.set('data-lang',{'py':'python','sh':'bash','shell':'bash','ps1':'powershell'}.get(language,language or 'text'))
        pre.set('style',f'display:block!important;font-family:{FONT};font-size:11px!important;line-height:18px;width:100%!important;max-width:100%!important;min-width:0!important;box-sizing:border-box;float:none;overflow-x:auto!important;overflow-y:hidden;white-space:pre!important;word-break:normal!important;word-wrap:normal!important;overflow-wrap:normal!important;-webkit-overflow-scrolling:touch;-webkit-text-size-adjust:100%;tab-size:4;margin:0;padding:12px;background:#152C3D;color:{COLORS["plain"]};border-radius:6px;')
        for row in highlighted_lines(source,language):
            line=etree.SubElement(pre,'code');line.set('style',f'display:block!important;min-height:18px;font-family:{FONT};font-size:11px!important;line-height:18px;width:max-content!important;min-width:100%;max-width:none!important;white-space:pre!important;word-break:normal!important;word-wrap:normal!important;overflow-wrap:normal!important;')
            if not row:
                blank=etree.SubElement(line,'span');blank.set('style',f'font-family:{FONT};font-size:11px!important;line-height:18px;color:{COLORS["plain"]}!important;white-space:pre!important;');blank.text='\xa0'
            for color,value in row:
                span=etree.SubElement(line,'span');span.set('style',f'font-family:{FONT};font-size:11px!important;line-height:18px;color:{color}!important;white-space:pre!important;word-break:normal!important;word-wrap:normal!important;overflow-wrap:normal!important;')
                if color in native_classes:span.set('class',native_classes[color])
                span.text=value.replace(' ','\xa0')
        outer=etree.Element('section');outer.set('class','code-snippet__fix')
        outer.set('style','display:block;width:100%;max-width:100%;min-width:0;margin:20px 0;padding:0;overflow:hidden;box-sizing:border-box;-webkit-text-size-adjust:100%;')
        pre.addprevious(outer);outer.append(pre)
    # 参考50例文章的真实微信DOM：code默认14px，span[leaf]保留11px并供高亮子节点继承。
    for line in doc.xpath('.//pre/code'):
        leaf=etree.Element('span');leaf.set('leaf','')
        leaf.set('style','font-size: 11px !important;')
        leaf.text=line.text;line.text=None
        for token in list(line):leaf.append(token)
        line.append(leaf)
    # 手机高亮/横滑已获确认；仅补齐字号继承并禁止代码区自动文字放大。
    for pre in doc.xpath('.//pre'):
        for node in [pre.getparent(), *pre.iter()]:
            style=node.get('style','')
            style=re.sub(r'(?<![-\w])(?:font-size|line-height|text-size-adjust|-webkit-text-size-adjust):[^;]*;?', '', style)
            node.set('style',style+'font-size:11px!important;line-height:18px!important;-webkit-text-size-adjust:none!important;text-size-adjust:none!important;')
    output=html.tostring(doc,encoding='unicode')
    (out/f'公众号正文_{VERSION}.html').write_text(output,encoding='utf8')
    full='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+TITLE+'</title><style>html{background:#edf1f2}body{max-width:720px;margin:0 auto;padding:28px 22px;background:white;box-sizing:border-box}*{box-sizing:border-box}img{max-width:100%}@media(max-width:500px){body{padding:20px 16px}}</style></head><body>'+output+'</body></html>'
    (out/f'文章阅读版_{VERSION}.html').write_text(full,encoding='utf8')
    for name,obj in [('图文映射',image_map),('文章代码块',blocks),('制作元数据',{'version':VERSION,'title':TITLE,'author':'才哥AGI','public_materials_url':URL,'images':len(image_map),'code_blocks':len(blocks)})]:
        (out/f'{name}_{VERSION}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
    print('rendered:',len(image_map),'images;',len(blocks),'highlighted blocks;',len(output.encode()),'bytes')

if __name__=='__main__':main()
