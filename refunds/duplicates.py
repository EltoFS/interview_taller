"""Nightly check for refunds sent twice by mistake."""


def find_duplicates(refunds: list) -> list:
    """Refunds with the same merchant_id, amount_cents, card_last4 and day are duplicates.
    Return the ids of every refund after the first one in each group, in input order."""
    duplicates = []
    for i, refund in enumerate(refunds):
        for earlier in refunds[:i]:
            if (
                refund["merchant_id"] == earlier["merchant_id"]
                and refund["amount_cents"] == earlier["amount_cents"]
                and refund["card_last4"] == earlier["card_last4"]
                and refund["day"] == earlier["day"]
            ):
                duplicates.append(refund["id"])
                break
    return duplicates
