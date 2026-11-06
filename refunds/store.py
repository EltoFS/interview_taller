"""In-memory stand-ins for DynamoDB and Redis, so the exercise runs with no AWS account or server.
Same ideas as the real services, with a smaller API. You don't need to change this file."""

import copy
import time


class ConditionalCheckFailed(Exception):
    """Raised like DynamoDB's ConditionalCheckFailedException."""


class Table:
    """Like a DynamoDB table whose partition key is "pk"."""

    def __init__(self):
        self._items = {}

    def put_item(self, item, only_if_new=False):
        """Save the item under item["pk"], replacing any item with the same key.
        only_if_new=True works like ConditionExpression="attribute_not_exists(pk)":
        if the key already exists, nothing is saved and ConditionalCheckFailed is raised."""
        if only_if_new and item["pk"] in self._items:
            raise ConditionalCheckFailed(item["pk"])
        self._items[item["pk"]] = copy.deepcopy(item)

    def get_item(self, pk):
        """Return a copy of the item with that key, or None."""
        item = self._items.get(pk)
        return copy.deepcopy(item) if item else None

    def query(self, prefix):
        """Return copies of every item whose key starts with prefix."""
        return [copy.deepcopy(v) for k, v in self._items.items() if k.startswith(prefix)]


class Cache:
    """Like Redis GET, SET (with optional EX seconds) and DEL."""

    def __init__(self):
        self._values = {}
        self._expires_at = {}

    def get(self, key):
        expires_at = self._expires_at.get(key)
        if expires_at is not None and time.time() >= expires_at:
            self.delete(key)
        return self._values.get(key)

    def set(self, key, value, ex=None):
        """ex: seconds until the key expires, like redis-py's set(key, value, ex=...)."""
        self._values[key] = value
        if ex is None:
            self._expires_at.pop(key, None)
        else:
            self._expires_at[key] = time.time() + ex

    def delete(self, key):
        self._values.pop(key, None)
        self._expires_at.pop(key, None)
