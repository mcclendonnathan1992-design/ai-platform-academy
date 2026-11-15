"""Tutor logic. Standard library only, so it runs anywhere Python does.

The tutor talks to your local Ollama server. It reads the README of the module
you pick and answers *from that lesson*, which keeps a small local model on
topic. Small models make mistakes: treat the tutor as a study partner, and
treat `make verify-NN` and the tests as the source of truth.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "modules"
PROGRESS_FILE = REPO_ROOT / ".progress.json"
MAX_CONTEXT_CHARS = 6000

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
TUTOR_MODEL = os.environ.get("TUTOR_MODEL", "llama3.2:1b")

TUTOR_SYSTEM = (
    "You are a patient tutor for a hands-on engineering course. Answer using the "
    "lesson text provided. If the lesson does not cover the question, say so, then "
    "give a short, careful answer and label it as outside the lesson. Prefer a hint "
    "and a pointer to the lab step over a full solution. Be concise."
)

ChatFn = Callable[[list[dict[str, str]]], str]


class TutorError(Exception):
    pass


def list_modules() -> list[str]:
    return sorted(p.name for p in MODULES_DIR.iterdir() if p.is_dir() and p.name[:2].isdigit())


def resolve_module(query: str) -> str:
    """'04', '4', 'kubernetes' or '04-kubernetes' all find the module."""
    modules = list_modules()
    query = query.strip().lower()
    if query.isdigit():
        query = query.zfill(2)
    matches = [m for m in modules if m == query or m.startswith(query + "-") or query in m]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise TutorError(f"No module matches {query!r}. Try one of: {', '.join(modules)}")
    raise TutorError(f"{query!r} is ambiguous: {', '.join(matches)}")


def module_text(module: str) -> str:
    readme = MODULES_DIR / resolve_module(module) / "README.md"
    if not readme.exists():
        raise TutorError(f"{readme} does not exist yet.")
    return readme.read_text(encoding="utf-8")[:MAX_CONTEXT_CHARS]


def chat(messages: list[dict[str, str]], url: str = OLLAMA_URL, model: str = TUTOR_MODEL) -> str:
    payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
    request = urllib.request.Request(
        f"{url}/api/chat", data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.load(response)
        return data["message"]["content"].strip()
    except urllib.error.URLError as exc:
        raise TutorError(
            f"Cannot reach Ollama at {url} ({exc.reason}). Start it, then run: ollama pull {model}"
        ) from exc
    except (KeyError, ValueError) as exc:
        raise TutorError(f"Unexpected reply from Ollama: {exc}") from exc


def ask(module: str, question: str, chat_fn: ChatFn = chat) -> str:
    lesson = module_text(module)
    return chat_fn(
        [
            {"role": "system", "content": TUTOR_SYSTEM},
            {"role": "user", "content": f"LESSON:\n{lesson}\n\nQUESTION: {question}"},
        ]
    )


_QUESTION_LINE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s*(.+?\?)\s*$")


def parse_questions(text: str, limit: int = 3) -> list[str]:
    questions = []
    for line in text.splitlines():
        match = _QUESTION_LINE.match(line)
        if match:
            questions.append(match.group(1))
        if len(questions) == limit:
            break
    return questions


def make_questions(module: str, chat_fn: ChatFn = chat, count: int = 3) -> list[str]:
    lesson = module_text(module)
    reply = chat_fn(
        [
            {"role": "system", "content": TUTOR_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"LESSON:\n{lesson}\n\nWrite exactly {count} short quiz questions about "
                    "this lesson. Number them 1., 2., 3., one per line, each ending with a "
                    "question mark. Output only the questions."
                ),
            },
        ]
    )
    questions = parse_questions(reply, count)
    if not questions:
        raise TutorError("The model did not produce usable questions. Try again, or use a larger TUTOR_MODEL.")
    return questions


def grade(module: str, question: str, answer: str, chat_fn: ChatFn = chat) -> tuple[float, str]:
    """Return (score, feedback). Score is 1, 0.5, or 0, from the model's first word."""
    lesson = module_text(module)
    reply = chat_fn(
        [
            {"role": "system", "content": TUTOR_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"LESSON:\n{lesson}\n\nQUESTION: {question}\nLEARNER ANSWER: {answer}\n\n"
                    "Begin your reply with exactly one word: Correct, Partly, or Incorrect. "
                    "Then give one sentence of feedback."
                ),
            },
        ]
    )
    first = reply.strip().lower()
    if first.startswith("correct"):
        return 1.0, reply
    if first.startswith("partly"):
        return 0.5, reply
    return 0.0, reply


def load_progress(path: Path = PROGRESS_FILE) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def mark_done(module: str, note: str = "", path: Path = PROGRESS_FILE) -> str:
    name = resolve_module(module)
    progress = load_progress(path)
    progress[name] = note or "done"
    path.write_text(json.dumps(progress, indent=2, sort_keys=True), encoding="utf-8")
    return name
