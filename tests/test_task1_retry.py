"""Task 1: a retry with the same request_id must not refund twice. Do not edit."""

import unittest

from refunds.service import RefundService
from refunds.store import Cache, Table


class RetryTest(unittest.TestCase):
    def test_same_request_twice_refunds_once(self):
        service = RefundService(Table(), Cache())
        first = service.create_refund("req-1", "m-1", 500)
        second = service.create_refund("req-1", "m-1", 500)  # Lambda retried after a timeout
        self.assertEqual(first, second, "the retry should return the same refund id")
        self.assertEqual(len(service.refunds_for("m-1")), 1, "only one refund should be saved")
        self.assertEqual(service.balance("m-1"), -500, "the balance should go down once")

    def test_different_requests_both_refund(self):
        service = RefundService(Table(), Cache())
        service.create_refund("req-1", "m-1", 500)
        service.create_refund("req-2", "m-1", 500)
        self.assertEqual(len(service.refunds_for("m-1")), 2)


if __name__ == "__main__":
    unittest.main()
