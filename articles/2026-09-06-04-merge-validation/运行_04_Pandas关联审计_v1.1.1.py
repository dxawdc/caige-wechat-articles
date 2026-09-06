"""v1.1.1 | 2026-09-06 | pandas合并后金额翻倍，问题出在哪里：专属入口，保留包内原始材料。"""
from pathlib import Path
import json,shutil,subprocess,sys
BASE=Path(__file__).resolve().parent
manifest=json.loads((BASE/'物料清单_v1.1.1.json').read_text(encoding='utf-8'))
assert manifest['articleId']=='04-merge-validation'
OUT=(BASE/'运行结果'/'04-merge-validation').resolve()
if not OUT.is_relative_to(BASE):raise RuntimeError('输出目录不在资料包内')
OUT.mkdir(parents=True,exist_ok=True)
for entry in manifest['files']:
    source=(BASE/entry['path']).resolve();target=(OUT/entry['path']).resolve()
    if not source.is_relative_to(BASE) or not target.is_relative_to(OUT):raise RuntimeError('非法资料路径')
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
for script in ['案例与绘图_v1.0.0.py','进阶案例_v1.1.0.py']:
    subprocess.run([sys.executable,str(OUT/script)],cwd=OUT,check=True)
print('pandas合并后金额翻倍，问题出在哪里：基础与进阶案例运行通过。')
print('结果目录：'+str(OUT))
