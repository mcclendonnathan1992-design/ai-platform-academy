"""Grade a lab.   python scripts/lab_check.py 05            (checks labs/05-*/work)
                  python scripts/lab_check.py 05 solution   (checks the reference answer)
"""

from __future__ import annotations

import sys
from pathlib import Path

from labkit import Ctx, Result, passed
from lab_specs import LABS

ROOT = Path(__file__).resolve().parent.parent


def run_lab(lab: str, which: str = "work") -> list[Result]:
    name, spec = LABS[lab]
    ctx = Ctx(ROOT / "labs" / name / which)
    results = [c(ctx) for c in spec.checks]
    for tool in spec.tools:
        try:
            out = tool(ctx)
        except Exception as exc:  # noqa: BLE001
            out = Result("tool check", False, f"{type(exc).__name__}: {exc}")
        results += out if isinstance(out, list) else [out]
    return results


def main(argv: list[str]) -> int:
    if not argv or argv[0].zfill(2) not in LABS:
        print(f"usage: lab_check.py <{'|'.join(LABS)}> [work|solution]")
        return 2
    lab, which = argv[0].zfill(2), (argv[1] if len(argv) > 1 else "work")
    name, spec = LABS[lab]
    print(f"Lab {lab}: {spec.title}  ({name}/{which})\n")
    results = run_lab(lab, which)
    for r in results:
        mark = {True: "PASS", False: "FAIL", None: "SKIP"}[r.ok]
        print(f"  {mark}  {r.desc}" + (f"\n        -> {r.detail}" if r.detail and r.ok is not True else ""))
    ok = sum(1 for r in results if r.ok is True)
    bad = sum(1 for r in results if r.ok is False)
    print(f"\n{ok} passed, {bad} failed, {len(results) - ok - bad} skipped")
    if not bad:
        print("Done. Now compare with solution/ and write down what you did differently.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
