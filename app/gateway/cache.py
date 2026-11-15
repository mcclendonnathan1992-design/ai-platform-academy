"""ResponseCache concept: do not pay twice for the same answer.

Spec:
  purpose:    avoid recomputing identical requests
  principle:  after store(k, v), lookup(k) returns v until evicted
  actions:    lookup(key), store(key, value)

Only safe because generation here is treated as repeatable. If you add
sampling temperature or per-user context, the key must include them
(Module 08 discusses cache poisoning and cross-user leaks).
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict


def make_key(model: str, prompt: str, max_tokens: int) -> str:
    raw = f"{model}\x00{max_tokens}\x00{prompt}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class LRUCache:
    def __init__(self, max_entries: int) -> None:
        self.max_entries = max_entries
        self._data: OrderedDict[str, str] = OrderedDict()

    def lookup(self, key: str) -> str | None:
        if self.max_entries <= 0 or key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def store(self, key: str, value: str) -> None:
        if self.max_entries <= 0:
            return
        self._data[key] = value
        self._data.move_to_end(key)
        while len(self._data) > self.max_entries:
            self._data.popitem(last=False)

    def __len__(self) -> int:
        return len(self._data)
