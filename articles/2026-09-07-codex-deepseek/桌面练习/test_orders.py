"""v1.0.0 | 目标：已支付金额，Decimal 两位小数，空输入返回 0.00。"""
from decimal import Decimal
import unittest
from orders import total_paid

class OrderTests(unittest.TestCase):
    def test_exact_amount(self):
        self.assertEqual(total_paid([{'status':'paid','amount':'0.10'},{'status':'paid','amount':'0.20'}]),Decimal('0.30'))
    def test_exclude_refunded(self):
        self.assertEqual(total_paid([{'status':'paid','amount':'10.20'},{'status':'refunded','amount':'99.00'}]),Decimal('10.20'))
    def test_empty_type(self):
        result=total_paid([])
        self.assertIsInstance(result,Decimal)
        self.assertEqual(str(result),'0.00')

if __name__=='__main__':unittest.main()
