"""Evaluate the gateway against eval/golden.jsonl BEFORE you optimize anything.

    python scripts/eval_gateway.py [--url http://localhost:8080]

Exit code 1 if the pass rate is below --threshold (default 0.6; small models are weak).
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

GOLDEN = Path(__file__).resolve().parent.parent / "eval" / "golden.jsonl"


def load_cases(path: Path = GOLDEN) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def passes(response: str, must_contain: list[str]) -> bool:
    lowered = response.lower()
    return all(term.lower() in lowered for term in must_contain)


def ask(url: str, prompt: str) -> str:
    body = json.dumps({"prompt": prompt, "max_tokens": 64}).encode()
    request = urllib.request.Request(f"{url}/v1/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)["response"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument("--threshold", type=float, default=0.6)
    args = parser.parse_args()
    cases = load_cases()
    ok = 0
    for case in cases:
        good = passes(ask(args.url, case["prompt"]), case["must_contain"])
        ok += good
        print(("PASS " if good else "FAIL ") + case["prompt"])
    rate = ok / len(cases)
    print(f"pass rate: {rate:.0%} ({ok}/{len(cases)})")
    return 0 if rate >= args.threshold else 1


if __name__ == "__main__":
    raise SystemExit(main())
