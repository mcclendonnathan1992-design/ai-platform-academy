"""Measure gateway latency.  python scripts/benchmark.py [--url URL] [-n 20] [--unique]

Without --unique every request repeats one prompt, so after the first the cache answers.
With --unique each prompt differs, so you measure the model. Compare the two.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.request


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(pct / 100 * (len(ordered) - 1))))
    return ordered[index]


def call(url: str, prompt: str) -> tuple[float, bool]:
    body = json.dumps({"prompt": prompt, "max_tokens": 32}).encode()
    request = urllib.request.Request(f"{url}/v1/chat", data=body, headers={"Content-Type": "application/json"})
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.load(response)
    return (time.perf_counter() - start) * 1000, bool(data.get("cached"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument("-n", type=int, default=20)
    parser.add_argument("--unique", action="store_true")
    args = parser.parse_args()

    times, hits = [], 0
    for i in range(args.n):
        prompt = f"Say hello number {i}" if args.unique else "Say hello"
        ms, cached = call(args.url, prompt)
        times.append(ms)
        hits += cached
    print(f"requests={args.n} cache_hits={hits}")
    print(f"p50={percentile(times, 50):.0f}ms p95={percentile(times, 95):.0f}ms mean={statistics.mean(times):.0f}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
