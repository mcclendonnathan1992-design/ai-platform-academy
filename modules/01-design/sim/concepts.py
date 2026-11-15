"""Executable concept specs for the gateway (Module 01).

Each class is one *concept*: a small unit with one purpose, its own state, and
a few actions. A concept never calls another concept. The `Gateway` at the
bottom composes them in one place, which is where the design decisions live.

Running the simulation (simulate.py) and its tests lets you check the design
BEFORE writing the real service, including what the system must refuse to do.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Refusal:
    reason: str


class RateLimit:
    """purpose: share scarce model time fairly.
    state:   used[client] = requests this window
    actions: allow(client) -> bool, new_window()
    """

    def __init__(self, per_window: int) -> None:
        self.per_window = per_window
        self.used: dict[str, int] = {}

    def allow(self, client: str) -> bool:
        count = self.used.get(client, 0)
        if count >= self.per_window:
            return False
        self.used[client] = count + 1
        return True

    def new_window(self) -> None:
        self.used.clear()


class PromptGuard:
    """purpose: keep unsafe or abusive input away from the model.
    state:   max_chars, banned phrases
    actions: check(prompt) -> reason | None
    """

    def __init__(self, max_chars: int, banned: tuple[str, ...]) -> None:
        self.max_chars = max_chars
        self.banned = tuple(b.lower() for b in banned)

    def check(self, prompt: str) -> str | None:
        if not prompt.strip():
            return "empty"
        if len(prompt) > self.max_chars:
            return "too_long"
        lowered = prompt.lower()
        if any(b in lowered for b in self.banned):
            return "banned_phrase"
        return None


class ResponseCache:
    """purpose: do not pay twice for the same answer.
    state:   entries[prompt] = response
    actions: lookup(prompt), store(prompt, response)
    principle: after store(p, r), lookup(p) returns r
    """

    def __init__(self) -> None:
        self.entries: dict[str, str] = {}

    def lookup(self, prompt: str) -> str | None:
        return self.entries.get(prompt)

    def store(self, prompt: str, response: str) -> None:
        self.entries[prompt] = response


class ModelRuntime:
    """purpose: turn a prompt into text.
    state:   calls (every prompt it has ever seen)
    actions: generate(prompt) -> text
    """

    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        return f"answer to: {prompt}"


@dataclass
class Gateway:
    """The composition. Order matters and is a design decision:

    1. RateLimit first, so a flooding client costs us almost nothing.
    2. PromptGuard second, so refused input is never cached or sent on.
    3. ResponseCache third, so cache hits skip the model.
    4. ModelRuntime last.
    """

    limiter: RateLimit
    guard: PromptGuard
    cache: ResponseCache
    model: ModelRuntime
    trace: list[str] = field(default_factory=list)

    def handle(self, client: str, prompt: str) -> str | Refusal:
        if not self.limiter.allow(client):
            self.trace.append(f"{client}: refused (rate_limited)")
            return Refusal("rate_limited")
        reason = self.guard.check(prompt)
        if reason:
            self.trace.append(f"{client}: refused ({reason})")
            return Refusal(reason)
        hit = self.cache.lookup(prompt)
        if hit is not None:
            self.trace.append(f"{client}: cache hit")
            return hit
        response = self.model.generate(prompt)
        self.cache.store(prompt, response)
        self.trace.append(f"{client}: model called")
        return response


def default_gateway() -> Gateway:
    return Gateway(
        limiter=RateLimit(per_window=3),
        guard=PromptGuard(max_chars=200, banned=("ignore previous instructions",)),
        cache=ResponseCache(),
        model=ModelRuntime(),
    )
