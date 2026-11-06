"""Task 2: the balance must be up to date right after a refund. Do not edit."""

import unittest

from refunds.service import RefundService
from refunds.store import Cache, Table


class BalanceTest(unittest.TestCase):
    def test_balance_after_refund(self):
        service = RefundService(Table(), Cache())
        self.assertEqual(service.balance("m-2"), 0)  # the merchant opens the app: balance is cached
        service.create_refund("req-10", "m-2", 300)
        self.assertEqual(service.balance("m-2"), -300, "the merchant should see the refund right away")
        service.create_refund("req-11", "m-2", 200)
        self.assertEqual(service.balance("m-2"), -500)


if __name__ == "__main__":
    unittest.main()
