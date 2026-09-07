"""v1.0.0 | 人工提供的参考实现，不是 DeepSeek 实际生成结果。"""
from decimal import Decimal

def total_paid(rows):
    total=sum((Decimal(row['amount']) for row in rows if row['status']=='paid'),Decimal('0.00'))
    return total.quantize(Decimal('0.01'))
