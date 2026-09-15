"""只读验证当前物料、同源 ZIP、链接、静态资源与 Python 语法。"""
import ast
from html.parser import HTMLParser
import json
import re
import sys
from urllib.parse import unquote, urlsplit
import zipfile
from common import ROOT, catalog, safe_path, sha256, sources

class StaticLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {'img', 'script', 'iframe', 'source'} and a.get('src'):
            self.links.append(a['src'])
        if tag in {'a', 'link'} and a.get('href'):
            self.links.append(a['href'])

def local_target(file, url):
    url = url.strip().strip('<>')
    if not url or url.startswith(('#', '//')):
        return None
    parsed = urlsplit(url)
    if parsed.scheme:
        # 同库绝对链接可在本地验证；不访问第三方网络。
        patterns = {
            'raw.githubusercontent.com': '/dxawdc/caige-wechat-articles/main/',
            'github.com': '/dxawdc/caige-wechat-articles/',
        }
        prefix = patterns.get(parsed.netloc, '')
        if not prefix or not parsed.path.startswith(prefix):
            return None
        path = parsed.path[len(prefix):]
        if parsed.netloc == 'github.com':
            for start in ('tree/main/', 'blob/main/', 'raw/refs/heads/main/', 'raw/main/'):
                if path.startswith(start):
                    path = path[len(start):]
                    break
            else:
                return None
        return ROOT / unquote(path)
    if parsed.path.startswith('/'):
        # 演示站从自己的静态服务根目录加载；目前使用相对资源。
        return None
    return file.parent / unquote(parsed.path)

def main():
    errors = []
    checks = 0
    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    items = catalog()
    check(len({i['id'] for i in items}) == len(items), '目录存在重复 id')
    check(len({i['source'] for i in items}) == len(items), '目录存在重复资料路径')
    check(len({i['download'] for i in items}) == len(items), '目录存在重复下载路径')
    actual_articles = {p.name for p in (ROOT/'articles').iterdir() if p.is_dir()}
    listed_articles = {i['source'].split('/')[1] for i in items if i['kind'] == 'article'}
    check(actual_articles == listed_articles, '文章目录与 catalog 不一致')
    expected_archives = {i['download'] for i in items}
    actual_archives = {p.relative_to(ROOT).as_posix() for p in (ROOT/'downloads').glob('*.zip')}
    check(expected_archives == actual_archives, 'ZIP 存在多余旧包或缺包')
    sums = dict(line.rsplit('  ', 1)[::-1] for line in (ROOT/'downloads/SHA256SUMS.txt').read_text().splitlines())
    files_to_check = set(p for p in ROOT.glob('*.md')) | {ROOT/'downloads/README.md'}
    manifest_files = set()
    for item in items:
        base = safe_path(ROOT, item['source'])
        manifest = safe_path(base, item['manifest'])
        manifest_files.add(manifest)
        check((base/'README.md').is_file(), f'{item["id"]}: 缺 README')
        current = sources(base)
        files_to_check.update(current)
        if base.name.startswith('v'):
            files_to_check.add(base.parent/'README.md')
            siblings = [p.name for p in base.parent.iterdir() if p.is_dir() and re.fullmatch(r'v\d+\.\d+\.\d+', p.name)]
            check(siblings == [base.name], f'{item["id"]}: 有旧版目录')
        meta = json.loads(manifest.read_text(encoding='utf-8-sig'))
        for field in ['entrypoint', 'basic']:
            if meta.get(field):
                check(safe_path(base, meta[field]).is_file(), f'{item["id"]}: 缺运行入口 {field}')
        actual = {p.relative_to(base).as_posix() for p in current if p != manifest}
        expected = {e['path'] for e in meta['files']}
        check(actual == expected and len(expected) == len(meta['files']), f'{item["id"]}: 清单文件集合不一致')
        for entry in meta['files']:
            p = safe_path(base, entry['path'])
            check(p.is_file(), f'清单文件缺失: {item["id"]}/{entry["path"]}')
            if p.is_file():
                data = p.read_bytes()
                check(sha256(data) == entry['sha256'], f'清单 SHA 不一致: {item["id"]}/{entry["path"]}')
                check(len(data) == entry['bytes'], f'清单字节数不一致: {item["id"]}/{entry["path"]}')
        archive = safe_path(ROOT, item['download'])
        check(archive.is_file(), f'缺 ZIP: {item["download"]}')
        if archive.is_file():
            check(sums.get(archive.name) == sha256(archive.read_bytes()), f'ZIP SHA 不一致: {archive.name}')
            with zipfile.ZipFile(archive) as z:
                names = {archive.stem+'/'+p.relative_to(base).as_posix(): p for p in current}
                check(set(z.namelist()) == set(names) and len(z.namelist()) == len(names), f'ZIP 文件集合不一致: {archive.name}')
                for name, p in names.items():
                    check(name in z.namelist() and z.read(name) == p.read_bytes(), f'ZIP 字节不一致: {name}')
    # 检查公开资料中的过期说明/清单，不使用“版本号较小”判断有效依赖。
    for top in ['articles', 'tools/wechat-code-blocks']:
        for p in (ROOT/top).rglob('*'):
            if not p.is_file(): continue
            check(not re.match(r'README_v\d', p.name), f'重复 README: {p.relative_to(ROOT)}')
            if re.match(r'(?:物料清单|资料清单|manifest)_v[\d.]+\.json$', p.name):
                check(p in manifest_files, f'未登记/过期清单: {p.relative_to(ROOT)}')
    files_to_check.update((ROOT/'tools/repository').glob('*.py'))
    for p in sorted(files_to_check):
        if not p.is_file():
            check(False, f'缺文件: {p.relative_to(ROOT)}')
            continue
        relative = p.relative_to(ROOT).as_posix()
        check(not any(s in relative for s in ('_私有', '/private/', '草稿回执', '素材映射', '封面映射')), f'私有路径: {relative}')
        if p.suffix == '.py':
            try:
                ast.parse(p.read_text(encoding='utf-8-sig'), filename=relative)
                checks += 1
            except SyntaxError as e:
                check(False, f'Python 语法: {relative}:{e.lineno}')
        if p.suffix not in {'.md', '.html'}: continue
        text = p.read_text(encoding='utf-8-sig')
        if p.suffix == '.md':
            text = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', text, flags=re.M|re.S)
            links = re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', text)
            links = [s.split(' "', 1)[0] for s in links]
        else:
            parser = StaticLinks()
            parser.feed(text)
            links = parser.links
        for link in links:
            target = local_target(p, link)
            if target is not None:
                check(target.exists(), f'失效链接: {relative} -> {link}')
    result = {'passed': not errors, 'packages': len(items), 'checks': checks, 'errors': errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1

if __name__ == '__main__':
    sys.exit(main())
