"""v1.0.0 | 教学练习：有意保留金额精度和状态过滤问题。"""
def total_paid(rows):
    return sum(float(row['amount']) for row in rows)
