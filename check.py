"""`docker compose run --rm check`: one line per task, for the interviewer. Do not edit."""

import hashlib
import io
import pathlib
import unittest

ROOT = pathlib.Path(__file__).parent
TASKS = [
    ("T1 Retry refunds once", "tests.test_task1_retry"),
    ("T2 Balance up to date", "tests.test_task2_balance"),
    ("T3 Duplicates fast", "tests.test_task3_speed"),
]


def run(module):
    suite = unittest.defaultTestLoader.loadTestsFromName(module)
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    problems = result.failures + result.errors
    reason = str(problems[0][1]).strip().splitlines()[-1].strip(" :")[:90] if problems else ""
    return result.testsRun - len(problems), result.testsRun, reason


print("\nRefund service — check\n")
for label, module in TASKS:
    passed, total, reason = run(module)
    mark = "✓" if passed == total else "✗"
    print(f"{label:.<28} {passed}/{total} {mark}" + (f"  ({reason})" if reason else ""))

digest = hashlib.sha256()
for path in sorted([ROOT / "check.py", *(ROOT / "tests").glob("*.py")]):
    digest.update(path.name.encode())
    digest.update(path.read_bytes())
print(f"{'tests and check':.<28} {digest.hexdigest()[:8]}\n")
