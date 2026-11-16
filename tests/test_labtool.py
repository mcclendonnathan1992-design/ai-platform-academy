"""reset / break / reveal must never lose work and must plant bugs the checker can see."""

import json
import os
import shutil
from pathlib import Path

import pytest

os.environ["LABKIT_NO_TOOLS"] = "1"

import lab_check  # noqa: E402
import labtool  # noqa: E402
from lab_specs import LABS  # noqa: E402

REAL = Path(__file__).resolve().parent.parent
BREAKABLE = [k for k in LABS if k != "14"]


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    shutil.copytree(REAL / "labs", tmp_path / "labs")
    monkeypatch.setattr(labtool, "ROOT", tmp_path)
    monkeypatch.setattr(labtool, "ATTEMPTS", tmp_path / ".attempts")
    monkeypatch.setattr(lab_check, "ROOT", tmp_path)
    return tmp_path


@pytest.mark.parametrize("lab", BREAKABLE)
def test_break_plants_visible_bugs_and_fix_by_solution_passes(sandbox, lab):
    assert labtool.cmd_break(lab, 3, 1) == 0
    assert labtool.failures(lab) >= 1, "the checker must notice the planted bugs"
    record = json.loads((sandbox / ".attempts" / f"bugs-{lab}.json").read_text())
    assert record["bugs"] and all({"file", "bug"} <= set(b) for b in record["bugs"])
    # putting the reference solution back must clear every failure
    name = LABS[lab][0]
    work = sandbox / "labs" / name / "work"
    shutil.rmtree(work)
    labtool.fill_work(sandbox / "labs" / name / "given", sandbox / "labs" / name / "solution", work=work)
    assert labtool.failures(lab) == 0


def test_break_is_reproducible_with_a_seed(sandbox):
    labtool.cmd_break("05", 3, 42)
    first = (sandbox / ".attempts" / "bugs-05.json").read_text()
    labtool.cmd_break("05", 3, 42)
    assert (sandbox / ".attempts" / "bugs-05.json").read_text() == first


def test_break_keeps_your_previous_work(sandbox):
    work = sandbox / "labs" / LABS["01"][0] / "work"
    (work / "Dockerfile").write_text("FROM python:3.12-slim\n# MY OWN WORK\n")
    labtool.cmd_break("01", 3, 1)
    saved = list((sandbox / ".attempts").glob("01-*/Dockerfile"))
    assert saved and "MY OWN WORK" in saved[0].read_text()


def test_reset_archives_work_and_restores_blank(sandbox):
    work = sandbox / "labs" / LABS["05"][0] / "work"
    (work / "main.tf").write_text("# mine")
    assert labtool.cmd_reset("5") == 0
    assert [p.name for p in work.iterdir()] == [".gitkeep"]
    assert list((sandbox / ".attempts").glob("05-*/main.tf"))


def test_reset_restores_given_starting_files(sandbox):
    name = LABS["13"][0]
    work = sandbox / "labs" / name / "work"
    labtool.cmd_reset("13")
    assert {p.name for p in work.iterdir()} >= {"Dockerfile", "main.tf", "main.bicep", "app.yaml"}
    assert labtool.failures("13") == 12


def test_unknown_lab_exits(sandbox):
    with pytest.raises(SystemExit):
        labtool.cmd_reset("99")


def test_capstone_has_nothing_to_break(sandbox, capsys):
    assert labtool.cmd_break("14", 3, 1) == 1
    assert "no reference solution" in capsys.readouterr().out
