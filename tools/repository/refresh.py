"""刷新当前清单、确定性独立包与下载索引；不会清理文件或连接网络。"""
from pathlib import Path
import zipfile
from common import ROOT, catalog, safe_path, sha256, sources, write_json
import json

def main():
    items = catalog()
    index = ['# 独立资料下载', '', '每篇仅保留当前 ZIP。解压后的顶层目录与包名一致，README 包含环境与运行说明。', '',
             '| 资料 | 版本 | 下载 | 大小 |', '| --- | --- | --- | --- |']
    sums = []
    for item in items:
        base = safe_path(ROOT, item['source'])
        manifest = safe_path(base, item['manifest'])
        meta = json.loads(manifest.read_text(encoding='utf-8-sig'))
        meta['files'] = [dict(path=p.relative_to(base).as_posix(), bytes=p.stat().st_size,
                              sha256=sha256(p.read_bytes())) for p in sources(base) if p != manifest]
        meta['material_policy'] = 'latest-complete-set-only'
        write_json(manifest, meta)
        archive = safe_path(ROOT, item['download'])
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for p in sources(base):
                info = zipfile.ZipInfo(archive.stem+'/'+p.relative_to(base).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, p.read_bytes(), compresslevel=9)
        digest = sha256(archive.read_bytes())
        sums.append(f'{digest}  {archive.name}')
        index.append(f'| [{item["title"]}](../{item["source"]}/README.md) | {item["version"]} | [{archive.name}]({archive.name}) | {archive.stat().st_size/1024/1024:.2f} MB |')
        print(f'{item["id"]}: {len(meta["files"])+1} files')
    (ROOT/'downloads/README.md').write_text('\n'.join(index)+'\n\n[SHA-256 校验值](SHA256SUMS.txt) · [返回资料库](../README.md)\n', encoding='utf-8', newline='\n')
    (ROOT/'downloads/SHA256SUMS.txt').write_text('\n'.join(sums)+'\n', encoding='utf-8', newline='\n')

if __name__ == '__main__':
    main()
