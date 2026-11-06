# Refund service

A small Python service that refunds money to merchants' customers. `refunds/store.py` holds in-memory stand-ins for DynamoDB and Redis, so nothing else needs to be installed. Support reported three problems; each has a failing test in `tests/`.

## Setup

1. On this page, click **Use this template → Create a new repository** in your GitHub account (public). Clone **your** repository.
2. With Docker Desktop running, from its folder: `docker compose run --rm check`. You will see three ✗. Run it as often as you like.
3. Paste your repository link in the chat.

## Your tasks

The tasks are independent: if one gets stuck, move on. You may use your usual AI assistant; share your whole screen and say how you check what it gives you. Do not edit `tests/` or `check.py`.

1. Retry (4 minutes). In `refunds/service.py`, AWS Lambda sometimes retries `create_refund()` with the same `request_id` after a timeout, and the merchant is refunded twice. Make a retry return the first refund instead of creating a new one.
2. Balance (3 minutes). Right after a refund, `balance()` still shows the old amount. Make it show the new balance.
3. Speed (4 minutes). On a big night, `find_duplicates()` in `refunds/duplicates.py` takes minutes. Make it fast, with the same results.

At the end, run the check again, then commit and push to your repository.
