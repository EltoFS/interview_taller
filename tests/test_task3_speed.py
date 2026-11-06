"""Task 3: find_duplicates must give the same answer, fast, on a big night. Do not edit."""

import random
import signal
import unittest

from refunds.duplicates import find_duplicates

LIMIT_SECONDS = 2


def refunds(n, seed):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        if rows and rng.random() < 0.02:
            row = dict(rng.choice(rows), id=f"r{i}")  # sent twice by mistake
        else:
            row = {"id": f"r{i}", "merchant_id": f"m{rng.randrange(500)}", "amount_cents": rng.randrange(100, 100000),
                   "card_last4": f"{rng.randrange(10000):04d}", "day": f"2026-11-{rng.randrange(1, 29):02d}"}
        rows.append(row)
    return rows


class SpeedTest(unittest.TestCase):
    def test_small_example(self):
        rows = [
            {"id": "a", "merchant_id": "m1", "amount_cents": 500, "card_last4": "1234", "day": "2026-11-02"},
            {"id": "b", "merchant_id": "m1", "amount_cents": 500, "card_last4": "1234", "day": "2026-11-03"},
            {"id": "c", "merchant_id": "m1", "amount_cents": 500, "card_last4": "1234", "day": "2026-11-02"},
            {"id": "d", "merchant_id": "m1", "amount_cents": 500, "card_last4": "1234", "day": "2026-11-02"},
        ]
        self.assertEqual(find_duplicates(rows), ["c", "d"])

    def test_big_night_is_fast(self):
        rows = refunds(30000, seed=7)

        def too_slow(*_):
            raise TimeoutError(f"took more than {LIMIT_SECONDS} seconds")

        signal.signal(signal.SIGALRM, too_slow)
        signal.alarm(LIMIT_SECONDS)
        try:
            got = find_duplicates(rows)
        finally:
            signal.alarm(0)
        seen, expected = set(), []
        for r in rows:
            key = (r["merchant_id"], r["amount_cents"], r["card_last4"], r["day"])
            if key in seen:
                expected.append(r["id"])
            seen.add(key)
        self.assertEqual(got, expected)


if __name__ == "__main__":
    unittest.main()
