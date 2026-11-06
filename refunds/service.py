"""Refunds for merchants. create_refund() is called by an AWS Lambda function; when the call times out,
Lambda retries it with the same request_id."""

import time
import uuid

from .store import Cache, ConditionalCheckFailed, Table

LEASE_SECONDS = 30  # a pending request older than this is assumed crashed and may be taken over
MAX_ATTEMPTS = 3
BALANCE_CACHE_TTL_SECONDS = 60  # caps how long a stale balance can survive if a purge races a cache refill


class RefundInProgress(Exception):
    """Another attempt for this request_id is still within its lease; retry later."""


class RefundFailed(Exception):
    """The request ran out of attempts and needs a person to look at it."""


class RefundService:
    def __init__(self, table: Table, cache: Cache):
        self.table = table
        self.cache = cache

    def create_refund(self, request_id: str, merchant_id: str, amount_cents: int) -> str:
        """Refund amount_cents from the merchant's balance and return the refund id.
        Idempotent per request_id: a retry returns the first refund instead of refunding again."""
        now = time.time()
        claim = {
            "pk": f"request#{request_id}",
            "refund_id": str(uuid.uuid4()),
            "merchant_id": merchant_id,
            "amount_cents": amount_cents,
            "status": "pending",
            "attempts": 1,
            "started_at": now,
        }
        try:
            self.table.put_item(claim, only_if_new=True)
        except ConditionalCheckFailed:
            claim = self._resume_claim(request_id, merchant_id, amount_cents, now)
            if claim["status"] == "completed":
                return claim["refund_id"]

        self._process(request_id, claim)
        claim["status"] = "completed"
        self.table.put_item(claim)
        return claim["refund_id"]

    def _resume_claim(self, request_id: str, merchant_id: str, amount_cents: int, now: float) -> dict:
        """Decide what a repeated request_id means: done, still running, stuck (take over) or failed."""
        claim = self.table.get_item(f"request#{request_id}")
        if claim["merchant_id"] != merchant_id or claim["amount_cents"] != amount_cents:
            raise ValueError(f"request_id {request_id} was already used for a different refund")
        if claim["status"] == "failed":
            raise RefundFailed(request_id)
        if claim["status"] == "pending":
            if now - claim["started_at"] < LEASE_SECONDS:
                raise RefundInProgress(request_id)
            if claim["attempts"] >= MAX_ATTEMPTS:
                claim["status"] = "failed"
                self.table.put_item(claim)
                raise RefundFailed(request_id)
            # Resume with the same refund_id: the steps in _process are idempotent, so a partial earlier run
            # is finished, not repeated.
            # shortcut: takeover is not conditional on attempts (in-memory Table has no conditional update);
            # safe because _process is idempotent; on real DynamoDB use ConditionExpression="attempts = :seen".
            claim["attempts"] += 1
            claim["started_at"] = now
            self.table.put_item(claim)
        return claim

    def _process(self, request_id: str, claim: dict) -> None:
        refund_id = claim["refund_id"]
        self.table.put_item({
            "pk": f"refund#{refund_id}",
            "request_id": request_id,
            "merchant_id": claim["merchant_id"],
            "amount_cents": claim["amount_cents"],
        })
        self._add_to_balance(claim["merchant_id"], -claim["amount_cents"], refund_id)

    def balance(self, merchant_id: str) -> int:
        """The merchant's balance in cents. Read very often, so it is cached."""
        key = f"balance:{merchant_id}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        item = self.table.get_item(f"merchant#{merchant_id}")
        value = item["balance_cents"] if item else 0
        self.cache.set(key, value, ex=BALANCE_CACHE_TTL_SECONDS)
        return value

    def refunds_for(self, merchant_id: str) -> list:
        return [r for r in self.table.query("refund#") if r["merchant_id"] == merchant_id]

    def _add_to_balance(self, merchant_id: str, delta_cents: int, refund_id: str) -> None:
        """Apply delta once per refund_id: the id and the new balance are saved in one atomic single-item write."""
        item = self.table.get_item(f"merchant#{merchant_id}") or {"pk": f"merchant#{merchant_id}", "balance_cents": 0}
        # shortcut: applied_refunds grows without bound; upgrade to TransactWriteItems (refund + balance + claim)
        # on real DynamoDB.
        applied = item.setdefault("applied_refunds", [])
        if refund_id not in applied:
            applied.append(refund_id)
            item["balance_cents"] += delta_cents
            self.table.put_item(item)
        # Purge after the write, even if already applied: a resumed run may follow a crash between write and purge.
        self.cache.delete(f"balance:{merchant_id}")
