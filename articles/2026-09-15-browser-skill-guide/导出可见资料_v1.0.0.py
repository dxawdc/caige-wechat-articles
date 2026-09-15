"""v1.0.0 | 2026-09-15 | 从已保存的BrowserSkill页面快照导出演示资料。
用法：python 导出可见资料_v1.0.0.py 快照.txt --output 演示资料.csv
该解析器只适配本篇演示表格的四列，不是通用网页爬虫。
"""
import argparse,csv,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('snapshot',type=Path);p.add_argument('--output',type=Path,default=Path('演示资料_v1.0.0.csv'));args=p.parse_args()
text=args.snapshot.read_text(encoding='utf-8-sig')
rows=re.findall(r'^\s+row "(Python：[^"\r\n]+) (Python) (\d+) 分钟 (\d{4}-\d{2}-\d{2})"\s*$',text,re.M)
assert rows and len({r[0] for r in rows})==len(rows)
with args.output.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['标题','类别','阅读分钟','日期']);w.writerows(rows)
print(f'已导出{len(rows)}行；阅读时长合计{sum(int(r[2]) for r in rows)}分钟')
