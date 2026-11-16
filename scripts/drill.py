"""One 20-minute drill a day, written from a blank file.

    python scripts/drill.py              # start today's drill (the timer starts now)
    python scripts/drill.py check        # grade it and log your time
    python scripts/drill.py list         # all drills
    python scripts/drill.py start ID     # pick a specific drill
    python scripts/drill.py stats        # streak, fastest times

Rules: write the file yourself in drills/work/<id>/, no copying from drills/solutions/, no notes.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

from drill_specs import DRILLS
from labkit import Ctx

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "drills" / "work"
STATE = ROOT / ".drill_state.json"
LOG = ROOT / ".drill_log.json"
LIMIT_SECONDS = 20 * 60


def _load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def todays_id(today: dt.date | None = None) -> str:
    ids = sorted(DRILLS)
    return ids[(today or dt.date.today()).toordinal() % len(ids)]


def start(drill_id: str | None = None) -> int:
    drill_id = drill_id or todays_id()
    if drill_id not in DRILLS:
        print(f"No drill {drill_id!r}. Try: python scripts/drill.py list")
        return 2
    drill = DRILLS[drill_id]
    state = _load(STATE, {})
    if state.get("id") == drill_id and time.time() - state.get("start", 0) < 6 * 3600:
        started = state["start"]
        print("(Drill already running: the timer was not reset.)")
    else:
        started = time.time()
        STATE.write_text(json.dumps({"id": drill_id, "start": started}))
    folder = WORK / drill_id
    folder.mkdir(parents=True, exist_ok=True)
    left = max(0, LIMIT_SECONDS - (time.time() - started))
    print(f"DRILL: {drill.title}   ({drill_id})")
    print(f"Write:  drills/work/{drill_id}/{drill.file}")
    print(f"Time:   {int(left // 60)} min {int(left % 60)} s left of 20\n")
    print(drill.prompt)
    print("\nBlank file. No solutions, no copy-paste. When done:  make drill-check")
    return 0


def check() -> int:
    state = _load(STATE, {})
    if not state:
        print("No drill running. Start one with: make drill")
        return 2
    drill = DRILLS[state["id"]]
    elapsed = int(time.time() - state["start"])
    ctx = Ctx(WORK / drill.id)
    results = [c(ctx) for c in drill.checks]
    for r in results:
        print(f"  {'PASS' if r.ok else 'FAIL'}  {r.desc}" + (f"\n        -> {r.detail}" if not r.ok and r.detail else ""))
    ok = all(r.ok is True for r in results)
    in_time = elapsed <= LIMIT_SECONDS
    print(f"\n{sum(r.ok is True for r in results)}/{len(results)} checks   time {elapsed // 60}m{elapsed % 60:02d}s   {'within' if in_time else 'over'} 20 min")
    if ok:
        log = _load(LOG, [])
        log.append({"date": dt.date.today().isoformat(), "id": drill.id, "seconds": elapsed, "in_time": in_time})
        LOG.write_text(json.dumps(log, indent=1))
        STATE.unlink(missing_ok=True)
        print("Logged. " + ("Clean run." if in_time else "Passed, but over time: do this drill again later."))
        print("Now compare with drills/solutions/ and note one thing you would do faster.")
        return 0
    print("Not done yet. Fix the failures and run  make drill-check  again (the clock keeps running).")
    return 1


def streak(log: list[dict], today: dt.date | None = None) -> int:
    days = {dt.date.fromisoformat(e["date"]) for e in log}
    day, n = today or dt.date.today(), 0
    if day not in days:
        day -= dt.timedelta(days=1)  # today not done yet: the streak is still alive
    while day in days:
        n += 1
        day -= dt.timedelta(days=1)
    return n


def stats() -> int:
    log = _load(LOG, [])
    if not log:
        print("No drills logged yet. Start: make drill")
        return 0
    print(f"Drills passed: {len(log)}    current streak: {streak(log)} day(s)\n")
    best: dict[str, int] = {}
    for e in log:
        best[e["id"]] = min(best.get(e["id"], 10**9), e["seconds"])
    for drill_id in sorted(DRILLS):
        if drill_id in best:
            s = best[drill_id]
            print(f"  {drill_id:24} best {s // 60}m{s % 60:02d}s")
        else:
            print(f"  {drill_id:24} not done yet")
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "start"
    if cmd == "start":
        return start(argv[1] if len(argv) > 1 else None)
    if cmd == "check":
        return check()
    if cmd == "stats":
        return stats()
    if cmd == "list":
        for i in sorted(DRILLS):
            print(f"  {i:24} {DRILLS[i].title}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
