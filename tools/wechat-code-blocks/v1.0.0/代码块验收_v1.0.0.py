"""v1.0.0 | 2026-09-15 | 验证源代码保真、11px、leaf回归、长行和真实触摸事件模拟。"""
from pathlib import Path
import argparse, importlib.util, json, warnings
from lxml import html
from playwright.sync_api import sync_playwright

R = Path(__file__).parent
spec = importlib.util.spec_from_file_location('wechat_codeblocks', R / '公众号代码块_v1.0.0.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--browser', help='可选：现有Chrome可执行文件')
    ap.add_argument('--output', type=Path, default=R / '验收_v1.0.0'); args = ap.parse_args()
    blocks = json.loads((R / '示例代码_v1.0.0.json').read_text(encoding='utf8'))
    edge = '\tif x < 2:\n    print("<&>")\n\n'
    blocks.append({'language': 'python', 'source': edge})
    body = module.render_html(blocks)
    doc = html.fragment_fromstring(body, create_parent='div')
    for pre, source in zip(doc.xpath('.//pre'), blocks):
        lines = ['' if not c.text_content().strip() else c.text_content().replace('\xa0', ' ')
                 for c in pre.xpath('./code')]
        assert '\n'.join(lines) == source['source']
        assert all(len(c.xpath('./span[@leaf]')) == 1 for c in pre.xpath('./code'))
    with warnings.catch_warnings(record=True) as recorded:
        unknown = module.render_block('unaltered <&>', 'unknown-demo-language')
        assert unknown.find('pre').get('data-lang') == 'text' and recorded
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**({'executable_path': args.browser} if args.browser else {}))
        for width in [1280, 390, 360]:
            ctx = browser.new_context(viewport={'width': width, 'height': 844}, is_mobile=width < 500, has_touch=width < 500)
            page = ctx.new_page(); errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
            page.set_content('<meta name="viewport" content="width=device-width,initial-scale=1"><style>*{box-sizing:border-box}body{margin:0;padding:16px}</style>' + body)
            page.add_style_tag(content='pre,pre *{font-size:18px!important;white-space:pre-wrap!important;}pre code{max-width:100%}')
            fonts = page.eval_on_selector_all('pre span', 'ns=>[...new Set(ns.map(n=>getComputedStyle(n).fontSize))]')
            assert fonts == ['11px']
            geometry = page.eval_on_selector_all('pre', '''ps=>ps.map(p=>{p.scrollLeft=70;const moved=p.scrollLeft;p.scrollLeft=0;return {
              scroll:p.scrollWidth,client:p.clientWidth,moved,heights:[...p.querySelectorAll(':scope>code')].map(c=>c.getBoundingClientRect().height)}})''')
            assert all(all(abs(h-18)<.2 for h in p['heights']) for p in geometry)
            assert all(p['moved']>0 for p in geometry if p['scroll']>p['client']+1)
            assert page.evaluate('document.documentElement.scrollWidth') == width
            multi = page.eval_on_selector_all('pre', 'ps=>ps.map(p=>new Set([...p.querySelectorAll("code>span[leaf]>span")].map(n=>getComputedStyle(n).color)).size)')
            assert multi[0]>1 and multi[3]>1  # Python与JS多类别；普通命令不强求多色
            if width == 390:
                target = page.locator('pre').first; box = target.bounding_box()
                cdp = ctx.new_cdp_session(page); x=box['x']+box['width']-25; y=box['y']+25
                cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
                for dx in [30,70,110,160]:
                    cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':x-dx,'y':y}]}); page.wait_for_timeout(30)
                cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); page.wait_for_timeout(100)
                assert target.evaluate('p=>p.scrollLeft')>0
                page.screenshot(path=str(args.output / '手机尺寸示例_v1.0.0.png'))
            # 参考文章中code可回到14px，字体标记只由leaf保留。
            page.evaluate('''() => {document.querySelectorAll('pre code,pre span:not([leaf])').forEach(n=>n.style.removeProperty('font-size'));
              const s=document.createElement('style');s.textContent='pre code{font-size:14px!important}pre span{font-size:inherit!important}';document.head.append(s)}''')
            assert page.eval_on_selector_all('pre span', 'ns=>ns.every(n=>getComputedStyle(n).fontSize==="11px")')
            # 负例：撤掉leaf字号，14px会落到实际文字，防止测试永远通过。
            page.eval_on_selector_all('pre span[leaf]', 'ns=>ns.forEach(n=>n.style.removeProperty("font-size"))')
            assert page.eval_on_selector_all('pre span', 'ns=>ns.every(n=>getComputedStyle(n).fontSize==="14px")')
            assert not errors
            records.append({'width':width,'passed':True,'font_px':11,'leaf_14px_regression':True,'negative_control_detected':True})
            ctx.close()
        browser.close()
    (args.output / '验收结果_v1.0.0.json').write_text(json.dumps({'version':'v1.0.0','cases':records,
        'source_roundtrip':True,'real_wechat_phone_verified':False,'network_or_draft_mutation':False},ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS: 保真/转义/空行/Tab/未知语言降级；3种宽度、11px、触摸横滑、leaf正反例。')


if __name__ == '__main__':
    main()
