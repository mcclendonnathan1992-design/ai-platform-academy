import datetime as dt
import os
from pathlib import Path

import pytest

os.environ["LABKIT_NO_TOOLS"] = "1"

import drill  # noqa: E402
from drill_specs import DRILLS  # noqa: E402
from labkit import Ctx  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("drill_id", sorted(DRILLS))
def test_reference_solution_passes_every_check(drill_id):
    d = DRILLS[drill_id]
    assert (ROOT / "drills" / "solutions" / drill_id / d.file).exists()
    results = [c(Ctx(ROOT / "drills" / "solutions" / drill_id)) for c in d.checks]
    assert all(r.ok is True for r in results), [(r.desc, r.detail) for r in results if r.ok is not True]


@pytest.mark.parametrize("drill_id", sorted(DRILLS))
def test_blank_file_does_not_pass(drill_id, tmp_path):
    results = [c(Ctx(tmp_path)) for c in DRILLS[drill_id].checks]
    assert not all(r.ok is True for r in results)
    assert sum(r.ok is False for r in results) >= 3 or len(results) < 3


def test_every_drill_fits_twenty_minutes_of_prompt():
    for d in DRILLS.values():
        assert 3 <= len(d.checks) <= 8 and len(d.prompt) < 500


def test_todays_drill_is_stable_and_rotates():
    day = dt.date(2026, 11, 16)
    assert drill.todays_id(day) == drill.todays_id(day)
    seen = {drill.todays_id(day + dt.timedelta(days=i)) for i in range(len(DRILLS))}
    assert seen == set(DRILLS)


def test_streak_counts_consecutive_days_and_survives_an_unfinished_today():
    today = dt.date(2026, 11, 16)
    log = [{"date": (today - dt.timedelta(days=n)).isoformat()} for n in (1, 2, 3, 5)]
    assert drill.streak(log, today) == 3          # today not done yet, yesterday back to 3 days
    assert drill.streak(log + [{"date": today.isoformat()}], today) == 4
    assert drill.streak([], today) == 0


def test_check_logs_a_pass_and_clears_the_timer(tmp_path, monkeypatch):
    monkeypatch.setattr(drill, "WORK", tmp_path / "work")
    monkeypatch.setattr(drill, "STATE", tmp_path / "state.json")
    monkeypatch.setattr(drill, "LOG", tmp_path / "log.json")
    assert drill.start("dockerfile-api") == 0
    assert drill.check() == 1  # blank: fails, timer keeps running
    assert (tmp_path / "state.json").exists()
    src = ROOT / "drills" / "solutions" / "dockerfile-api" / "Dockerfile"
    (tmp_path / "work" / "dockerfile-api" / "Dockerfile").write_text(src.read_text())
    assert drill.check() == 0
    assert not (tmp_path / "state.json").exists()
    assert len(drill._load(tmp_path / "log.json", [])) == 1
