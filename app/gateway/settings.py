"""Runtime configuration, read from environment variables (12-factor style).

In Docker Compose these come from `environment:`; in Kubernetes they come from
the `ai-config` ConfigMap. The code never cares which.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _read_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _read_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    ollama_url: str = "http://localhost:11434"
    model: str = "llama3.2:1b"
    max_prompt_chars: int = 2000
    cache_size: int = 128  # 0 disables the cache
    rate_limit_per_min: int = 30  # 0 disables rate limiting
    request_timeout_s: float = 120.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            ollama_url=os.environ.get("OLLAMA_URL", cls.ollama_url).rstrip("/"),
            model=os.environ.get("MODEL", cls.model),
            max_prompt_chars=_read_int("MAX_PROMPT_CHARS", cls.max_prompt_chars),
            cache_size=_read_int("CACHE_SIZE", cls.cache_size),
            rate_limit_per_min=_read_int("RATE_LIMIT_PER_MIN", cls.rate_limit_per_min),
            request_timeout_s=_read_float("REQUEST_TIMEOUT_S", cls.request_timeout_s),
        )
