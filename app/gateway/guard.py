"""PromptGuard concept: decide whether a prompt may reach the model.

Spec (see modules/01-design):
  purpose:    keep obviously unsafe or abusive input away from the model
  principle:  a prompt is checked once; if it fails, the model never sees it
  actions:    check(prompt) -> cleaned prompt | refusal

IMPORTANT: a deny-list is a *teaching tool*, not a defense. Module 08 shows
how easily it is bypassed (see tests/test_guard_bypasses.py) and what to layer
on top: least privilege, output filtering, isolation of untrusted content.
"""

from __future__ import annotations

import re


class GuardError(Exception):
    """The prompt was refused. `code` is stable and safe to show to clients."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


_INJECTION_PATTERNS = [
    re.compile(
        r"\b(ignore|disregard)\s+(all\s+)?(the\s+)?(previous|prior|above)\s+"
        r"(instructions|prompts?|rules)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\breveal\s+(your\s+|the\s+)?(system\s+prompt|hidden\s+instructions)",
        re.IGNORECASE,
    ),
    re.compile(r"\byou\s+are\s+now\s+(in\s+)?(developer|dan|jailbreak)", re.IGNORECASE),
]


def check_prompt(prompt: str, max_chars: int) -> str:
    """Return the cleaned prompt, or raise GuardError."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise GuardError("empty_prompt", "Prompt must not be empty.")
    if len(prompt) > max_chars:
        raise GuardError(
            "prompt_too_long", f"Prompt exceeds the {max_chars}-character limit."
        )
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(prompt):
            raise GuardError(
                "injection_suspected", "Prompt looks like an instruction-override attempt."
            )
    return prompt.strip()
