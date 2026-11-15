"""Command line for the tutor.  python -m tutor --help"""

from __future__ import annotations

import argparse
import sys

from . import core


def _cmd_modules(_: argparse.Namespace) -> int:
    done = core.load_progress()
    for name in core.list_modules():
        print(f"[{'x' if name in done else ' '}] {name}")
    return 0


def _cmd_ask(args: argparse.Namespace) -> int:
    print(core.ask(args.module, " ".join(args.question)))
    return 0


def _cmd_quiz(args: argparse.Namespace) -> int:
    module = core.resolve_module(args.module)
    questions = core.make_questions(module)
    total = 0.0
    for number, question in enumerate(questions, start=1):
        print(f"\nQ{number}. {question}")
        answer = input("Your answer: ").strip()
        score, feedback = core.grade(module, question, answer)
        total += score
        print(f"  -> {feedback}")
    print(f"\nScore: {total:g} / {len(questions)}")
    if total >= len(questions) * 0.7:
        print(f"Looks solid. When the lab checks pass, run: python -m tutor done {module}")
    else:
        print("Re-read the lesson and retry the lab step you are unsure about.")
    return 0


def _cmd_done(args: argparse.Namespace) -> int:
    name = core.mark_done(args.module, " ".join(args.note))
    print(f"Marked {name} complete.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tutor", description="Local-LLM study partner.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("modules", help="list modules and your progress").set_defaults(func=_cmd_modules)

    p_ask = sub.add_parser("ask", help="ask a question about a module")
    p_ask.add_argument("module", help="e.g. 04 or kubernetes")
    p_ask.add_argument("question", nargs="+")
    p_ask.set_defaults(func=_cmd_ask)

    p_quiz = sub.add_parser("quiz", help="3-question quiz on a module")
    p_quiz.add_argument("module")
    p_quiz.set_defaults(func=_cmd_quiz)

    p_done = sub.add_parser("done", help="mark a module complete")
    p_done.add_argument("module")
    p_done.add_argument("note", nargs="*")
    p_done.set_defaults(func=_cmd_done)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except core.TutorError as exc:
        print(f"tutor: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
