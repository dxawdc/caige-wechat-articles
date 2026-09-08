"""v1.0.0 | 2026-09-08 | 模拟 Excel → Markdown，验证两张表和关键数字。"""
from pathlib import Path
import json,importlib.metadata
from openpyxl import load_workbook
from markitdown import MarkItDown
R=Path(__file__).resolve().parent
source=R/'活动样本_v1.0.0.xlsx';out=R/'本地运行输出';out.mkdir(exist_ok=True)
workbook=load_workbook(source,read_only=True,data_only=True)
rows=list(workbook['活动数据'].values);assert rows==[('渠道','访问用户','付费用户'),('A',1000,80),('B',800,72)]
workbook.close()
result=MarkItDown().convert_local(str(source));text=result.text_content
for token in ['活动数据','统计口径','渠道','访问用户','付费用户','1000','800','80','72']:
    assert token in text, f'转换缺失字段或数字：{token}'
assert '| A | 1000 | 80 |' in text and '| B | 800 | 72 |' in text
(out/'活动文本_v1.0.0.md').write_text(text,encoding='utf-8')
report={'version':'v1.0.0','status':'passed','markitdown':importlib.metadata.version('markitdown'),'worksheets':2,'channels':2,'visitors':1800,'payers':152,'overall_paid_rate':152/1800,'conversion_checks':['两个工作表','渠道与表头','A:1000/80','B:800/72'],'network_or_model_call':False}
(out/'转换校验_v1.0.0.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
